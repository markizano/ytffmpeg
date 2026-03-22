'''
This module will enact the operations needed to craft a new project directory with the following
data structure:

    .
    ├── build/
    ├── readme.md
    ├── resources/
    └── mkzforge.yml

The user will then be able to upload/place files in the `./resources` directory and run the
`mkzforge refresh` command to update the `mkzforge.yml` file with the new media.
'''

import os
import yaml
from kizano import getLogger
log = getLogger(__name__)

def gennew(config: dict) -> int:
    '''
    Produce a new project directory.
    '''
    if 'resource' in config['mkzforge']:
        resource_path = os.path.realpath(config['mkzforge']['resource'])
        if not os.path.exists(resource_path):
            log.info(f"Creating new resource directory in {resource_path}.")
            os.makedirs(resource_path, exist_ok=True)
        else:
            if not os.path.isdir(resource_path):
                log.error(f"{resource_path} is not a directory!")
                return 1
        os.chdir(resource_path)
    log.info(f'Creating new project directory in {os.getcwd()}.')
    initconfig = {
        'videos': [],
    }
    if not os.path.exists('build'):     os.mkdir('build')
    if not os.path.exists('resources'): os.mkdir('resources')
    if not os.path.exists('readme.md'): open('readme.md', 'w').write('')
    if not os.path.exists('mkzforge.yml'):
        open('mkzforge.yml', 'w').write(yaml.dump(initconfig))
    log.info('Created new project directory in current working directory.')
    return 0


