'''
Base module for all CLI commands in `ytffmpeg`.

'''
import os, io
import time
import warnings
import ffmpeg

from typing import Iterable

from faster_whisper import WhisperModel
from faster_whisper.transcribe import Segment
from faster_whisper.utils import format_timestamp

from kizano import getLogger
log = getLogger(__name__)

from ytffmpeg.types import WhisperTask

class BaseCommand(object):
    '''
    Base class for all ytffmpeg commands.
    Other commands will derive this class so they will have access to the
    same functionality.
    '''

    # class constants
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'guillaumekln/faster-whisper-large-v2')
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
        self.whisper = None
        # Cached subtitle segments.
        self._subs = []

    def load_whisper(self) -> None:
        '''
        Load the whisper model.
        '''
        if self.config['ytffmpeg'].get('subtitles', True):
            log.info('Loading whisper model...')
            now = time.time()
            self.whisper = WhisperModel(
                BaseCommand.WHISPER_MODEL,
                device=self.config['ytffmpeg']['device'],
                compute_type='auto')
            then = time.time()
            log.info(f'Whisper model loaded in {round(then-now, 4)} seconds!')
        else:
            log.info('Subtitles not enabled. Skipping whisper model load.')

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

    def get_audio(self, path: str) -> str:
        '''
        Gets the audio stream for the specified file.
        '''
        filepath = self.filename(path)
        output_path = os.path.join('build', f"{filepath}.wav")
        log.info(f"Extracting audio from \x1b[1m{filepath}\x1b[0m to \x1b[1m{output_path}\x1b[0m...")
        # Check to see if the file is already in the build directory.
        if os.path.exists(output_path):
            if self.isOverwrite():
                log.info(f"Overwriting existing audio for \x1b[1m{filepath}\x1b[0m!")
            else:
                log.info(f"Audio already extracted for \x1b[1m{filepath}\x1b[0m!")
                return output_path

        (
            ffmpeg.FFmpeg()
              .option('log_level', 'error')
              .option('y')
              .input(path)
              .output(
                output_path,
                acodec="pcm_s16le",
                ac=1,
                ar="16k"
            )
        ).execute()

        log.info('Done extracting audio!')
        return output_path

    def get_subtitles(self, video_path: str, lang: str) -> str:
        '''
        Input an audio path and output a SRT file containing the subtitles.
        '''
        if not self.isSubtitles() or not hasattr(self, 'whisper'):
            log.warning(f'Failed to get subtitles for {video_path}! Subtitles not enabled.')
            return ''

        # Subtitles depend on just the audio stream, so extract that from the video.
        audio_path = self.get_audio(video_path)
        srt_path = os.path.join('build', f"{self.filename(video_path)}.{lang}.srt")
        log.info(f"Generating subtitles for {srt_path} from {video_path}... This might take a while...")
        if os.path.exists(srt_path):
            if self.isOverwrite():
                log.info(f"Overwriting existing subtitles for \x1b[1m{srt_path}\x1b[0m!")
            else:
                log.info(f"Subtitles already generated for \x1b[1m{srt_path}\x1b[0m!")
                return srt_path
        args = {
            'word_timestamps': True,
            'language': lang,
            'task': os.environ.get('WHISPER_TASK', WhisperTask.TRANSCRIBE),
        }
        #warnings.filterwarnings("ignore")
        if self.whisper is None:
            self.load_whisper()
        transcript, transcriptInfo = self.whisper.transcribe(audio_path, **args) # type: ignore
        #warnings.filterwarnings("default")
        log.debug(transcriptInfo)
        log.info(f"Subtitles generated!")

        self.write_srt(transcript, srt_path)
        return srt_path

    def write_srt(self, transcript: Iterable[Segment], srt_path: str) -> None:
        '''
        Write out the SRT file.
        '''
        log.info('Writing out SRT file...')
        self._subs = [segment for segment in transcript]
        now = time.time()
        i = 1
        srt_tpl = '%d\n%s --> %s\n%s\n\n'
        with io.open(srt_path, "w", encoding="utf-8") as srt:
            for segment in transcript:
                #log.debug(segment)
                buffer = []
                log.info(f"{i}[{segment.start} --> {segment.end}]: {segment.text}")
                while segment.words:
                    word = segment.words.pop(0)
                    buffer.append(word)
                    text = ''.join([ x.word for x in buffer ]).strip().replace('-->', '->')
                    charlen = len(text)
                    stime = format_timestamp(buffer[0].start, always_include_hours=True)
                    etime = format_timestamp(buffer[-1].end, always_include_hours=True)
                    if ( len(buffer) > 6 or charlen > 32 ) and not len(segment.words) == 1:
                        srt.write( srt_tpl % ( i, stime, etime, text ) )
                        i += 1
                        buffer = []
                if len(buffer) > 0:
                    srt.write( srt_tpl % ( i, stime, etime, text ) )
                    i += 1
            srt.flush()
        then = time.time()
        log.info(f'Done writing SRT file in \x1b[4m{round(then-now, 4)}\x1b[0m seconds!')
