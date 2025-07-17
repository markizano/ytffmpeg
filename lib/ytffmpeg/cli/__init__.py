'''
Command line interface entrypoint for `ytffmpeg` command.

This module will be responsible for parsing command line arguments and
calling the appropriate sub-modules to perform the actions requested.
'''

import os
from multiprocessing import cpu_count
from argparse import ArgumentParser, RawTextHelpFormatter
from kizano import getLogger
log = getLogger(__name__)

from ..types import Devices, Action
from .base import BaseCommand
from .new import gennew
from .build import builder
from .refresh import refresher
from .subs import gensubs
from .publish import publisher

class Cli(object):
    '''
    Usage: %(prog)s [options] [command]
    '''

    ACTIONS = {
        Action.NEW: gennew,
        Action.BUILD: builder,
        Action.REFRESH: refresher,
        Action.SUBS: gensubs,
        Action.PUBLISH: publisher
    }

    def __init__(self, config: dict):
        self.config = config
        self.getOptions()
        log.debug(f'Final config: {self.config}')

    def getOptions(self) -> None:
        '''
        Gets command line arguments.
        '''
        options = ArgumentParser(
            usage=self.__doc__,
            formatter_class=RawTextHelpFormatter
        )

        options.add_argument(
            '--no-subtitles',
            action='store_false',
            dest='subtitles',
            help='Do not manage subtitle streams.',
            default=None
        )

        options.add_argument(
            '--no-autoplay',
            action='store_false',
            dest='autoplay',
            help="Don't attempt to automatically play the video after building.",
            default=None
        )

        options.add_argument(
            '--force', '-f',
            action='store_true',
            dest='overwrite',
            help='Valid for the `refresh` action. Runs a cleanup of files before writing new files.',
            default=None
        )

        options.add_argument(
            '--device', '-d',
            action='store',
            dest='device',
            help='Valid for the `refresh` action. Specify the device to use for processing.',
            choices=[Devices.CPU, Devices.CUDA, Devices.AUTO],
            default=Devices.GPU
        )

        options.add_argument(
            '--language',
            action='store',
            dest='language',
            help='Which language to use when generating subtitles?',
            choices=BaseCommand.LANGS,
            default=None
        )

        options.add_argument(
            '--log-level', '-l',
            action='store',
            dest='log_level',
            help='How verbose should this application be?',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default='INFO',
            type=str.upper
        )

        opts, other = options.parse_known_args()
        if not 'LOG_LEVEL' in os.environ:
            os.environ['LOG_LEVEL'] = opts.log_level
            log.setLevel(opts.log_level)
        action = None
        # If any() of the above constant actions is among the unknown arguments, pop it off the list
        # and set the action accordingly.
        # If there is a subsequent resource after the action, assign the resource to the options.
        while other:
            arg = other.pop(0)
            if arg in list(Cli.ACTIONS.keys()):
                action = arg
            else:
                opts.resource = arg
        if action:
            opts.action = action
        else:
            log.error('No action specified!')
            options.print_help()
            return
        if opts.overwrite == None:
            del opts.overwrite # type: ignore
        if opts.subtitles == None:
            del opts.subtitles # type: ignore
        if opts.autoplay == None:
            del opts.autoplay # type: ignore
        self.config['ytffmpeg'].update(vars(opts))

    def execute(self):
        '''
        Interprets command line options and calls the subsequent actions to take.
        These will be built out as sub-modules to this module.
        '''
        if 'OMP_NUM_THREADS' not in os.environ:
            os.environ['OMP_NUM_THREADS'] = str(cpu_count())
        action = Cli.ACTIONS.get(self.config['ytffmpeg']['action'])
        if not action:
            log.error('Invalid action: %s', self.config['action'])
            return 1
        log.info(f'Executing action: {action} with config: {self.config}')
        return action(self.config)
