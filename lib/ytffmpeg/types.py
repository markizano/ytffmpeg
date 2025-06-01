from typing import NamedTuple

class Devices(NamedTuple):
    '''
    Poor man's enumeration() object for device types.
    '''
    CPU = 'cpu'
    GPU = 'cuda'
    CUDA = 'cuda'
    AUTO = 'auto'

class Action(NamedTuple):
    NEW = 'new'
    BUILD = 'build'
    REFRESH = 'refresh'
    SUBS = 'gensubs'
    LOADMOD = 'load-module'
    PUBLISH = 'publish'

class WhisperTask(NamedTuple):
    TRANSCRIBE = 'transcribe'
    TRANSLATE = 'translate'

