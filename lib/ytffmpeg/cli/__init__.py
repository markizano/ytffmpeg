
from argparse import ArgumentParser, RawTextHelpFormatter
from kizano import getLogger
log = getLogger(__name__)

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
            'new',
            action='store_const',
            dest='action',
            help='Create a new project directory.',
            const=YTFFMPEG_Action.NEW
        )

        options.add_argument(
            'refresh',
            action='store_const',
            dest='action',
            help=('Refresh the resources directory with any new media. Convert resources/*.mp4 to mkv and update ytffmpeg.yml '
                'as necessary with new available media.'),
            const=YTFFMPEG_Action.REFRESH
        )

        options.add_argument(
            'publish',
            action='store_const',
            dest='action',
            help='For each of the supported configured social media sites, publish the build results to the channel.',
            const=YTFFMPEG_Action.PUBLISH
        )

        opts = options.parse_args()
        self.config['ytffmpeg'].update(vars(opts))

    def execute(self):
        '''
        Interprets command line options and calls the subsequent actions to take.
        These will be built out as sub-modules to this module.
        '''
        # These don't exist yet, but will be created.
        from .new import main as new
        from .refresh import main as refresh
        from .publish import main as publish
        action = {
            YTFFMPEG_Action.NEW: new,
            YTFFMPEG_Action.REFRESH: refresh,
            YTFFMPEG_Action.PUBLISH: publish
        }.get(self.config['action'])
        if not action:
            log.error('Invalid action: %s', self.config['action'])
            return 1
        return action(self.config)
