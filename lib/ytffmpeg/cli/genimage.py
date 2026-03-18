'''
Main entrypoint module for generating images/thumbnails based on video content.
'''
import os
from ytffmpeg import getLogger, utils, genimg
log = getLogger(__name__)

def genImage(cfg: dict) -> int:
    '''
    Main entrypoint to generate an image.
    '''
    ytffmpeg_cfg = utils.load()
    for video_cfg in ytffmpeg_cfg['videos']:
        content = open(f'build/{ytffmpeg_cfg["name"]}.txt')
        if 'attributes' in video_cfg and 'thumbnail' in video_cfg['attributes']:
            if os.path.exists('thumbnail.png') and cfg.get('overwrite', False):
                log.info('Overwriting thumbnail.png')
                genimg.generate_thumbnail(video_cfg['metadata']['title'], content)
            elif not os.path.exists('thumbnail.png'):
                log.info('Generating new thumbnail from content...')
                genimg.generate_thumbnail(video_cfg['metadata']['title'], content)
    return 0
