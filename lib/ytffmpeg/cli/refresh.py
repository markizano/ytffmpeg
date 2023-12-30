'''
This module will check the resources directory for any mis-matched media, convert it
and auto-generate subtitles for it using the `faster_whisper` library.
'''

import os
import copy
import ffmpeg
import time
from multiprocessing import Process
from glob import glob

from faster_whisper import WhisperModel

from kizano.utils import read_yaml, write_yaml
from kizano import getLogger
log = getLogger(__name__)

from .base import Devices, YTFFMPEG_BaseCommand

class RefreshCommand(YTFFMPEG_BaseCommand):
    '''
    Refresh command operations in object form so we have places to store program configuration.
    '''

    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'guillaumekln/faster-whisper-large-v2')
    WHISPER_PNG = '/home/YouTube/resources/openai.png'
    DEVICES = ['cpu', 'cuda', 'auto']
    LANGS = ["auto","af","am","ar","as","az","ba","be","bg","bn","bo","br","bs","ca",
    "cs","cy","da","de","el","en","es","et","eu","fa","fi","fo","fr","gl","gu","ha",
    "haw","he","hi","hr","ht","hu","hy","id","is","it","ja","jw","ka","kk","km","kn",
    "ko","la","lb","ln","lo","lt","lv","mg","mi","mk","ml","mn","mr","ms","mt","my",
    "ne","nl","nn","no","oc","pa","pl","ps","pt","ro","ru","sa","sd","si","sk","sl",
    "sn","so","sq","sr","su","sv","sw","ta","te","tg","th","tk","tl","tr","tt","uk",
    "ur","uz","vi","yi","yo","zh"]

    def __init__(self, config: dict):
        super().__init__(config)
        if self.config['ytffmpeg'].get('subtitles', True):
            def load_whisper():
                log.info('Loading whisper model...')
                now = time.time()
                self.whisper = WhisperModel(RefreshCommand.WHISPER_MODEL, device=self.config['ytffmpeg']['device'], compute_type='auto')
                then = time.time()
                log.info(f'Whisper model loaded in {round(then-now,4)} seconds!')
            self.whisper = None
            lw = Process(target=load_whisper)
            lw.start()
        log.info('Loading \x1b[4mytffmpeg.yml\x1b[0m configuration...')
        self.ytffmpeg = read_yaml('ytffmpeg.yml')
        log.info('\x1b[4mytffmpeg.yml\x1b[0m configuration loaded!')


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

    def isVidPresent(self, vid: str) -> bool:
        '''
        Check to see if the target video is already considered in the ytffmpeg.yml configuration.
        Iterate over all the `input` videos in `self.ytffmpeg` config and check to see if the `vid` is
        already in the list.
        '''
        for video in self.ytffmpeg['videos']:
            for invid in video['input']:
                if invid['i'] == vid:
                    return True
        return False

    def append_video(self, resource: str) -> None:
        '''
        Append a video to the ytffmpeg.yml configuration.
        '''
        if self.isVidPresent(resource):
            log.info(f'\x1b[1m{resource}\x1b[0m is already in the ytffmpeg.yml configuration.')
            return
        log.info(f'Appending \x1b[1m{resource}\x1b[0m to ytffmpeg.yml configuration.')
        srt = f'build/{self.filename(resource)}.srt'
        new_vid_tpl = copy.deepcopy(self.config['ytffmpeg']['defaults'])
        new_vid_tpl.update({
            'input': [
                { 'i': resource },
                { 'loop': 'true', 'framerate': '30', 't': '5', 'i': RefreshCommand.WHISPER_PNG },
                { 'i': srt }
            ],
            'output': 'build/%s.mp4' % self.filename(resource),
        })
        new_vid_tpl['metadata']['title'] = new_vid_tpl['metadata']['description'] = ''
        new_vid_tpl['filter_complex'] = [
            f"[0:v]scale=720x1280,pad=864:1536:72:80,scale=720x1280,setsar=1:1,subtitles={srt}:force_style='FontName=Impact,OutlineColour=&H40000000,BorderStyle=3'[_v]",
            "[1:v]format=yuv420p,setpts=PTS-STARTPTS,fade=in:st=0:d=1:alpha=1,fade=out:st=4:d=1:alpha=1[disclaim]",
            "[_v][disclaim]overlay=W-w-100:0:enable='between(t,0,5)',setpts=PTS-STARTPTS[video]",
            "[0:a]volume=1.5,afftdn=nr=10:nf=-20:tn=1,equalizer=f=623:w=3.5:t=h:g=-15:n=1,asetpts=NB_CONSUMED_SAMPLES/SR/TB[audio]"
        ]
        self.ytffmpeg['videos'].append(new_vid_tpl)
        log.info('Done appending video to ytffmpeg.yml configuration!')

    def save(self) -> None:
        '''
        Write ytffmpeg.yml updates to disk.
        '''
        log.info('Writing out ytffmpeg.yml configuration...')
        write_yaml('ytffmpeg.yml', self.ytffmpeg)
        log.info('Done writing out ytffmpeg.yml configuration!')

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
            # Start the mpv conversion in a subprocess.
            conversion = Process(target=cmd.mp4tompv, args=(resource,))
            conversion.start()
            if config['ytffmpeg'].get('subtitles', True):
                cmd.get_subtitles(resource)
            conversion.join()
            cmd.append_video(resource)
            log.info(f'Done processing \x1b[1m{resource}\x1b[0m!')
        elif resource.endswith('.mkv'):
            log.info(f'Processing {resource}...')
            if config['ytffmpeg'].get('subtitles', True):
                cmd.get_subtitles(resource)
            cmd.append_video(resource)
            log.info('Resources have been processed!')
            
    cmd.save()
    log.info('Refresh complete!')
    return 0
