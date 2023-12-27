'''
This module will check the resources directory for any mis-matched media, convert it
and auto-generate subtitles for it using the `faster_whisper` library.
'''

import os, io
import warnings
import ffmpeg
from multiprocessing import Process
from typing import Iterable
from glob import glob

from faster_whisper import WhisperModel
from faster_whisper.transcribe import Segment
from faster_whisper.utils import format_timestamp

from kizano.utils import read_yaml, write_yaml
from kizano import getLogger
log = getLogger(__name__)

class Devices(object):
    '''
    Poor man's enumeration() object for device types.
    '''
    CPU = 'cpu'
    GPU = 'cuda'
    CUDA = 'cuda'
    AUTO = 'auto'

class RefreshCommand(object):
    '''
    Refresh command operations in object form so we have places to store program configuration.
    '''

    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'guillaumekln/faster-whisper-large-v2')
    DEVICES = ['cpu', 'cuda', 'auto']
    LANGS = ["auto","af","am","ar","as","az","ba","be","bg","bn","bo","br","bs","ca",
    "cs","cy","da","de","el","en","es","et","eu","fa","fi","fo","fr","gl","gu","ha",
    "haw","he","hi","hr","ht","hu","hy","id","is","it","ja","jw","ka","kk","km","kn",
    "ko","la","lb","ln","lo","lt","lv","mg","mi","mk","ml","mn","mr","ms","mt","my",
    "ne","nl","nn","no","oc","pa","pl","ps","pt","ro","ru","sa","sd","si","sk","sl",
    "sn","so","sq","sr","su","sv","sw","ta","te","tg","th","tk","tl","tr","tt","uk",
    "ur","uz","vi","yi","yo","zh"]

    def __init__(self, config: dict):
        self.config = config
        self.whisper = WhisperModel(RefreshCommand.WHISPER_MODEL, device=Devices.GPU, compute_type='auto')

    def filename(self, path: str) -> str:
        '''
        Gets the filename without the extension or leading path.
        '''
        return os.path.splitext(os.path.basename(path))[0]

    def get_audio(self, path: str) -> str:
        '''
        Gets the audio stream for the specified file.
        '''
        filepath = self.filename(path)
        output_path = os.path.join('build', f"{filepath}.wav")
        log.info(f"Extracting audio from {filepath} to {output_path}...")
        # Check to see if the file is already in the build directory.
        if os.path.exists(output_path):
            if self.config['ytffmpeg'].get('overwrite', False):
                log.info(f"Overwriting existing audio for {filepath}!")
            else:
                log.info(f"Audio already extracted for {filepath}!")
                return output_path

        ffmpeg.input(path).output(
            output_path,
            acodec="pcm_s16le",
            ac=1,
            ar="16k"
        ).run(quiet=True, overwrite_output=True)

        log.info('Done extracting audio!')
        return output_path

    def get_subtitles(self, video_path: str) -> str:
        '''
        Input an audio path and output a SRT file containing the subtitles.
        '''
        audio_path = self.get_audio(video_path)
        srt_path = os.path.join('build', f"{self.filename(video_path)}.srt")
        log.info(f"Generating subtitles for {srt_path} from {video_path}... This might take a while...")
        if os.path.exists(srt_path):
            if self.config['ytffmpeg'].get('overwrite', False):
                log.info(f"Overwriting existing subtitles for {srt_path}!")
            else:
                log.info(f"Subtitles already generated for {srt_path}!")
                return srt_path
        args = {
            'word_timestamps': True,
            'language': os.getenv('LANGUAGE', 'en'),
        }
        warnings.filterwarnings("ignore")
        transcript, transcriptInfo = self.whisper.transcribe(audio_path, **args)
        warnings.filterwarnings("default")
        log.debug(transcriptInfo)
        log.info(f"Subtitles generated!")

        self.write_srt(transcript, srt_path)
        return srt_path

    def write_srt(self, transcript: Iterable[Segment], srt_path: str) -> None:
        '''
        Write out the SRT file.
        '''
        log.info('Writing out SRT file...')
        i = 1
        srt_tpl = '%d\n%s --> %s\n%s\n\n'
        with io.open(srt_path, "w", encoding="utf-8") as srt:
            for segment in transcript:
                log.debug(segment)
                buffer = []
                log.info(f"{i}[{segment.start} --> {segment.end}]: {segment.text}")
                while segment.words:
                    word = segment.words.pop(0)
                    buffer.append(word)
                    text = ''.join([ x.word for x in buffer ]).strip().replace('-->', '->')
                    charlen = len(text)
                    stime = format_timestamp(buffer[0].start, always_include_hours=True)
                    etime = format_timestamp(buffer[-1].end, always_include_hours=True)
                    if ( len(buffer) > 6 or charlen > 32 ) and not len(segment.words) == 1:
                        srt.write( srt_tpl % ( i, stime, etime, text ) )
                        i += 1
                        buffer = []
                if len(buffer) > 0:
                    srt.write( srt_tpl % ( i, stime, etime, text ) )
                    i += 1
            srt.flush()
        log.info('Done writing SRT file!')

    def mp4tompv(self, resource: str) -> str:
        '''
        Convert an MP4 file to MKV.
        '''
        log.debug(f'Converting {resource} to mkv.')
        mkvfile = resource.replace('.mp4', '.mkv')
        if os.path.exists(mkvfile):
            if self.config['ytffmpeg'].get('overwrite', False):
                log.info(f'Overwriting existing {mkvfile}!')
            else:
                log.info(f'{mkvfile} already exists!')
                return mkvfile
        out_opts = {
            'f': 'matroska',
            'vcodec': 'libx264',
            'acodec': 'ac3',
            'crf': 28,
            'metadata:s:v': 'language=eng',
            'metadata:s:a': 'language=eng'
        }
        ffmpeg.input(resource).output(mkvfile, **out_opts).global_args('-hide_banner').run()
        if self.config['ytffmpeg'].get('delete_mp4', False):
            log.debug(f'Deleting {resource} to save on disk space.')
            os.unlink(resource)
        return mkvfile

