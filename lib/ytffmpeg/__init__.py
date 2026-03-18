import kizano
kizano.Config.APP_NAME = 'ytffmpeg'  # type: ignore

from logging import Logger
def getLogger(n: str, ll: str = None, lf: str = 'standard') -> Logger: return kizano.getLogger(n, ll, lf)

import ytffmpeg.types as types
import ytffmpeg.const as const
import ytffmpeg.cli as cli
import ytffmpeg.genimg as genimg
import ytffmpeg.metadata as metadata
import ytffmpeg.subtitles as subtitles
import ytffmpeg.i18n as i18n
import ytffmpeg.notify as notify
import ytffmpeg.videos as videos

def main():
    '''
    Main entry point for this application.
    Let's you run commands for ytffmpeg.
    '''
    log = getLogger(__name__)
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

__all__ = [
    'getLogger',
    'main',
    'types',
    'const',
    'cli',
    'genimg',
    'metadata',
    'subtitles',
    'i18n',
    'notify',
    'videos',
]
