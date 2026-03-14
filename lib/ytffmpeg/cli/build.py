'''
Build opertions for ytffmpeg.
This will read the central configuration and the local configuration, combine the two, and
execute the build operations for each of the videos specified.

If a video is specified, only that video will be built.
'''

import os
import time
import subprocess
from copy import deepcopy as copy
from ytffmpeg.cli.base import BaseCommand
import ytffmpeg.genimg

from kizano import getLogger
log = getLogger(__name__)

class BuildCommand(BaseCommand):
    '''
    Build command for ytffmpeg.
    '''

    def __init__(self, config: dict):
        super().__init__(config)
        if not ytffmpeg.genimg.GOOGLE_API_KEY:
            ytffmpeg.genimg.GOOGLE_API_KEY = config['ytffmpeg'].get('google', {}).get('api_key')

    def processRequirements(self, requirements: list) -> None:
        '''
        If we have dependencies, process them first before building this video.
        '''
        log.info('Processing video dependencies...')
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
        log.info('Done processing dependencies.')

    def processInput(self, raw_input_video: str|dict) -> list:
        '''
        Process one branch of the data structure that defines an input video.
        For each of the options, include it on the command line.
        Lead with -f for the format.
        Tail with -i for the input file.
        In this way, all options for that video are processed on the command line in the correct order.
        '''
        input_cmd = []
        if isinstance(raw_input_video, str):
            log.debug(f'INPUT stream: \x1b[1m{raw_input_video}\x1b[0m')
            input_cmd.append('-i')
            input_cmd.append(raw_input_video)
        elif isinstance(raw_input_video, dict):
            assert 'i' in raw_input_video, 'No input specified for video!'
            input_video = copy(raw_input_video)
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

    def _preBuildHooks(self, video_opts: dict):
        log.info('**\x1b[1mPre-Build Hooks!\x1b[0m**')
        log.debug(f'CWD: {os.getcwd()}')
        # If we have pre-existing requirements or videos this is dependent on, process them first.
        if 'require' in video_opts:
            self.processRequirements(video_opts['require'])
        if video_opts.get('thumbnail', True):
            if not os.path.exists('thumbnail.png'):
                log.info('Generating thumbnail...')
                txt_path = f'build/{self.filename(video_opts["output"])}.txt'
                title = video_opts['metadata']['title']
                content = open(txt_path).read()
                ytffmpeg.genimg.generate_thumbnail(title, content)

    def execute(self):
        '''
        Build the videos described by `ytffmpeg.yml`, so load that configuration up first.
        If a resource video was provided to build, only build that one.

        '''
        with self.video_processing_lock('build'):
            now = time.time()
            if 'resource' in self.config['ytffmpeg']:
                log.info(f'Filtering process to just {self.config["ytffmpeg"]["resource"]} due to config.')
                videos = list( filter(lambda x: x['output'] == self.config['ytffmpeg']['resource'], self.config['videos']) ) or []
            else:
                log.info('Processing all configured videos in ytffmpeg.yml.')
                videos = self.config['videos']
            while videos:
                video_opts = videos.pop(0)
                final_cmd = [os.getenv('FFMPEG_BIN', 'ffmpeg'), '-hide_banner', '-noautorotate']
                assert 'input' in video_opts, 'No input specified for video!'
                assert 'output' in video_opts, 'No output specified for video!'
                assert isinstance(video_opts['input'], list), 'Input must be an array!'
                vidnow = time.time()
                output = video_opts["output"]
                if output is None:
                    log.warning(f'Skipping vid because output is set to None.')
                    continue
                attributes = video_opts.get('attributes', [])
                log.info(f'Processing video: \x1b[1m{output}\x1b[0m')
                self._preBuildHooks(video_opts)

                # Process ffmpeg input/output options.
                ## Append the `-i` arguments accordingly.
                for input_video in video_opts['input']:
                    final_cmd.extend(self.processInput(input_video))
                # With the pre-hook, this should just execute now.
                if os.path.exists('thumbnail.png'):
                    final_cmd.append('-i')
                    final_cmd.append('thumbnail.png')
                # Process a filter_complex if we have one.
                if 'filter_complex' in video_opts:
                    filter_complex = f'build/{self.filename(output)}.filter_complex'
                    self.processFilterComplex(filter_complex, video_opts['filter_complex'])
                    final_cmd.append('-/filter_complex')
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

                # With the pre-hook, this should just execute now.
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
    cmd = BuildCommand(copy(config))
    return cmd.execute()
