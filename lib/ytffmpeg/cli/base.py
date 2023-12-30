import os, io
import time
import warnings
import ffmpeg
from typing import Iterable
from faster_whisper.transcribe import Segment
from faster_whisper.utils import format_timestamp

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

class YTFFMPEG_Action(object):
    NEW = 'new'
    BUILD = 'build'
    REFRESH = 'refresh'
    PUBLISH = 'publish'

class YTFFMPEG_BaseCommand(object):
    '''
    Base class for all ytffmpeg commands.
    Other commands will derive this class so they will have access to the
    same functionality.
    '''
    def __init__(self, config: dict):
        self.config = config

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
        log.info(f"Extracting audio from \x1b[1m{filepath}\x1b[0m to \x1b[1m{output_path}\x1b[0m...")
        # Check to see if the file is already in the build directory.
        if os.path.exists(output_path):
            if self.config['ytffmpeg'].get('overwrite', False):
                log.info(f"Overwriting existing audio for \x1b[1m{filepath}\x1b[0m!")
            else:
                log.info(f"Audio already extracted for \x1b[1m{filepath}\x1b[0m!")
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
                log.info(f"Overwriting existing subtitles for \x1b[1m{srt_path}\x1b[0m!")
            else:
                log.info(f"Subtitles already generated for \x1b[1m{srt_path}\x1b[0m!")
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
        now = time.time()
        i = 1
        srt_tpl = '%d\n%s --> %s\n%s\n\n'
        with io.open(srt_path, "w", encoding="utf-8") as srt:
            for segment in transcript:
                #log.debug(segment)
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
        then = time.time()
        log.info(f'Done writing SRT file in \x1b[4m{round(then-now, 4)}\x1b[0m seconds!')