def refresh(config: dict) -> int:
    '''
    Update `ytffmpeg.yml` with any new media in `./resources`.
    Check to see if any media in `./resources` needs to be converted to Matroska format.
    Check to see if any media in `./resources` needs subtitles generated.
    If it's in MP4 format, it will need both subtitles and MKV conversion.
    WHen converting from MP4 to MKV format, the previous metadata is removed, then the following
    metadata is attached to both the audio and the video streams separately: language=eng.
    The video codec is converted to libx264 and the audio codec is converted to ac3.
    The CRF is turned up to 28.
    The resulting MP4 file is then deleted if `.ytffmpeg.delete_mp4` is set to `True`.
    '''
    log.info('Refreshing resources directory.')
    cmd = RefreshCommand(config)
    resources = glob('resources/*')
    log.debug(f'Found resources: {resources}')
    for resource in resources:
        if resource.endswith('.mp4'):
            log.info(f'Processing {resource}...')
            new_vid_tpl = config['ytffmpeg']['defaults']
            new_vid_tpl.update({
                'input': [
                    { 'i': resource.replace('.mp4', '.mkv') },
                    { 'loop': 'true', 'framerate': '30', 'i': resource.replace('.mp4', '.mkv') },
                    { 'i': resource.replace('.mp4', '.srt') }
                ],
                'output': 'build/%s.mp4' % cmd.filename(resource),
            })
            new_vid_tpl['metadata']['title'] = new_vid_tpl['metadata']['description'] = ''
            cmd.mp4tompv(resource)
            cmd.get_subtitles(os.path.realpath(resource))
            # Start the mpv conversion in a subprocess.
            # conversion = Process(target=cmd.mp4tompv, args=(os.path.realpath(resource),))
            # conversion.start()
            # if config['ytffmpeg'].get('subtitles', True):
            #     # Start the subtitle generation in a subprocess.
            #     subtitles = Process(target=cmd.get_subtitles, args=(os.path.realpath(resource),))
            #     subtitles.start()
            #     subtitles.join()
            # conversion.join()
            log.info('Resources have been processed!')
            log.info('Updating ytffmpeg.yml configuration...')
            # Load ytffmpeg.yml config and append the new video. Re-write the updates to disk.
            ytffmpeg_cfg = read_yaml('ytffmpeg.yml')
            ytffmpeg_cfg['videos'].append(new_vid_tpl)
            write_yaml('ytffmpeg.yml', ytffmpeg_cfg)
    log.info('Refresh complete!')

    return 0
