'''
Build opertions for ytffmpeg.
This will read the central configuration and the local configuration, combine the two, and
execute the build operations for each of the videos specified.

If a video is specified, only that video will be built.
'''

import ffmpeg
from .base import YTFFMPEG_BaseCommand
from kizano.utils import read_yaml, dictmerge

from kizano import getLogger
log = getLogger(__name__)

class YTFFMPEG_BuildCommand(YTFFMPEG_BaseCommand):
    '''
    Build command for ytffmpeg.
    '''

    def __init__(self, config: dict):
        super().__init__(config)

    def execute(self):
        '''
        Build the videos described by `ytffmpeg.yml`, so load that configuration up first.
        If a resource video was provided to build, only build that one.

        '''
        local_cfg = read_yaml('ytffmpeg.yml')
        cfg = dictmerge(self.config, local_cfg)
        input_video = None
        output = None
        for video_opts in cfg['videos']:
            assert 'input' in video_opts, 'No input specified for video!'
            assert 'output' in video_opts, 'No output specified for video!'
            for video_input in video_opts['input']:
                if input_video == None:
                    input_video = ffmpeg.input(video_input['i'])
                    continue
                input_video = input_video.input(video_input['i'])
            output = input_video.output(video_opts['output'])
            log.info(f'Processing video: {output}')
            if 'metadata' in video_opts:
                for name, value in video_opts['metadata'].items():
                    output = output.output(f'-metadata {name}={value}')
            if 'map' in video_opts:
                for map in video_opts['map']:
                    output = output.output(f'-map {map}')
            if 'filter_complex' in video_opts:
                output = output.output(f'-filter_complex \'{";".join(video_opts["filter_complex"])}\'')
            output = output.overwrite_output()
            output.run()

def build(config: dict) -> int:
    '''
    Entrtypoint for this model.
    '''
    cmd = YTFFMPEG_BuildCommand(config)
    cmd.execute()
    return 0
