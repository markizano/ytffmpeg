
from typing import Any, Iterable
from kizano import getLogger
log = getLogger(__name__)

class FilterComplexFunctionList(list):
    '''
    Overloads an array object to represent a collection, but ensure data types are correct
    and string representations look like ffmpeg filter_complex functions.
    '''

    def __init__(self, iterable: Iterable = None) -> None:
        if iterable:
            super().__init__((FilterComplexFunctionUnit(i) for i in iterable))
        else:
            super().__init__()

    def __str__(self) -> str:
        return ','.join([ str(x) for x in self ])

    def __setitem__(self, index, item):
        super().__setitem__(index, FilterComplexFunctionUnit(item))

    def insert(self, index, item):
        super().insert(index, FilterComplexFunctionUnit(item))

    def append(self, item):
        super().append(FilterComplexFunctionUnit(item))

    def extend(self, other):
        if isinstance(other, type(self)):
            super().extend(other)
        else:
            super().extend(FilterComplexFunctionUnit(item) for item in other)

class FilterComplexStream(object):
    '''
    A filter complex stream. This acts as a single line that represents a stream of either video,
    audio or subtitles.
    That is to say this will have an input stream, an output stream and any number of functions
    to perform transformations on that stream.
    '''

    def __init__(self, istreams: list, ostreams: list, funcs: FilterComplexFunctionList) -> None:
        self.istreams = []
        self.ostreams = []
        self.functions = FilterComplexFunctionList()
        if isinstance(istreams, type(self)): # Ability to canabalize another FilterComplexStream object.
            self.istreams = istreams.istreams
            self.ostreams = istreams.ostreams
            self.functions = istreams.functions
        else:
            assert isinstance(istreams, (list, tuple, set)), 'Argument istreams must be a list!'
            assert isinstance(ostreams, (list, tuple, set)), 'Argument ostreams must be a list!'
            assert isinstance(funcs, (list, tuple, set, FilterComplexFunctionList)), 'Argument funcs must be an array!'
            self.istreams = istreams
            self.ostreams = ostreams
            self.functions = funcs

    def __str__(self) -> str:
        return f'[{"][".join(self.istreams)}] {self.functions} [{"][".join(self.ostreams)}]'

    def __repr__(self) -> str:
        return f'<FilterComplexStream input={self.istreams} output={self.ostreams} functions={self.functions}>'

class FilterComplexFunctionUnit(object):
    '''
    A single unit of a filter_complex.
    Name can be any of the filters as described by https://ffmpeg.org/ffmpeg-filters.html
    Args is a list of arguments to be passed to that filter.
    FFMPEG is kind of like Python in that it accepts args and kwargs, so accept both kinds as arguments.
    Order of args matters and kwargs can be placed in any order.
    Example:
    {
        'name': 'trim',
        'args': [
            'start=1.15',
            'end=4.5'
        ]
    }

    Example:
    {
        'name': 'fade',
        'args': [
            'in',
            'st=1',
            'd=3',
            "enable='between(t, 1, 3)'"
        ]
    }

    Which will result in `fade=in:st=1:d=1:enable='between(t, 1, 3)'` when coerced to a string.

    I also want this implementation to be able to handle any function ffmpeg supports today or
    may support in the future. This part of the lexer should not care about which functions
    are being passed through.
    '''

    def __init__(self, name: str, *args, **kwargs) -> None:
        '''
        The constructor should be able to handle any of the following argument styles:
        unit = FilterComplexFunctionUnit('trim=start=1.15:end=4.5')
        unit = FilterComplexFunctionUnit('trim', 'start=1.15:end=4.5')
        unit = FilterComplexFunctionUnit('trim', ['start=1.15', 'end=4.5'])
        unit = FilterComplexFunctionUnit('trim', {'start': '1.15', 'end': '4.5'})
        '''
        assert isinstance(name, (str, type(self))), 'Argument name must be string!'
        if isinstance(name, type(self)):
            args = list(args) + name.args
            kwargs = dict(kwargs, **name.kwargs)
            name = name.name
        if '=' in name:
            name, nameargs = name.split('=', 1)
            args = list(args) + nameargs.split(':')
            del nameargs
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def __str__(self) -> str:
        if not hasattr(self, 'args'):
            args = []
        else:
            args = ':'.join(self.args)
        kwargs = ':'.join([ '='.join(x) for x in self.kwargs.items() ])
        if len(args) > 0 and len(kwargs) > 0:
            return f'{self.name}={args}:{kwargs}'
        elif len(args) > 0:
            return f'{self.name}={args}'
        elif len(kwargs) > 0:
            return f'{self.name}={kwargs}'
        else:
            return self.name

    def __repr__(self) -> str:
        return f'<FilterComplexFunctionUnit name={self.name} args={self.args} kwargs={self.kwargs}>'

    def __setattr__(self, __name: str, __value: Any) -> None:
        def process_str(val: str) -> None:
            assert isinstance(val, str), 'val must be a string!'
            #log.debug(f'val is a string: {val}')
            if ':' in val: # In the case of trim, "start=1.15:end=4.5"
                #log.debug(f'val is a multi-arg array: {val}')
                for arg in val.split(':'):
                    if '=' in arg:
                        #log.debug(f'arg is a kwarg: {arg}')
                        kwname, kwval = arg.split('=', 1)
                        self.__dict__['kwargs'][kwname] = kwval
                    else:
                        #log.debug(f'arg is an arg: {arg}')
                        self.__dict__['args'].append(arg)
            elif '=' in val: # In the case of trim, "start=1.15" and no second argument.
                #log.debug(f'val is a kwarg: {val}')
                kwname, kwval = val.split('=', 1)
                self.__dict__['kwargs'][kwname] = kwval
            else: # In the case of concat with no arguments or a single argument like fade, "in"
                #log.debug(f'val is an arg: {val}')
                self.__dict__['args'].append(val)

        for name in ['name', 'args', 'kwargs']:
            if name not in self.__dict__:
                self.__dict__[name] = {'name': '', 'args': [], 'kwargs': {}}.get(name)
        if __name == 'name':
            assert isinstance(__value, str), 'name must be a string!'
            self.__dict__[__name] = __value
        elif __name in ('args', 'kwargs'):
            #log.debug(f'__setattr__({__name}, {__value} as {type(__value)})')
            if __name not in self.__dict__:
                self.__dict__[__name] = [] if __name == 'args' else {}
            if isinstance(__value, str):
                #log.debug(f'__value is a string: {__value}')
                process_str(__value)
            elif isinstance(__value, (list, tuple, set)):
                #log.debug(f'__value is an array: {__value}')
                for val in __value:
                    # Somehow a list of tuples gets passed in ...
                    if isinstance(val, (list, tuple, set)):
                        for _val in val:
                            process_str(_val)
                    elif isinstance(val, dict):
                        self.__dict__['kwargs'].update(val)
                    elif isinstance(val, str):
                        process_str(val)
            elif isinstance(__value, dict):
                #log.debug(f'__value is a dict: {__value}')
                self.__dict__['kwargs'].update(__value)

