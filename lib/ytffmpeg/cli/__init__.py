'''
Command line interface entrypoint for `ytffmpeg` command.

This module will be responsible for parsing command line arguments and
calling the appropriate sub-modules to perform the actions requested.
'''
from argparse import ArgumentParser, RawTextHelpFormatter
from kizano import getLogger
log = getLogger(__name__)

from .new import new
from .refresh import refresh
from .publish import publish

class YTFFMPEG_Action(object):
    NEW = 'new'
    REFRESH = 'refresh'
    PUBLISH = 'publish'

class YTFFMPEG_Cli(object):
    '''
    Usage: %(prog)s [options] [command]
    '''

    def __init__(self, config: dict):
        self.config = config
        self.getOptions()

    def getOptions(self) -> None:
        '''
        Gets command line arguments.
        '''
        options = ArgumentParser(
            usage=self.__doc__,
            formatter_class=RawTextHelpFormatter
        )

        options.add_argument(
            '--no-auto-subtitles',
            action='store_false',
            dest='subtitles',
            help='Do not automatically generate subtitles.',
            default=True
        )

        options.add_argument(
            '--force',
            action='store_true',
            dest='overwrite',
            help='Valid for the `refresh` action. Runs a cleanup of files before writing new files.',
            default=False
        )

        options.add_argument(
            '--action',
            action='store',
            dest='action',
            help='Choose an action to take.',
            choices=[YTFFMPEG_Action.NEW, YTFFMPEG_Action.REFRESH, YTFFMPEG_Action.PUBLISH],
        )

        opts = options.parse_args()
        self.config['ytffmpeg'].update(vars(opts))

    def execute(self):
        '''
        Interprets command line options and calls the subsequent actions to take.
        These will be built out as sub-modules to this module.
        '''
        action = {
            YTFFMPEG_Action.NEW: new,
            YTFFMPEG_Action.REFRESH: refresh,
            YTFFMPEG_Action.PUBLISH: publish
        }.get(self.config['ytffmpeg']['action'])
        if not action:
            log.error('Invalid action: %s', self.config['action'])
            return 1
        return action(self.config)
