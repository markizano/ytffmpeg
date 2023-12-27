import sys

import kizano
log = kizano.getLogger(__name__)
kizano.Config.APP_NAME = 'ytffmpeg'

import ytffmpeg.cli as cli

def main():
    '''
    Main entry point for this application.
    Let's you run commands for ytffmpeg.
    '''
    config = kizano.getConfig()
    if 'ytffmpeg' not in config:
        config['ytffmpeg'] = {}
    ytffmpeg = cli.YTFFMPEG_Cli(config)
    ytffmpeg.execute()

if __name__ == '__main__':
    sys.exit(main())
