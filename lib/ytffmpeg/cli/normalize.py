'''
Takes the place of the "refresh" function. Normalizes the input video and add to the configuration.
This is a change from "refresh".
The command line operation is different from the in-app functions in that they discover the
environment, collect config and CLI args and pass that intelligently into the functions.
The functions themselves may perform config-changing operations or make calls to
`ytffmpeg build` internally to craft intermittent resources.
'''
import os
from ytffmpeg import getLogger, utils, videos, genimg, subtitles, metadata

log = getLogger(__name__)

def compressVideos(cfg: dict) -> int:
    '''
    Takes the inputs and runs the `mp4tomkv()` method with expected args.
    Minimize and compress videos via re-encoding them.
    '''
    log.info('Compressing resources to save on disk space...')
    ytffmpeg_cfg = utils.load()
    for resource in utils.getResources():
        if not resource.endswith('mp4'): continue
        if utils.hasInput(ytffmpeg_cfg, resource): continue
        log.info(f'Identified {resource} to be compressed...')
        compressed = videos.mp4tomkv(resource, **cfg)
        log.info(f'Compressed video {compressed}')
    log.info('Done compressing resources!')
    return 0

def cutSilence(cfg: dict) -> int:
    '''
    Find quiet moments in the video and cut/strip them out as configured.
    '''
    log.info('Cut-Silence from resources to remove dead moments...')
    for resource in utils.getResources():
        videos.removeSilence(resource, **cfg)
    log.info('Removed silence from videos!')
    return 0

def genSubs(cfg: dict) -> int:
    '''
    Entrypoint to generate subtitles from the videos in the `resources/` folder.
    '''
    log.info('Generating subtitles for resources...')
    ytffmpeg_cfg = utils.load()
    for resource in utils.getResources():
        video_cfg = utils.getInputIndex(ytffmpeg_cfg, resource) or videos.newVideo(resource)
        subtitles.genSubtitles(video_cfg, resource, **cfg)
        ytffmpeg_cfg['videos'].append(video_cfg)
    utils.save(ytffmpeg_cfg)
    log.info('Done generating subtitles!')
    return 0

def genMetadata(cfg: dict) -> int:
    '''
    Produce a title and description based on content of the video.
    Requires/Assumes `genSubs()` has already been called.
    '''
    log.info('Generating title and description metadata.')
    ytffmpeg_cfg = utils.load()
    for video_cfg in ytffmpeg_cfg['videos']:
        if 'subs' not in video_cfg['attributes']: continue
        metadata.generateMetadata(video_cfg, 'title', **cfg)
        metadata.generateMetadata(video_cfg, 'description', **cfg)
    utils.save(ytffmpeg_cfg['videos'])
    log.info('Done generating title and description metadata.')
    return 0

def genImage(cfg: dict) -> int:
    '''
    Main entrypoint to generate an image.
    Creates a thumbnail from the video content used in the gen-image prompt.
    Requires/Assumes `genSubs()` and `genMetadata()` have already been called here.
    '''
    log.info('Generating video thumbnail...')
    ytffmpeg_cfg = utils.load()
    for video_cfg in ytffmpeg_cfg['videos']:
        if 'thumbnail' not in video_cfg['attributes']: continue
        if os.path.exists('thumbnail.png') and not cfg.get('overwrite', False):
            log.info('Not overwriting thumbnail.png. SKIP')
            continue
        log.info('Generating thumbnail.png...')
        content = open(f'build/{ytffmpeg_cfg["name"]}.txt')
        genimg.generate_thumbnail(video_cfg['metadata']['title'], content)
    log.info('Done generating thumbnail image(s)!')
    return 0

def normalize(cfg: dict) -> int:
    '''
    Main method entrypoint.

    Operations include:
        * mp4tomkv: Convert and compress video.
        * cut-silence: Strip the video of pauses in audio.
        * gensubs: Generate subtitles for video.
        * metadata: Generate metadata (title and description).
        * amend/configure: Add this video to the `ytffmpeg.yml` config for compilation.
    '''
    log.info('Normalizing videos to produce compressed subtitled videos with metadata attached.')
    # There's no video config to consider. So determine language as soon as possible.
    ytffmpeg_cfg = utils.load()
    cfg['name'] = os.path.basename(os.getcwd())
    resources = utils.getResources()
    if len(resources) >1:
        resource = videos.preProcessResources(ytffmpeg_cfg, **cfg)
    else:
        resource = videos.mp4tomkv(resources[0])
        # cut-silence from video.
    video_cfg = videos.newVideo(resource)
    subtitles.genSubtitles(video_cfg, resource, **cfg)
    metadata.generateMetadata(video_cfg, 'title', **cfg)
    metadata.generateMetadata(video_cfg, 'description', **cfg)
    # Set filter_complex to None to get the default hardsub filter.
    videos.updateVideo(video_cfg, attributes=['thumbnail'], filter_complex=None)
    content = open(f'build/{utils.filename(resource)}.txt').read()
    if not os.path.exists('thumbnail.png') or ( os.path.exists('thumbnail.png') and cfg.get('overwrite', False) ):
        genimg.generate_thumbnail(video_cfg['metadata']['title'], content)

    ytffmpeg_cfg['videos'].append(video_cfg)
    log.info('Video(s) normalized and added to `ytffmpeg.yml` config.')
    utils.save(ytffmpeg_cfg['videos'])
    log.info('Done normalizing videos!')
    return 0
