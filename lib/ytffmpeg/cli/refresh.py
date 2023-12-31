'''
This module will check the resources directory for any mis-matched media, convert it
and auto-generate subtitles for it using the `faster_whisper` library.
'''

import os
import copy
import ffmpeg
from multiprocessing import Process, Queue
from glob import glob

from kizano.utils import write_yaml
from kizano import getLogger
log = getLogger(__name__)

from .base import YTFFMPEG_BaseCommand
class RefreshCommand(YTFFMPEG_BaseCommand):
    '''
    Refresh command operations in object form so we have places to store program configuration.
    '''

    def mp4tompv(self, resource: str, q: Queue) -> str:
        '''
        Convert an MP4 file to MKV.
        '''
        log.debug(f'Converting {resource} to mkv.')
        mkvfile = resource.replace('.mp4', '.mkv')
        if os.path.exists(mkvfile):
            if self.isOverwrite():
                log.info(f'Overwriting existing {mkvfile}!')
            else:
                log.info(f'{mkvfile} already exists!')
                q.put(mkvfile)
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
        q.put(mkvfile)
        return mkvfile

    def isVidPresent(self, vid: str) -> bool:
        '''
        Check to see if the target video is already considered in the ytffmpeg.yml configuration.
        Iterate over all the `input` videos in `self.config` config and check to see if the `vid` is
        already in the list.
        '''
        for video in self.config['videos']:
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
        self.config['videos'].append(new_vid_tpl)
        log.info('Done appending video to ytffmpeg.yml configuration!')

    def save(self) -> None:
        '''
        Write ytffmpeg.yml updates to disk.
        '''
        log.info('Writing out ytffmpeg.yml configuration...')
        write_yaml('ytffmpeg.yml', self.config)
        log.info('Done writing out ytffmpeg.yml configuration!')

    def execute(self) -> int:
        '''
        Entrypoint for execution
        '''
        resources = glob('resources/*')
        log.debug(f'Found resources: {resources}')
        for resource in resources:
            if resource.endswith('.mp4'):
                log.info(f'Processing {resource}...')
                # Start the mpv conversion in a subprocess.
                q = Queue()
                conversion = Process(target=self.mp4tompv, args=(resource, q))
                conversion.start()
                if self.isSubtitles():
                    self.get_subtitles(resource)
                conversion.join()
                while q.empty() is False:
                    self.append_video(q.get())
                log.info(f'Done processing \x1b[1m{resource}\x1b[0m!')
            elif resource.endswith('.mkv'):
                log.info(f'Processing {resource}...')
                if self.isSubtitles():
                    self.get_subtitles(resource)
                self.append_video(resource)
                log.info('Resources have been processed!')
                
        self.save()
        log.info('Refresh complete!')
        return 0

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
    return cmd.execute()
