'''
Build opertions for ytffmpeg.
This will read the central configuration and the local configuration, combine the two, and
execute the build operations for each of the videos specified.

If a video is specified, only that video will be built.
'''

from ytffmpeg import getLogger, utils, videos

log = getLogger(__name__)

def buildVideo(cfg: dict) -> int:
    '''
    Main CLI entrypoint for compiling the video.
    '''
    log.info('Building project based on `ytffmpeg.yml` config.')
    ytffmpeg_cfg = utils.load()
    return videos.compileVideo(ytffmpeg_cfg, **cfg)
