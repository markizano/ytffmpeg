'''
Base module for all CLI commands in `ytffmpeg`.

'''
import os
import subprocess
import time

import ffmpeg

from ..types import WhisperTask

from kizano import getLogger
log = getLogger(__name__)

class BaseCommand(object):
    '''
    Base class for all ytffmpeg commands.
    Other commands will derive this class so they will have access to the
    same functionality.
    '''

    # class constants
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'large-v2')
    WHISPER_PNG = '/home/YouTube/resources/openai.png'
    DEVICES = ['cpu', 'cuda', 'auto']
    LANGS = ["auto","af","am","ar","as","az","ba","be","bg","bn","bo","br","bs","ca",
    "cs","cy","da","de","el","en","es","et","eu","fa","fi","fo","fr","gl","gu","ha",
    "haw","he","hi","hr","ht","hu","hy","id","is","it","ja","jw","ka","kk","km","kn",
    "ko","la","lb","ln","lo","lt","lv","mg","mi","mk","ml","mn","mr","ms","mt","my",
    "ne","nl","nn","no","oc","pa","pl","ps","pt","ro","ru","sa","sd","si","sk","sl",
    "sn","so","sq","sr","su","sv","sw","ta","te","tg","th","tk","tl","tr","tt","uk",
    "ur","uz","vi","yi","yo","zh"]

    def __init__(self, config: dict):
        self.config = config

    def filename(self, path: str) -> str:
        '''
        Gets the filename without the extension or leading path.
        '''
        return os.path.splitext(os.path.basename(path))[0]

    def isOverwrite(self) -> bool:
        '''
        Checks to see if the overwrite flag is set.
        '''
        return self.config['ytffmpeg'].get('overwrite', False)

    def isSubtitles(self) -> bool:
        '''
        Checks to see if the subtitles flag is set.
        '''
        return self.config['ytffmpeg'].get('subtitles', True)

    def isSilenceDetector(self) -> bool:
        '''
        Checks to see if we are detecting silence.
        '''
        return self.config['ytffmpeg'].get('cut_silence', False)

    def has_video(self, vid: str) -> bool:
        '''
        Check the list of videos. If any of the input videos match the resource using filename() then return True.
        '''
        for video in self.config['videos']:
            for inputVid in video['input']:
                if inputVid['i'] == vid:
                    return True
        return False

    def get_video_config(self, vid: str) -> dict:
        '''
        Get specific video configuration of a video by input name.
        '''
        for video in self.config['videos']:
            for invid in video['input']:
                if self.filename(invid['i']).lower() in vid.lower():
                    return video
        return {}

    def get_subtitles(self, video_path: str, lang: str) -> str:
        '''
        Generate subtitles for a video file using the whisper script directly.
        Returns the path to the generated SRT file.
        '''
        if not self.isSubtitles():
            log.warning(f'Failed to get subtitles for {video_path}! Subtitles not enabled.')
            return ''

        srt_path = os.path.join('build', f"{self.filename(video_path)}.{lang}.srt")
        log.info(f"Generating subtitles for {srt_path} from {video_path}... This might take a while...")

        if os.path.exists(srt_path):
            if self.isOverwrite():
                log.info(f"Overwriting existing subtitles for \x1b[1m{srt_path}\x1b[0m!")
            else:
                log.info(f"Subtitles already generated for \x1b[1m{srt_path}\x1b[0m!")
                return srt_path

        # Ensure build directory exists
        os.makedirs('build', exist_ok=True)

        # Build whisper command
        whisper_cmd = [
            'whisper',
            '--model', self.config['ytffmpeg'].get('whisper_model', BaseCommand.WHISPER_MODEL),
            '--device', self.config['ytffmpeg'].get('device', 'cuda'),
            '--output_dir', 'build',
            '--output_format', 'srt',
            '--language', lang,
            '--task', os.environ.get('WHISPER_TASK', WhisperTask.TRANSCRIBE),
            '--word_timestamps', 'True',
            '--append_punctuations', 'True',
            '--prepend_punctuations', 'True',
            '--max_words_per_line', '5',
            '--highlight_words', 'True',
            '--verbose', 'False',
        ]

        # Add temperature if specified
        if 'whisper_temperature' in self.config['ytffmpeg']:
            whisper_cmd.extend(['--temperature', str(self.config['ytffmpeg']['whisper_temperature'])])

        # Add the video file
        whisper_cmd.append(video_path)

        log.info(f"Running whisper command: {' '.join(whisper_cmd)}")

        try:
            now = time.time()
            result = subprocess.run(whisper_cmd, capture_output=True, text=True, check=True)
            then = time.time()

            log.info(f"Whisper completed in {round(then-now, 4)} seconds!")
            log.debug(f"Whisper stdout: {result.stdout}")
            if result.stderr:
                log.debug(f"Whisper stderr: {result.stderr}")

            # Whisper will create the SRT file with the same name as the video but with .srt extension
            # We need to rename it to match our expected naming convention
            expected_whisper_srt = os.path.join('build', f"{self.filename(video_path)}.srt")
            if os.path.exists(expected_whisper_srt) and expected_whisper_srt != srt_path:
                os.rename(expected_whisper_srt, srt_path)
                log.info(f"Renamed {expected_whisper_srt} to {srt_path}")

            return srt_path

        except subprocess.CalledProcessError as e:
            log.error(f"Whisper failed with exit code {e.returncode}")
            log.error(f"Whisper stderr: {e.stderr}")
            return ''
        except FileNotFoundError:
            log.error("Whisper command not found. Please ensure whisper is installed and available in PATH.")
            return ''
