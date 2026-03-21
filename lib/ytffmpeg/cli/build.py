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
    results = []
    for video_cfg in ytffmpeg_cfg['videos']:
        cv = videos.compileVideo(video_cfg, **cfg)
        if cv != 0:
            log.info(f'Compile Video had an error for producing {video_cfg["output"]}')
        results.append(cv)
    if all(r == 0 for r in results):
        return 0
    return 1
