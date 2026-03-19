'''
@TODO: Future plans with this module:
- Find API for TikTok and YouTube.
- Make ability to POST to their API's using configurations described in the ytffmpeg.yml file.

What will be interesting is to see how much control over the components and metadata of a video
will be available via the API's.

'''
import os
from fabric import Connection

from ytffmpeg import getLogger, utils
log = getLogger(__name__)

def publishBuilds(cfg: dict) -> int:
    log.info('Publishing compiled resources...')
    publish_cfg = cfg.get('publish', {})
    ytffmpeg_cfg = utils.load()
    for video_cfg in ytffmpeg_cfg['videos']:
        output = video_cfg['output']
        if not output or not os.path.exists(output):
            log.warning(f'Potentially unbuilt artifact? {output} does not exist!')
            continue
        if 'attributes' in video_cfg and 'no-publish' in video_cfg['attributes']:
            log.info(f'Skipping \x1b[1m{output}\x1b[0m as it is not meant for publishing.')
            continue
        log.info(f'Publishing \x1b[1m{output}\x1b[0m...')

        if 'youtube' in publish_cfg:
            log.info('**NOT IMPLEMENTED** Would be Publishing to YouTube...')

        if 'tiktok' in publish_cfg:
            log.info('**NOT IMPLEMENTED** Would be Publishing to TikTok...')

        if 'sftp' in publish_cfg:
            log.info('Publishing to SFTP Endpoint...')
            sftp_host = publish_cfg["sftp"]["host"]
            remote_filename = os.path.join(publish_cfg['sftp']['out_dir'], video_cfg.get('publish', os.path.basename(output)))
            log.info(f'Publishing to {sftp_host} as {remote_filename}')
            c = Connection(sftp_host)
            c.put(output, remote_filename)
            if 'post_publish_cmd' in publish_cfg['sftp']:
                post_publish_cmd = publish_cfg['sftp']['post_publish_cmd']
                log.info(f'Running post-publish command: {post_publish_cmd}')
                # If you plan to run more than one command here, I suggest you create a script and put on the remote first.
                # Keep this a 1-liner with maybe arguments.
                c.run(post_publish_cmd)
        log.info(f'Done publishing \x1b[1m{output}\x1b[0m!')
    log.info('Complete publishing videos!')
    return 0
