from enum import StrEnum

class Devices(StrEnum):
    '''
    Poor man's enumeration() object for device types.
    '''
    CPU = 'cpu'
    GPU = 'cuda'
    CUDA = 'cuda'
    AUTO = 'auto'

class Action(StrEnum):
    NEW = 'new'
    BUILD = 'build'
    REFRESH = 'refresh'
    SUBS = 'gensubs'
    LOADMOD = 'load-module'
    PUBLISH = 'publish'
    SERVE = 'serve'

class WhisperTask(StrEnum):
    TRANSCRIBE = 'transcribe'
    TRANSLATE = 'translate'

