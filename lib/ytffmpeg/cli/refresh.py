'''

No more refresh... This is changing.

Operations include:
* mp4tomkv: Convert and compress video.
* cut-silence: Strip the video of pauses in audio.
* gensubs: Generate subtitles for video.
* metadata: Generate metadata (title and description).
* amend: Add this video to the `ytffmpeg.yml` config for compilation.



This module will check the resources directory for any mis-matched media, convert it,
optionally detect and remove silent segments if configured to do so, and then
auto-generate subtitles from the final processed video using the `whisper` script directly.

Critical: When silence detection is enabled, MP4→MKV conversion and silence removal happen
in one step, and subtitles are generated from the trimmed video to ensure timing accuracy.

Video Rotation Detection:
  - Automatically detects display matrix metadata to determine video rotation
  - Applies appropriate transpose filter (transpose=1 for 90°, transpose=2 for 270°)
  - Ensures proper orientation before scaling and subtitle application

Silence detection is configurable via:
  --silence-threshold (default: 30dB)
  --silence-duration (default: 1 second)
  --silence-pad (default: 350ms) - padding before/after silence removal
'''

import os
import copy
from multiprocessing import Process, Queue
from glob import glob

from ytffmpeg import getLogger
log = getLogger(__name__)

from ytffmpeg.cli.base import BaseCommand

class RefreshCommand(BaseCommand):
    '''
    Refresh command operations in object form so we have places to store program configuration.
    '''

    def processSubtitles(self, resource: str) -> None:
        '''
        Do the needful with the subtitles.
        Help generate subtitles, if they haven't been done already.
        Attach them to the video config if they haven't already been connected.
        Only do this if subtitles are enabled for this video.

        Multi-language support:
        - Generates English subtitles using Whisper
        - Translates to additional languages using Argos Translate
        - Preserves timing by translating full context then splitting by word count
        - Checks for global 'languages' config to auto-enable translation
        '''
        # Skip if this is totally told to bypass subs.
        if not self.isSubtitles():
            return

        base_lang = self.language()  # Default base language (usually 'en')
        srt_base = f'build/{self.filename(resource)}.{base_lang}.srt'

        if self.has_video(resource):
            vid_config = self.get_video_config(resource)
        else:
            vid_config = copy.deepcopy(self.config['ytffmpeg']['defaults'])
            vid_config['attributes'] = [ 'subs' ]

            # Check for global languages configuration
            global_languages = self.config['ytffmpeg'].get('languages', [])
            if global_languages and isinstance(global_languages, list):
                # Auto-configure multi-language support from global config
                vid_config['languages'] = [f'{lang}:{idx}' for idx, lang in enumerate(global_languages)]
                vid_config['map'] = {lang: f'{idx+1}:s' for idx, lang in enumerate(global_languages)}
                log.info(f'Using global language configuration: {global_languages}')
            else:
                # Default single language
                vid_config['languages'] = [f'{base_lang}:0']
                vid_config['map'] = { base_lang: '1:s' }

            if 'input' not in vid_config:
                vid_config['input'] = []
            vid_config['input'].append({ 'i': srt_base })

        if 'attributes' in vid_config and 'subs' in vid_config['attributes']:
            if 'languages' in vid_config:
                log.info(f'Transcription detected for video found at \x1b[1m{resource}\x1b[0m')

                # Extract all requested languages
                requested_langs = []
                for i, ilang in enumerate(vid_config['languages']):
                    lang = ilang.split(':').pop(0)
                    assert lang != '', f'Language for {resource} index {i} was empty??'
                    requested_langs.append(lang)

                # First, generate base language subtitles using Whisper
                if base_lang in requested_langs:
                    log.info(f'Generating base language ({base_lang}) subtitles with Whisper for \x1b[1m{resource}\x1b[0m')
                    self.get_subtitles(resource, base_lang)
                else:
                    # If base language not in requested languages, generate it anyway for translation
                    log.info(f'Generating {base_lang} subtitles as translation source for \x1b[1m{resource}\x1b[0m')
                    self.get_subtitles(resource, base_lang)

                # Translate to other languages
                for lang in requested_langs:
                    if lang == base_lang:
                        continue  # Already generated

                    target_srt = f'build/{self.filename(resource)}.{lang}.srt'

                    # Check if translation already exists
                    if os.path.exists(target_srt) and not self.isOverwrite():
                        log.info(f'Translated subtitles already exist for \x1b[1m{target_srt}\x1b[0m')
                        continue

                    log.info(f'Translating subtitles from {base_lang} to {lang} for \x1b[1m{resource}\x1b[0m')
                    translated_srt = self.translate_subtitles(srt_base, base_lang, lang)

                    if translated_srt:
                        log.info(f'Successfully created translated subtitles: {translated_srt}')
                    else:
                        log.error(f'Failed to translate subtitles to {lang}')
            else:
                # Single language mode
                self.get_subtitles(resource, base_lang)
        else:
            log.info(f'Subs not enabled for \x1b[1m{resource}\x1b[0m')


    def execute(self) -> int:
        '''
        Entrypoint for execution
        '''
        with self.video_processing_lock('refresh'):
            resources = glob('resources/*')
            log.debug(f'Found resources: {resources}')
            for resource in resources:
                if resource.endswith('.mp4'):
                    log.info(f'Processing {resource}...')

                    # If silence detection is enabled, do MP4→MKV conversion + silence removal in one step
                    if self.shouldCutSilence():
                        log.info('Silence detection enabled, combining conversion and trimming...')
                        processed_resource = self.removeSilence(resource)
                        # Generate subtitles from the trimmed video
                        self.processSubtitles(processed_resource)
                        self.appendVideo(processed_resource)
                    else:
                        # Standard flow: convert MP4→MKV first, then process
                        log.info('No silence detection enabled, converting MP4→MKV...')
                        q = Queue()
                        conversion = Process(target=self.mp4tomkv, args=(resource, q))
                        conversion.start()
                        conversion.join()

                        while q.empty() is False:
                            converted_resource = q.get()
                            # Generate subtitles from the converted video
                            self.processSubtitles(converted_resource)
                            self.appendVideo(converted_resource)

                    log.info(f'Done processing \x1b[1m{resource}\x1b[0m!')
                elif resource.endswith('.mkv'):
                    log.info(f'Processing {resource}...')
                    # Apply silence removal if enabled
                    processed_resource = self.removeSilence(resource)
                    # Generate subtitles from the final video (trimmed or original)
                    self.processSubtitles(processed_resource)
                    self.appendVideo(processed_resource)
                    log.info(f'Done processing \x1b[1m{resource}\x1b[0m!')
                # I don't believe the last suggested else should be here because sometimes
                # PNG files and other non-video items may be included, so we only want to
                # track specified video files.

            log.info('Resources have been processed!')
            self.save()
            log.info('Refresh complete!')
            # Somehow the terminal is getting messed up after this command is run.
            os.system('stty echo -brkint -imaxbel icanon iexten icrnl')
            return 0

