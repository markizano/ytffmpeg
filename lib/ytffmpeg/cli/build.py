'''
Build opertions for ytffmpeg.
This will read the central configuration and the local configuration, combine the two, and
execute the build operations for each of the videos specified.

If a video is specified, only that video will be built.
'''

import os
import time
import subprocess
from .base import BaseCommand
from ..filter_complex import FilterComplexFunctionUnit

from kizano import getLogger
log = getLogger(__name__)

class BuildCommand(BaseCommand):
    '''
    Build command for ytffmpeg.
    '''

    def __init__(self, config: dict):
        super().__init__(config)

    def processRequirements(self, requirements: list) -> None:
        '''
        If we have dependencies, process them first before building this video.
        '''
        if isinstance(requirements, str):
            require_videos = requirements.split(' ')
        else:
            require_videos = requirements
        for require_video in require_videos:
            if not os.path.exists(require_video):
                log.warning(f'\x1b[34mRequired\x1b[0m video \x1b[1m{require_video}\x1b[0m is a dependency of this video, building that first.')
                subprocess.run(['ytffmpeg', 'build', '--no-autoplay', require_video])
            for video in self.config['videos']:
                if video['output'] == require_video:
                    # We are consuming the ytffmpeg configuration on build, so pop it off the list.
                    self.config['videos'].remove(video)

    def processInput(self, input_video: str|dict) -> list:
        '''
        Process one branch of the data structure that defines an input video.
        For each of the options, include it on the command line.
        Lead with -f for the format.
        Tail with -i for the input file.
        In this way, all options for that video are processed on the command line in the correct order.
        '''
        input_cmd = []
        if isinstance(input_video, str):
            log.debug(f'INPUT stream: \x1b[1m{input_video}\x1b[0m')
            input_cmd.append('-i')
            input_cmd.append(input_video)
        elif isinstance(input_video, dict):
            assert 'i' in input_video, 'No input specified for video!'
            i = input_video.pop('i')
            log.debug(f'INPUT stream: \x1b[1m{i}\x1b[0m')
            while len(input_video):
                # Make sure the format is the first argument to be added.
                if 'f' in input_video:
                    input_cmd.append('-f')
                    input_cmd.append(input_video.pop('f'))
                # Add other arguments in the middle
                if len(input_video) >= 1:
                    name, value = input_video.popitem()
                    input_cmd.append(f'-{name}')
                    input_cmd.append(value)
            input_cmd.append('-i')
            input_cmd.append(i)
        return input_cmd

    def parseFunction(self, func: dict) -> str:
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

        Which will result in `fade=in:st=1:d=1:enable='between(t, 1, 3)'`

        Things to keep in mind: https://www.abyssale.com/generate-video/how-to-change-the-appearances-of-subtitles-with-ffmpeg
        Styles available for subtitles:
        - Fontname
        - Fontsize
        - PrimaryColour
        - SecondaryColour
        - OutlineColour
        - BackColour

        Also Colour format is NOT ARGB, it's ABGR!
        '''
        assert isinstance(func, dict), '`func` must be a dictionary!'
        assert len(list(func.keys())) == 1, f'`func` must have only 1 key that is the function name! In: {func}'
        function = list(func.keys())[0]
        args = []
        if isinstance(func[function], dict):
            for arg in func[function].items():
                args.append( '='.join(arg) )
        elif isinstance(func[function], (list, tuple)):
            args.extend(func[function])
        elif isinstance(func[function], str):
            args.append( func[function] )
        else:
            raise ValueError('Unknown type "%s" from func[%s]!' % ( type(func[function]), function ) )
        return function + '=' + ':'.join(args)

    def processFilterComplex(self, filter_complex_filename: str, filter_complex_script: list) -> None:
        '''
        Here's where things get interesting with filter_complex.
        In its simplest form, it's a list of strings that are joined together with a semicolon.
        In its most complex form, it's a data structure where each key is a function, and the value
        of that object is the set of arguments that are fed to that function.
        The challenge comes into play with the streams and how to operate with named streams in ffmpeg.
        All inputs are available to the filter_complex. By default, only [video] and [audio] are mapped
        in the resulting output unless the .videos[].attributes specifies otherwise.
        If the filter_complex string result is greater than the bash max string for arguments,
        then this needs to write to a file and tell ffmpeg to use `-filter_complex_script` to refer
        to that file. I am torn as to whether I should just do this as the default for easier
        inspection and debugging of the final filter_complex result.
        This might also result in less interpolation against the command line that may need to happen.
        '''
        result = []
        log.info(f'Writing out \x1b[1m{filter_complex_filename}\x1b[0m script...')
        with open(filter_complex_filename, 'w') as fc:
            for i, filter_complex in enumerate(filter_complex_script):
                if isinstance(filter_complex, str):
                    # Ignore commented lines.
                    if filter_complex.startswith('#'): continue
                    # Otherwise add the string.
                    result.append(filter_complex)
                elif isinstance(filter_complex, dict):
                    assert 'istream' in filter_complex, f'I need an input stream specified in filter_complex[{i}]!'
                    assert 'ostream' in filter_complex, f'I need an output stream specified in filter_complex[{i}]!'
                    assert 'filters' in filter_complex, f'I need a list of functions specified in filter_complex[{i}]!'
                    funcs = ','.join( map(lambda x: self.parseFunction(x['func']), filter_complex['funcs']) )
                    filter_complex_str = f'[{filter_complex["istream"]}] {funcs} [{filter_complex["ostream"]}]'
                    result.append(filter_complex_str)
            fc.write(";\n".join(result))
            fc.flush()
        log.info(f'Done writing out \x1b[1m{filter_complex_filename}\x1b[0m script!')

    def execute(self):
        '''
        Build the videos described by `ytffmpeg.yml`, so load that configuration up first.
        If a resource video was provided to build, only build that one.

        '''
        now = time.time()
        if 'resource' in self.config['ytffmpeg']:
            videos = list( filter(lambda x: x['output'] == self.config['ytffmpeg']['resource'], self.config['videos']) ) or []
        else:
            videos = self.config['videos']
        while videos:
            video_opts = videos.pop(0)
            final_cmd = [os.getenv('FFMPEG_BIN', 'ffmpeg'), '-hide_banner']
            assert 'input' in video_opts, 'No input specified for video!'
            assert 'output' in video_opts, 'No output specified for video!'
            vidnow = time.time()
            output = video_opts["output"]
            if output is None:
                log.warning(f'Skipping vid because output is set to None.')
                continue
            attributes = video_opts.get('attributes', [])
            log.info(f'Processing video: \x1b[1m{output}\x1b[0m')
            # If we have pre-existing requirements or videos this is dependent on, process them first.
            if 'require' in video_opts:
                self.processRequirements(video_opts['require'])
            # Append the `-i` arguments accordingly.
            for input_video in video_opts['input']:
                final_cmd.extend(self.processInput(input_video))
            if os.path.exists('thumbnail.png'):
                final_cmd.append('-i')
                final_cmd.append('thumbnail.png')
            # Process a filter_complex if we have one.
            if 'filter_complex' in video_opts:
                filter_complex = f'build/{self.filename(output)}.filter_complex'
                self.processFilterComplex(filter_complex, video_opts['filter_complex'])
                final_cmd.append('-filter_complex_script')
                final_cmd.append(filter_complex)
            # Strip previous metadata.
            final_cmd.append('-map_metadata')
            final_cmd.append('-1')
            language = video_opts.get('language', 'en')

            # Attach current required metadata.
            if 'metadata' in video_opts:
                for name, value in video_opts['metadata'].items():
                    final_cmd.append('-metadata')
                    final_cmd.append(f'{name}={value}')
            # If there's custom mapping involved, ensure that is handled as well.
            if 'no-video' not in attributes:
                final_cmd.append('-map')
                final_cmd.append(video_opts.get('map', {}).get('video', '[video]'))
            if 'no-audio' not in attributes:
                final_cmd.append('-map')
                final_cmd.append(video_opts.get('map', {}).get('audio', '[audio]'))
            if 'subs' in attributes:
                if 'languages' in video_opts:
                    # If you set languages and subs, then we assume you know you need to set
                    # map to each of the language inputs you want to include as well.
                    for ilang in video_opts['languages']:
                        lang, i = ilang.split(':')
                        final_cmd.append('-map')
                        final_cmd.append(video_opts['map'][lang])
                        final_cmd.append(f'-metadata:s:s:{i}')
                        final_cmd.append(f'language={lang}')
                else:
                    final_cmd.append('-map')
                    final_cmd.append(video_opts.get('map', {}).get('subs', '[subs]'))
                    final_cmd.append('-metadata:s:s')
                    final_cmd.append(f'language=eng')

            if 'vsync' in attributes:
                final_cmd.append('-fps_mode')
                final_cmd.append('vfs')
            if 'no-video' in attributes:
                final_cmd.append('-vn')
            else:
                final_cmd.append('-c:v')
                final_cmd.append(video_opts.get('codecs', {}).get('video', 'h264'))
                final_cmd.append('-pix_fmt')
                final_cmd.append('yuv420p')
                final_cmd.append('-crf')
                final_cmd.append('28')
                final_cmd.append('-metadata:s:v')
                final_cmd.append(f'language={language}')
            if 'no-audio' in attributes:
                final_cmd.append('-an')
            else:
                final_cmd.append('-c:a')
                final_cmd.append(video_opts.get('codecs', {}).get('audio', 'aac'))
                final_cmd.append('-metadata:s:a')
                final_cmd.append(f'language={language}')
            if 'subs' in attributes:
                final_cmd.append('-c:s')
                final_cmd.append('mov_text')

            if 'movflags' in video_opts:
                final_cmd.append('-movflags')
                final_cmd.append(video_opts['movflags'])
            if os.path.exists('thumbnail.png'):
                i = len(video_opts['input'])
                final_cmd.append(f'-disposition:v:{i}')
                final_cmd.append('attached_pic')

            # Attach the output file.
            final_cmd.append('-y')
            final_cmd.append(video_opts['output'])
            log.info(f'Execute: \x1b[34m{" ".join(final_cmd)}\x1b[0m')
            if os.path.exists(video_opts['output']):
                if self.isOverwrite():
                    log.info(f'Overwriting existing \x1b[1m{output}\x1b[0m!')
                else:
                    log.info(f'File \x1b[1m{output}\x1b[0m already exists!')
                    continue
            subprocess.run(final_cmd, shell=False)
            vidthen = time.time()
            if not self.config['ytffmpeg'].get('autoplay', True):
                log.info(f'Done processing \x1b[1m{output}\x1b[0m in {round(vidthen-vidnow,4)} seconds!')
                continue
            log.info(f'Done processing \x1b[1m{output}\x1b[0m in {round(vidthen-vidnow,4)} seconds! Now playing...')
            media_player = self.config['ytffmpeg'].get('media_player', 'mpv')
            subprocess.run([media_player, output], shell=False)
        os.system('stty echo -brkint -imaxbel icanon iexten icrnl')
        then = time.time()
        log.info(f'Completed all media in \x1b[4m{round(then-now, 2)}\x1b[0m seconds!')
        return 0

def builder(config: dict) -> int:
    '''
    Entrtypoint for this model.
    '''
    cmd = BuildCommand(config)
    return cmd.execute()
