'''
Takes the place of the "refresh" function. Normalizes the input video and add to the configuration.
This is a change from "refresh".
'''
import os
from ytffmpeg import getLogger, utils, videos, subtitles, metadata

log = getLogger(__name__)

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
    # There's no video config to consider. So determine language as soon as possible.
    language = utils.language(cfg, {})
    ytffmpeg_cfg = utils.load()
    cfg['name'] = os.path.basename(os.getcwd())
    resources = utils.getResources()
    if resources >1:
        resource = videos.preProcessResources(ytffmpeg_cfg, **cfg)
    else:
        resource = resources[0]
    subtitles.genSubtitles(resource, language, cfg.get('overwrite', False))
    # Check if title is empty in config and generate if needed
    if not cfg.get('title'):
        log.info('Title is empty in config, generating from subtitles...')
        cfg['title'] = metadata.generateTitle(resource)
        log.info(f'Generated title: {cfg["title"]}')

    # Check if description is empty in config and generate if needed
    if not cfg.get('description'):
        log.info('Description is empty in config, generating from subtitles...')
        cfg['description'] = metadata.generateDescription(resource)
        log.info(f'Generated description: {cfg.get("description")}')

    new_vid_tpl = videos.newVideo(resource, cfg['title'], cfg['description'])
    ytffmpeg_cfg['videos'].append(new_vid_tpl)
    log.info('Video(s) normalized and added to `ytffmpeg.yml` config.')
    utils.save(ytffmpeg_cfg['videos'])
    return 0
