#!/usr/bin/env python3

import io, os, sys
import json

import argparse
import time

from pprint import pprint

parser = argparse.ArgumentParser()

class FFMPEG(object):

    POST_DATE = {
        'drawtext': {
            'fontfile': '/home/YouTube/resources/DejaVuSans.ttf',
            'text': os.environ.get('POST_DATE', time.strftime('%F')),
            'fontcolor': 'black',
            'fontsize': '28',
            'box': '1',
            'boxcolor': 'white@0.8',
            'boxborderw': '10',
            'x': 'w-200',
            'y': '15'
        }
    }

    def __init__(self, cfg):
        self.config = cfg
        self._buildVideoCmds()

    def parseFunction(self, unit):
        '''
        Parse the data structure into a single-line string function we can input for ffmpeg's -filter_complex argument.
        This is a single-unit function. If you have an array of these objects, iterate over them calling this method.
        Example:
        unit = {
            'trim': {
                'start': '1.15',
                'end': '4.5'
            }
        }

        unit = {
            'trim': [
                'start=1.15',
                'end=4.5'
            ]
        }
        Both of these would return a string "trim=start=1.15:end=4.5"

        Also, dynamic enough to do stuff like:
        unit = {
            'fade': [
                'in',
                'st=1',
                'd=3',
                "enable='between(t, 1, 3)'"
            ]
        }
        '''
        assert isinstance(unit, dict), '`unit` must be a dictionary!'
        assert len(list(unit.keys())) == 1, '`unit` must have only 1 key that is the function name! In: %s' % unit
        function = list(unit.keys())[0]
        args = []
        if isinstance(unit[function], dict):
            for arg in unit[function].items():
                args.append( '='.join(arg) )
        elif isinstance(unit[function], (list, tuple)):
            print('list/tuple found!')
            args.extend(unit[function])
            pprint(args)
        elif isinstance(unit[function], str):
            args.append( unit[function] )
        else:
            raise ValueError('Unknown type "%s" from unit[%s]!' % ( type(unit[function]), function ) )
        import pdb
        if not isinstance(args, list):
            pdb.set_trace()
        return function + '=' + ':'.join(args)

    def parseFilterComplex(self, filter_complexes):
        '''
        Attempts to parse for a line to reference in the filter complex.
        Example:
        filter_complex = [{
            'istream': '[0:v]',
            'func': {...}, # Use trim() function example from above defined `self.parseFunction()`
            'ostream': '[video]'
        }]
        Returns a string of "[0:v]trim=start=1.5:end=4.5[video]" that will need quoting as per your needs
        after the return value (e.g. this function returns data only as a string. You would need to wrap
        quotes to escape to shell if you are writing results to a shell.
        If any of the items in `filter_complexes` are strings, just pass those along as-is for backwards-compat.
        '''
        # If we have an array, iterate and append each item, but try to parse them.
        result = []
        for fc in filter_complexes:
            if isinstance(fc, str):
                # If it's already a string, just pass it along.
                if fc.strip().startswith('#'): continue # but not if it's a comment.
                result.append(fc)
                continue

            # If it's an object/dict, then try to parse it into a string-like function.
            result.append(fc['istream'] + self.parseFunction(fc['func']) + fc['ostream'])
        return ';'.join( result )

    def _genVideoCmd(self, config):
        result = ['ffmpeg', '-hide_banner']
        config['attributes'] = config.get('attributes', [])
        config['require'] = config.get('require', '')
        if isinstance(config['input'], (list, tuple, set)):
            for video in config['input']:
                if isinstance(video, dict):
                    inputVideo = video['i']
                    del video['i']
                    for opt, val in video.items():
                        result.append('-%(opt)s %(val)s' % locals())
                    result.append('-i %s' % inputVideo)
                else:
                    result.append('-i')
                    result.append(video)
        else:
            # caution: if this is not a string or list, weird things can happen here... :O
            result.append('-i')
            result.append(config['input'])
        if 'filter_complex' in config:
            result.append('-filter_complex')
            if isinstance(config['filter_complex'], str):
                result.append(config['filter_complex']) # User's descretion on how they want their command quoted.
            elif isinstance(config['filter_complex'], list):
                result.append( '"' + self.parseFilterComplex(config['filter_complex'] ) + '"' )
        if 'filter_complex_script' in config:
            result.append('-filter_complex_script')
            fcsName = config['filter_complex_script'] + '.filter_complex'
            with io.open(config['filter_complex_script']) as fcs:
                with io.open(fcsName, 'w') as fcsOut:
                    for line in fcs:
                        if not line.strip() or line.strip().startswith('#') or line.strip().startswith(';'): continue
                        fcsOut.write(line)
            result.append(fcsName)
        if 'filter_complex' in config or 'filter_complex_script' in config:
            if 'no-video' not in config.get('attributes', []):
                result.append('-map')
                result.append('[video]')
            if 'no-audio' not in config.get('attributes', []):
                result.append('-map')
                result.append('[audio]')

        if 'no-audio' not in config.get('attributes', []):
            result.append('-c:a')
            result.append(config.get('codec', {}).get('audio', 'aac'))
        if 'no-video' not in config.get('attributes', []):
            result.append('-c:v')
            result.append(config.get('codec', {}).get('video', 'h264'))
        if 'metadata' in config:
            for name, value in config['metadata'].items():
                result.append('-metadata')
                result.append(f'"{name}={value}"')

        result.append('-map_metadata')
        result.append('-1')

        if 'vsync' in config['attributes']:
            result.append('-vsync 2')

        if 'movflags' in config:
            movflags = ' '.join(config['movflags'])
            result.append('-movflags ' + movflags)

        result.append('-y')
        result.append(config['output'])

        config['ffmpeg'] = ' '.join(result)
        return config['ffmpeg']

    def _buildVideoCmds(self):
        for video in self.config['videos']:
            if 'attributes' in video and 'include-only' in video['attributes']:
                continue
            self._genVideoCmd(video)

    def _genFinalCmd(self):
        '''
        Generate the final FFMPEG command based on what is already in inventory.
        Only run once per instance!
        '''
        final = {
            'deps': '',       # Makefile build dependencies.
            'input': '',      # List of `-i' arguments for video input.
            'vstreams': '',   # List of [0:v] streams to concat.
            'astreams': '',   # List of [0:a] streams to concat.
        }
        # Not every video == an index in the list.
        # Intentionally set this way to avoid filter_complex=[v:5][v:9][v:12]concat=n=3[video]
        i = 0
        for video in self.config['videos']:
            if 'not-a-build' in video['attributes']:
                continue
            vidName = video['output']
            final['input'] += ' -i %s' % vidName
            final['vstreams'] += '[%d:v]' % i
            final['astreams'] += '[%d:a]' % i
            if 'attributes' in video and 'include-only' in video['attributes']:
                continue
            final['deps'] += ' %s' % vidName
            i += 1
        final['streamCount'] = i
        final['date'] = self.parseFunction(FFMPEG.POST_DATE)
        if 'no-video' in self.config.get('attributes', []):
            final['vcodec'] = ''
        else:
            final['vcodec'] = '-c:v ' + self.config.get('vcodec', 'h264')
        if 'no-audio' in self.config.get('attributes', []):
            final['acodec'] = ''
        else:
            final['acodec'] = '-c:a ' + self.config.get('acodec', 'aac')
        result = ('build/final.mp4:%(deps)s\n'
            '\tffmpeg -hide_banner%(input)s'
            ' -filter_complex "%(vstreams)sconcat=n=%(streamCount)d,%(date)s[video];%(astreams)sconcat=v=0:a=1:n=%(streamCount)d[audio]"'
            ' -map [video] -map [audio] -map_metadata -1 %(vcodec)s %(acodec)s -vsync 2 -y build/final.mp4'
            '\n\n')
        return result % final

    def Makefile(self):
        '''
        Return the text necessary to put into Makefile for this ffmpeg config instance.

build/00_intro.mp4:
    $(ffmpeg) -i WalletsEx/VID_20211012_133822672.mp4 -vf scale=$(SCALE),setsar=1:1 -c:a aac -c:v h264 \
    -map_metadata -1 -y build/00_intro.mp4

        '''
        result = '''
all: build/final.mp4

clean:
\trm -fv build/*.mp4

'''
        i = 0
        for video in self.config['videos']:
            if 'attributes' in video and 'include-only' in video['attributes']:
                continue
            video['require'] = video.get('require', '')
            result += video['output'] + ( ': %(require)s\n\t%(ffmpeg)s' % video ) + '\n\n'
        result += self._genFinalCmd()
        return result


def main():
    parser.add_argument(
        '-c', '--config',
        action='store',
        dest='configFile',
        help='Path to configuration file (JSON format).',
        default='Makefile.config.json'
    )
    opts = parser.parse_args()
    #pprint(opts)
    config = json.load(io.open(opts.configFile, 'r'))
    #pprint(config)
    ff = FFMPEG(config)
    io.open('Makefile', 'w').write(ff.Makefile())
    print('Makefile written ^_^')
    if not os.path.exists('build'):
        os.mkdir('build')
    return 0


sys.exit(main())

