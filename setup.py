#!/usr/bin/env python3

import os
import sys
from glob import glob
from pprint import pprint
from setuptools import setup

sys.path.insert(0, os.path.abspath('lib'))

setup_opts = {
    'name'                : 'ytffmpeg',
    # We change this default each time we tag a release.
    'version'             : '1.1.0',
    'description'         : 'Scripts and tools to ease the processing of videos for Social Media platforms.',
    'long_description'    : ('This is a library that ingests configuration formats and converts them into '
                            'actions that will end up processing videos in a streamlined fashion in hopes '
                            'automating the pipeline on how videos get created.'),
    'long_description_content_type': 'text/markdown',
    'author'              : 'Markizano Draconus',
    'author_email'        : 'support@markizano.net',
    'url'                 : 'https://markizano.net/',
    'license'             : 'GNU',

    'tests_require'       : ['pytest', 'mock'],
    'install_requires'    : [
      'PyYAML>=6.0.1',
      'kizano',
      'ffmpeg-python==0.2.0',
      'nvidia-pyindex',
      'nvidia-cudnn',
      'openai',
      'openai-whisper',
      'faster-whisper',
      'numba',
      'requests'
    ],
    'package_dir'         : { 'ytffmpeg': 'lib/ytffmpeg' },
    'packages'            : [
      'ytffmpeg', 'ytffmpeg.cli'
    ],
    'scripts'             : glob('bin/*'),
    'entry_points': {
      'console_scripts': [
        'ytffmpeg=ytffmpeg:main'
      ],
    },
    'test_suite'          : 'tests',
}

try:
    import argparse
    HAS_ARGPARSE = True
except:
    HAS_ARGPARSE = False

if not HAS_ARGPARSE: setup_opts['install_requires'].append('argparse')

# I botch this too many times.
if sys.argv[1] == 'test':
    sys.argv[1] = 'nosetests'

if 'DEBUG' in os.environ: pprint(setup_opts)

setup(**setup_opts)

