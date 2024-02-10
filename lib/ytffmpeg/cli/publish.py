'''
@TODO: Future plans with this module:
- Find API for TikTok and YouTube.
- Make ability to POST to their API's using configurations described in the ytffmpeg.yml file.

What will be interesting is to see how much control over the components and metadata of a video
will be available via the API's.

'''
import os
from fabric import Connection

from kizano import getLogger
log = getLogger(__name__)

from .base import BaseCommand
class PublishCommand(BaseCommand):

    def execute(self) -> int:
        '''
        Run the publish command for the given resource.
        '''
        if 'publish' not in self.config['ytffmpeg']:
            log.warning('No publish configuration found in ytffmpeg.yml!')
            return 1
        publish_cfg = self.config['ytffmpeg']['publish']
        log.info('Publishing compiled resources...')
        if 'resource' in self.config['ytffmpeg']:
            videos = list( filter(lambda x: x['output'] == self.config['ytffmpeg']['resource'], self.config['videos']) ) or []
        else:
            videos = self.config['videos']
        while videos:
            video = videos.pop(0)
            output = video['output']
            if os.path.exists(output):
                if 'attributes' in video and 'not-a-build' in video['attributes']:
                    log.info(f'Skipping \x1b[1m{output}\x1b[0m as it is not a build artifact.')
                    continue
                log.info(f'Publishing \x1b[1m{output}\x1b[0m...')

                if 'youtube' in publish_cfg:
                    log.info('Publishing to YouTube...')

                if 'tiktok' in publish_cfg:
                    log.info('Publishing to TikTok...')

                if 'sftp' in publish_cfg:
                    log.info('Publishing to SFTP Endpoint...')
                    sftp_host = publish_cfg["sftp"]["host"]
                    remote_filename = os.path.join(publish_cfg['sftp']['out_dir'], video.get('publish', os.path.basename(output)))
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
            else:
                log.warning(f'Potentially unbuilt artifact? {output} does not exist!')
        log.info('Complete publishing videos!')
        return 0

def publisher(config: dict) -> int:
    cmd = PublishCommand(config)
    return cmd.execute()
