'''
Generate subtitles for a given resource. Ignore the subtitle configuration for this command.
'''

import os

from kizano import getLogger
log = getLogger(__name__)

from .base import BaseCommand
class GenSubsCommand(BaseCommand):

    def execute(self):
        '''
        Run the gen-subs command for the given resource.
        0: Success
        1: General error
        2: Invalid resource
        4: System error
        8: Invalid user input.
        '''
        self.config['ytffmpeg']['subtitles'] = True
        self.language = self.config['ytffmpeg'].get('language', os.environ.get('LANGUAGE', 'en'))
        if 'resource' not in self.config['ytffmpeg']:
            log.error('No resource specified!')
            return 8
        resource = self.config['ytffmpeg']['resource']
        if not os.path.exists(resource):
            log.error(f"{resource} does not exist!")
            return 8
        if not os.path.isfile(resource):
            log.error(f"{resource} is not a file!")
            return 8
        if not os.path.exists('build'):
            log.info('Creating `./build` directory.')
            os.mkdir('build')
        log.info(f"Generating subtitles for {resource}")
        self.get_subtitles(resource, self.language)
        return 0

def gensubs(config: dict) -> int:
    '''
    Ignore the subtitle configuration for this command.
    On-demand command for subtitle generation of a given resource.
    '''
    log.info('Refreshing resources directory.')
    cmd = GenSubsCommand(config)
    return cmd.execute()
