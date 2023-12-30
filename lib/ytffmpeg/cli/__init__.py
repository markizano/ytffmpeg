'''
Command line interface entrypoint for `ytffmpeg` command.

This module will be responsible for parsing command line arguments and
calling the appropriate sub-modules to perform the actions requested.
'''

from argparse import ArgumentParser, RawTextHelpFormatter
from kizano import getLogger
log = getLogger(__name__)

from .base import Devices, YTFFMPEG_Action
from .new import new
from .build import build
from .refresh import refresh
from .publish import publish

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
            '--force', '-f',
            action='store_true',
            dest='overwrite',
            help='Valid for the `refresh` action. Runs a cleanup of files before writing new files.',
            default=False
        )

        options.add_argument(
            '--device', '-d',
            action='store',
            dest='device',
            help='Valid for the `refresh` action. Specify the device to use for processing.',
            choices=[Devices.CPU, Devices.CUDA, Devices.AUTO],
            default=Devices.GPU
        )

        opts, other = options.parse_known_args()
        action = None
        # If any() of the above constant actions is among the unknown arguments, pop it off the list
        # and set the action accordingly.
        # If there is a subsequent resource after the action, assign the resource to the options.
        for arg in other:
            if arg in [YTFFMPEG_Action.NEW, YTFFMPEG_Action.BUILD, YTFFMPEG_Action.REFRESH, YTFFMPEG_Action.PUBLISH]:
                action = arg
                other.remove(arg)
            else:
                opts.resource = arg
        if action:
            opts.action = action
        else:
            log.error('No action specified!')
            options.print_help()
            return 1
        self.config['ytffmpeg'].update(vars(opts))

    def execute(self):
        '''
        Interprets command line options and calls the subsequent actions to take.
        These will be built out as sub-modules to this module.
        '''
        action = {
            YTFFMPEG_Action.NEW: new,
            YTFFMPEG_Action.BUILD: build,
            YTFFMPEG_Action.REFRESH: refresh,
            YTFFMPEG_Action.PUBLISH: publish
        }.get(self.config['ytffmpeg']['action'])
        if not action:
            log.error('Invalid action: %s', self.config['action'])
            return 1
        return action(self.config)
