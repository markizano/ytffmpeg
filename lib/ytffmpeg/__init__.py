import sys

import kizano
log = kizano.getLogger(__name__)
kizano.Config.APP_NAME = 'ytffmpeg'

import ytffmpeg.cli as cli
import ytffmpeg.filter_complex as filter_complex

def main():
    '''
    Main entry point for this application.
    Let's you run commands for ytffmpeg.
    '''
    try:
        local_cfg = kizano.utils.read_yaml('ytffmpeg.yml')
    except Exception as e:
        log.warning(f'Local ytffmpeg.yml not found: {e}')
        local_cfg = {}
    config = kizano.utils.dictmerge( kizano.getConfig(), local_cfg )
    if 'ytffmpeg' not in config:
        config['ytffmpeg'] = {}
    ytffmpeg = cli.Cli(config)
    ytffmpeg.execute()

if __name__ == '__main__':
    sys.exit(main())
