'''
Module entrypoint function for compressing MP4 files into MKV files.
'''

from ytffmpeg import getLogger, videos, utils

log = getLogger(__name__)

def compressVideo(cfg: dict) -> int:
    '''
    Takes the inputs and runs the `mp4tomkv()` method with expected args.
    Minimize and compress videos via re-encoding them.
    '''
    ytffmpeg_cfg = utils.load()
    for resource in utils.getResources():
        if not resource.endswith('mp4'): continue
        if utils.hasInput(ytffmpeg_cfg, resource): continue
        log.info(f'Identified {resource} to be compressed...')
        compressed = videos.mp4tomkv(resource)
        log.info(f'Compressed video {compressed}')
    return 0
