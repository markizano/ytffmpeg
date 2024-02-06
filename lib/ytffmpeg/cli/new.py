'''
This module will enact the operations needed to craft a new project directory with the following
data structure:

    .
    ├── build/
    ├── readme.md
    ├── resources/
    └── ytffmpeg.yml

The user will then be able to upload/place files in the `./resources` directory and run the
`ytffmpeg refresh` command to update the `ytffmpeg.yml` file with the new media.
'''

import os
import yaml
from kizano import getLogger
log = getLogger(__name__)

def gennew(config: dict) -> int:
    '''
    Produce a new project directory.
    '''
    log.debug(config)
    if 'resource' in config['ytffmpeg']:
        if not os.path.exists(config['ytffmpeg']['resource']):
            log.info(f"Creating new resource directory in {config['ytffmpeg']['resource']}.")
            os.mkdir(config['ytffmpeg']['resource'])
        else:
            if not os.path.isdir(config['ytffmpeg']['resource']):
                log.error(f"{config['ytffmpeg']['resource']} is not a directory!")
                return 1
        os.chdir(config['ytffmpeg']['resource'])
    log.info(f'Creating new project directory in {os.getcwd()}.')
    initconfig = {
        'videos': [],
    }
    if not os.path.exists('build'):     os.mkdir('build')
    if not os.path.exists('resources'): os.mkdir('resources')
    if not os.path.exists('readme.md'): open('readme.md', 'w').write('')
    if not os.path.exists('ytffmpeg.yml'):
        open('ytffmpeg.yml', 'w').write(yaml.dump(initconfig))
    log.info('Created new project directory in current working directory.')
    return 0


