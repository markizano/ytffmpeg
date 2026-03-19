'''
Main CLI entrypoint for generating metadata based on video content.
Requires `gensubs` having been run.
'''
import os
from ytffmpeg import getLogger, utils, metadata

log = getLogger(__name__)

def generateMetadata(cfg: dict) -> int:
    '''
    Produce a title and description based on content of the video.
    '''
    log.info('Generating title and description metadata.')
    ytffmpeg_cfg = utils.load()
    for transcript in utils.getTranscripts():
        artifact = utils.filename(transcript)
        srt_en = f'build/{artifact}.en.srt'
        if not utils.hasInput(ytffmpeg_cfg['videos'], srt_en): continue
        video_cfg = utils.getInputIndex(ytffmpeg_cfg['videos'], srt_en)
        current_title = video_cfg['metadata'].get('title', '')
        current_description = video_cfg['metadata'].get('description', '')

        if not current_title:
            log.info('Title is empty in config, generating from subtitles...')
            generated_title = metadata.generateTitle(srt_en)
            if generated_title:
                video_cfg['metadata']['title'] = generated_title
                log.info(f'Generated title: {generated_title}')
            else:
                log.warning('Failed to generate title, using empty string.')
                video_cfg['metadata']['title'] = ''

        if not current_description:
            log.info('Description is empty in config, generating from subtitles...')
            generated_description = metadata.generateDescription(srt_en)
            if generated_description:
                video_cfg['metadata']['description'] = generated_description
                log.info(f'Generated description: {generated_description}')
            else:
                log.warning('Failed to generate description, using empty string.')
                video_cfg['metadata']['description'] = ''
    utils.save(ytffmpeg_cfg['videos'])
    log.info('Done generating title and description metadata.')
    return 0