def refresher(config: dict) -> int:
    '''
    Update `ytffmpeg.yml` with any new media in `./resources`.
    Check to see if any media in `./resources` needs to be converted to Matroska format.
    Detect and remove silent segments if `.ytffmpeg.cut_silence` is enabled.
    Check to see if any media in `./resources` needs subtitles generated.

    Processing order is critical:
    1. MP4→MKV conversion (with or without silence removal)
    2. Subtitle generation (from the final processed video)
    3. Video configuration appended to ytffmpeg.yml

    If silence detection is enabled (`.ytffmpeg.cut_silence`):
      - MP4 files: Conversion to MKV and silence removal happen in ONE step
      - MKV files: Silence removal is applied directly
      - Output: Trimmed videos saved to build/<filename>.mkv
      - Subtitles are generated from the trimmed video to ensure timing accuracy

    If silence detection is disabled:
      - MP4 files: Standard conversion to MKV format
      - MKV files: Used as-is
      - Subtitles are generated from the converted/original video

    Conversion settings (MP4→MKV):
      - Previous metadata is removed
      - Metadata attached: language=eng (both audio and video streams)
      - Video codec: libx264
      - Audio codec: ac3
      - CRF: 28
      - Resulting MP4 deleted if `.ytffmpeg.delete_mp4` is `True`

    Silence detection settings:
      - Threshold: Configurable via `--silence-threshold` (default: 30dB)
      - Minimum duration: Configurable via `--silence-duration` (default: 1 second)
      - Padding: Configurable via `--silence-pad` (default: 350ms) - adds padding before/after silence
    '''
    log.info('Refreshing resources directory.')
    cmd = RefreshCommand(copy.deepcopy(config))
    return cmd.execute()
