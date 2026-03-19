'''
Module entrypoint to generate subtitles.
'''
from ytffmpeg import getLogger, utils, subtitles

def genSubs(cfg: dict) -> int:
    '''
    Entrypoint to generate subtitles from the resources that need them.
    '''
    ytffmpeg_cfg = utils.load()
    for resource in utils.getResources():
        for video_cfg in ytffmpeg_cfg['videos']:
            if not utils.hasInput(video_cfg['input'], resource): continue
            if 'attributes' in video_cfg and 'subs' in video_cfg['attributes']:
                subtitles.genSubtitles(resource, utils.language(cfg, video_cfg), **cfg)
    return 0
