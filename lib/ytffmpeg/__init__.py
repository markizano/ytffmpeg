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
    kizano.log.setLevel(99)
    config = kizano.getConfig()
    if 'google' in config and 'api_key' in config['google']:
        const.GOOGLE_API_KEY = config['google']['api_key']
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
