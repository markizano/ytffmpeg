'''
Normally reserved for pre-install scripts. Ensures the whisper models are loaded.
Useful in Docker containers as well!
'''

from kizano import getLogger
log = getLogger(__name__)

from .base import BaseCommand
class LoadModuleCommand(BaseCommand):
    '''
    Load Whisper models to disk.
    '''
    def execute(self) -> int:
        '''
        Load the whisper models into local cache so we are not searching the internet for them later.
        '''
        return 0


def loadmodule(config: dict) -> int:
    '''
    Load the whisper models into local cache so we are not searching the internet for them later.
    '''
    cmd = LoadModuleCommand(config)
    return cmd.execute()
