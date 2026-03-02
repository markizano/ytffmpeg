'''
Command line interface entrypoint for `ytffmpeg` command.

This module will be responsible for parsing command line arguments and
calling the appropriate sub-modules to perform the actions requested.
'''

import os, sys
from signal import signal, SIGINT
from multiprocessing import cpu_count
from argparse import ArgumentParser, RawTextHelpFormatter
from kizano import getLogger
log = getLogger(__name__)

from ytffmpeg.types import Devices, Action
import ytffmpeg.cli.base as base
import ytffmpeg.cli.new as new
import ytffmpeg.cli.build as build
import ytffmpeg.cli.refresh as refresh
import ytffmpeg.cli.publish as publish
import ytffmpeg.webserv as webserv

def interrupt(signal, frame):
    log.error('Caught ^C interrupt, exiting...')
    sys.exit(signal)

class Cli(object):
    '''
    Usage: %(prog)s [options] [command]
    '''

    ACTIONS = {
        Action.NEW: new.gennew,
        Action.BUILD: build.builder,
        Action.REFRESH: refresh.refresher,
        Action.PUBLISH: publish.publisher,
        Action.SERVE: webserv.serve
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
            '--silence-detect',
            action='store',
            dest='cut_silence',
            type=bool,
            help='Valid for the `refresh` action. Enables silence detection and removal (Default: True).',
            default=True,
        )

        options.add_argument(
            '--silence-threshold',
            action='store',
            dest='silence_threshold',
            help='Valid for the `refresh` action. Silence threshold in decibels (default: 30).',
            type=int,
        )

        options.add_argument(
            '--silence-duration',
            action='store',
            dest='silence_duration',
            help='Valid for the `refresh` action. Minimum silence duration in seconds (default: 1.2).',
            type=float,
        )

        options.add_argument(
            '--silence-pad',
            action='store',
            dest='silence_pad',
            help='Valid for the `refresh` action. Padding in milliseconds before/after silence removal (default: 350).',
            type=int,
            default=350
        )

        options.add_argument(
            '--no-title',
            action='store_false',
            dest='title',
            help="Don't generate a title on refresh.",
        )

        options.add_argument(
            '--no-description',
            action='store_false',
            dest='description',
            help="Don't generate a description on refresh.",
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
            choices=base.BaseCommand.LANGS,
            default=None
        )

        options.add_argument(
            '--workspace',
            action='store',
            dest='workspace',
            help='Valid for the `serve` action. Workspace directory for video projects.',
            default=None
        )

        options.add_argument(
            '--http-port',
            action='store',
            dest='http_port',
            help='Valid for the `serve` action. HTTP port for web server (default: 9091).',
            type=int,
            default=None
        )

        options.add_argument(
            '--webroot',
            action='store',
            dest='webroot',
            help='Valid for the `serve` action. Directory containing web assets.',
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
        if opts.language == None:
            del opts.language # type: ignore
        if opts.overwrite == None:
            del opts.overwrite # type: ignore
        if opts.subtitles == None:
            del opts.subtitles # type: ignore
        if opts.autoplay == None:
            del opts.autoplay # type: ignore
        if opts.cut_silence == None:
            del opts.cut_silence # type: ignore
        if opts.silence_duration == None:
            del opts.silence_duration # type: ignore
        if opts.silence_threshold == None:
            del opts.silence_threshold # type: ignore
        if opts.workspace == None:
            del opts.workspace # type: ignore
        if opts.http_port == None:
            del opts.http_port # type: ignore
        if opts.webroot == None:
            del opts.webroot # type: ignore
        self.config['ytffmpeg'].update(vars(opts))
        # The following "defaults" are set **after** everything above because if a default is
        # defined in the ArgumentParser(), it does not allow ~/.config/ytffmpeg/config.yml
        # to define the default behaviour/config. Setting it here ensures that is possible
        # and if still not defined (e.g. config absent), we can define in-code.
        self.config['ytffmpeg']['silence_duration'] = self.config['ytffmpeg'].get('silence_duration', 1.2)
        self.config['ytffmpeg']['silence_threshold'] = self.config['ytffmpeg'].get('silence_threshold', 30)

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
        signal(SIGINT, interrupt)
        return action(self.config)

__all__ = ['base', 'new', 'build', 'refresh', 'publish', 'webserv', 'Cli']
