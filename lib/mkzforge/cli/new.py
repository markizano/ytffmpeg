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
from mkzforge import getLogger, videos
log = getLogger(__name__)

def gennew(cfg: dict) -> int:
    '''
    Produce a new project directory.
    '''
    if 'resource' in cfg:
        resource = os.path.realpath(cfg['resource'])
    else:
        resource = os.getcwd()
    log.info(f'New project to create in {resource}')
    videos.newProject(resource, **cfg)
    return 0


