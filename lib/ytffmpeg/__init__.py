import kizano
kizano.Config.APP_NAME = 'ytffmpeg'  # type: ignore

from logging import Logger
import ytffmpeg.cli as cli
import ytffmpeg.filter_complex as filter_complex
import ytffmpeg.genimg as genimg
import ytffmpeg.metadata as metadata
import ytffmpeg.subtitles as subtitles
import ytffmpeg.notify as notify
import ytffmpeg.videos as videos

def getLogger(n: str, ll: str, lf: str) -> Logger: return kizano.getLogger(n, ll, lf)
log = getLogger(__name__)

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

__all__ = [
    'getLogger',
    'main',
    'cli',
    'filter_complex',
    'genimg',
    'metadata',
    'subtitles',
    'notify',
    'videos',
]
