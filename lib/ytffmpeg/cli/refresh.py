'''
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
import ffmpeg
import re
from multiprocessing import Process, Queue
from glob import glob

from kizano.utils import write_yaml
from kizano import getLogger
from langchain_core.messages import HumanMessage, SystemMessage
log = getLogger(__name__)

from .base import BaseCommand

GENERATE_TITLE_PROMPT = '''
Based on the subtitles provided, summarize the post in a 1-3 word summary that would be engaging for a TikTok user.
No markdown or extra formatting accepted.
Just the 1 to 3 word summary.
'''

GENERATE_DESCRIPTION_PROMPT = '''
Based on the subtitles provided, provide an engaging summary for the user to view when they click on the video description in TikTok.
Markdown is not allowed in TikTok descriptions.
'''

class RefreshCommand(BaseCommand):
    '''
    Refresh command operations in object form so we have places to store program configuration.
    '''

    def mp4tompv(self, resource: str, q: Queue) -> str:
        '''
        Convert an MP4 file to MKV.
        '''
        if self.config['ytffmpeg'].get('no_convert', False) == True:
            log.info('NOT converting due to user direction.')
            return resource
        log.debug(f'Converting {resource} to mkv.')
        mkvfile = resource.replace('.mp4', '.mkv')
        if os.path.exists(mkvfile):
            if self.isOverwrite():
                log.info(f'Overwriting existing {mkvfile}!')
            else:
                log.info(f'{mkvfile} already exists!')
                q.put(mkvfile)
                return mkvfile
        out_opts = {
            'f': 'matroska',
            'vcodec': 'libx264',
            'acodec': 'ac3',
            'crf': 28,
            'map_metadata': '-1',
            'metadata:s:v': 'language=eng',
            'metadata:s:a': 'language=eng',
        }
        (
            ffmpeg.FFmpeg()
              .option('hide_banner')
              .option('y')
              .input(resource)
              .output(mkvfile, **out_opts)
        ).execute()
        if self.config['ytffmpeg'].get('delete_mp4', False):
            log.debug(f'Deleting {resource} to save on disk space.')
            os.unlink(resource)
        q.put(mkvfile)
        return mkvfile

    def getVideoDuration(self, resource: str) -> float:
        '''
        Get the duration of a video file in seconds.
        '''
        # This ffprobe will output the number of seconds in the video.
        probe_stream = (
            ffmpeg.FFmpeg(executable="ffprobe")
            .option('v', 'quiet')
            .option('show_entries', 'format=duration')
            .option('of', 'csv=p=0')
            .input(resource)
        )

        return float(probe_stream.execute().decode('utf-8').strip())

    def detectSilence(self, resource: str) -> list[str]:
        '''
        Detect silence in a video file and return filter_complex strings to remove silent segments.
        '''
        if not self.shouldCutSilence():
            log.debug('Silence detection disabled in configuration.')
            return []

        log.info(f'Detecting silence in \x1b[1m{resource}\x1b[0m...')

        # Use FFmpeg silencedetect filter to find silent segments
        silence_output = []
        silence_threshold = self.config['ytffmpeg'].get('silence_threshold', 30)
        silence_duration = self.config['ytffmpeg'].get('silence_duration', 1.0)
        log.debug(f'Using silence threshold: -{silence_threshold}dB, duration: {silence_duration}s')

        try:
            out_args = {
                'vn': None,
                'f': 'null',
                'af': f'silencedetect=noise=-{silence_threshold}dB:d={silence_duration}',
            }
            stream = (
                ffmpeg.FFmpeg()
                .option('hide_banner')
                .input(resource)
                .output('-', **out_args)
            )

            @stream.on('stderr')
            def on_stderr(line):
                silence_output.append(line)

            stream.execute()
            output = '\n'.join(silence_output)
        except Exception as e:
            log.error(f'Error running silence detection: {e}')
            return []

        # Parse silence detection output
        silence_start_pattern = r'silence_start: ([\d.]+)'
        silence_end_pattern = r'silence_end: ([\d.]+)'

        silence_starts = [float(match) for match in re.findall(silence_start_pattern, output)]
        silence_ends = [float(match) for match in re.findall(silence_end_pattern, output)]

        if not silence_starts or not silence_ends:
            log.info('No significant silence detected.')
            return []

        # Get padding value in seconds (from milliseconds)
        silence_pad_ms = self.config['ytffmpeg'].get('silence_pad', 350)
        silence_pad = silence_pad_ms / 1000.0  # Convert ms to seconds
        log.debug(f'Using silence padding: {silence_pad}s ({silence_pad_ms}ms)')

        # Create segments to keep (non-silent parts)
        segments = []
        current_time = 0.0
        total_duration = self.getVideoDuration(resource)
        log.debug(f'Total video duration: {total_duration}')

        for i, start in enumerate(silence_starts):
            # Add segment before silence, extending into the silence by the padding amount
            if start > current_time:
                segment_start = current_time
                segment_end = min(start + silence_pad, total_duration)
                segments.append((segment_start, segment_end))

            # Update current time to end of silence (if available), backing up by padding amount
            if i < len(silence_ends):
                current_time = max(0.0, silence_ends[i] - silence_pad)

        # Add final segment if there's content after the last silence
        if current_time < total_duration:
            segments.append((current_time, total_duration))

        if not segments:
            log.info('No segments to keep after silence removal.')
            return []

        log.info(f'Found {len(segments)} segments to keep after removing silence.')
        log.debug(f'Segments: {segments}')

        # Generate filter_complex strings for trimming and concatenating segments
        trim_filters = []
        for i, (start, end) in enumerate(segments):
            trim_filters.append(f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,setsar=1:1[v{i}]")
            trim_filters.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]")

        # Create concat filter for video and audio
        if len(segments) > 1:
            video_inputs = ''.join([f'[v{i}]' for i in range(len(segments))])
            audio_inputs = ''.join([f'[a{i}]' for i in range(len(segments))])
            concat_filter = f"{video_inputs}concat=n={len(segments)}:v=1:a=0,setsar=1:1[trimmed_video];{audio_inputs}concat=n={len(segments)}:v=0:a=1[trimmed_audio]"
            trim_filters.append(concat_filter)
        else:
            # Single segment, just rename outputs
            trim_filters.append("[v0]null[trimmed_video]")
            trim_filters.append("[a0]anull[trimmed_audio]")

        return trim_filters

    def removeSilence(self, resource: str) -> str:
        '''
        Process a video to remove silent segments and output to build/ directory.
        If the input is MP4, also handles conversion to MKV with CRF 28.
        Returns the path to the trimmed video.
        '''
        if not self.shouldCutSilence():
            log.debug('Silence removal not enabled.')
            return resource

        # Get silence filters
        silence_filters = self.detectSilence(resource)
        if not silence_filters:
            log.info('No silence detected, using original video.')
            return resource

        # Create output path in build/
        output_path = f'build/{self.filename(resource)}.mkv'

        if os.path.exists(output_path):
            if self.isOverwrite():
                log.info(f'Overwriting existing \x1b[1m{output_path}\x1b[0m!')
            else:
                log.info(f'\x1b[1m{output_path}\x1b[0m already exists! Skipping silence removal.')
                return output_path

        log.info(f'Processing silence removal for \x1b[1m{resource}\x1b[0m...')

        # Build filter_complex string for ffmpeg
        filter_complex_str = ';'.join(silence_filters)

        try:
            # Create ffmpeg stream with silence removal
            # This also handles MP4→MKV conversion if needed
            out_opts = {
                'filter_complex': filter_complex_str,
                'map': ['[trimmed_video]', '[trimmed_audio]'],
                'vcodec': 'libx264',
                'acodec': 'ac3',
                'crf': 28,
                'f': 'matroska',
                'map_metadata': '-1',
                'metadata:s:v': 'language=eng',
                'metadata:s:a': 'language=eng',
            }
            stream = (
                ffmpeg.FFmpeg()
                .option('hide_banner')
                .option('y')
                .input(resource)
                .output(
                    output_path,
                    **out_opts
                )
            )

            stream.execute()
            log.info(f'Successfully created silence-trimmed video at \x1b[1m{output_path}\x1b[0m!')

            # If original was MP4 and delete_mp4 is enabled, delete it
            if resource.endswith('.mp4') and self.config['ytffmpeg'].get('delete_mp4', False):
                log.debug(f'Deleting {resource} to save on disk space.')
                os.unlink(resource)

            return output_path

        except Exception as e:
            log.error(f'Error processing silence removal: {e}')
            log.warning('Using original video instead.')
            return resource

    def getVideoRotation(self, resource: str) -> int:
        '''
        Detect video rotation from display matrix metadata using ffprobe.
        Returns the rotation angle in degrees (0, 90, 180, 270).
        '''
        log.info(f'Detecting rotation for {resource}...')
        try:
            rotation_output = []

            # Use ffprobe to get rotation metadata
            probe_stream = (
                ffmpeg.FFmpeg(executable="ffprobe")
                .option('v', 'quiet')
                .option('show_entries', 'stream_tags=rotate:stream_side_data=rotation')
                .option('of', 'csv=p=0')
                .input(resource)
            )

            rotation_output = probe_stream.execute().decode('utf-8')

            # Parse rotation value
            if rotation_output:
                rotation = int(rotation_output.strip().strip(','))
                log.info(f'Detected rotation: {rotation} degrees for {resource}')
                return rotation
            log.debug(f'No rotation metadata found for {resource}')
            return 0

        except Exception as e:
            log.warning(f'Could not detect rotation for {resource}: {e}')
            return 0

    def appendVideo(self, resource: str) -> None:
        '''
        Append a video to the ytffmpeg.yml configuration.
        If title or description are empty in the config defaults, they will be auto-generated from subtitles.
        '''
        if self.has_video(resource):
            log.info(f'\x1b[1m{resource}\x1b[0m is already in the ytffmpeg.yml configuration.')
            return
        log.info(f'Appending \x1b[1m{resource}\x1b[0m to ytffmpeg.yml configuration.')
        srt = f'build/{self.filename(resource)}.{self.language()}.srt'
        new_vid_tpl = copy.deepcopy(self.config['ytffmpeg']['defaults'])
        new_vid_tpl.update({
            'input': [
                { 'i': resource },
            ],
            'output': f'build/{self.filename(resource)}.mp4',
        })

        # Check if title is empty in config and generate if needed
        current_title = new_vid_tpl['metadata'].get('title', '')
        if not current_title:
            log.info('Title is empty in config, generating from subtitles...')
            generated_title = self.generateTitle(resource)
            if generated_title:
                new_vid_tpl['metadata']['title'] = generated_title
                log.info(f'Generated title: {generated_title}')
            else:
                log.warning('Failed to generate title, using empty string.')
                new_vid_tpl['metadata']['title'] = ''

        # Check if description is empty in config and generate if needed
        current_description = new_vid_tpl['metadata'].get('description', '')
        if not current_description:
            log.info('Description is empty in config, generating from subtitles...')
            generated_description = self.generateDescription(resource)
            if generated_description:
                new_vid_tpl['metadata']['description'] = generated_description
                log.info(f'Generated description: {generated_description}')
            else:
                log.warning('Failed to generate description, using empty string.')
                new_vid_tpl['metadata']['description'] = ''

        if self.isSubtitles():
            new_vid_tpl['languages'] = ['en:0']
            new_vid_tpl['attributes'] = [ 'subs' ]
            new_vid_tpl['map'] = { 'en': '1:s' }
            new_vid_tpl['input'].append({ 'i': srt })

        # Detect video rotation from display matrix metadata
        rotation = self.getVideoRotation(resource)

        # Build video filter chain with rotation handling
        video_filters = []

        # Add transpose filter based on rotation
        if rotation == 90:
            log.info('Adding transpose=1 for 90° rotation')
            video_filters.append('transpose=1')  # 90 degrees clockwise
        elif rotation == 180:
            log.info('Adding transpose=2,transpose=2 for 180° rotation')
            video_filters.append('transpose=2,transpose=2')  # 180 degrees
        elif rotation == 270:
            log.info('Adding transpose=2 for 270° rotation')
            video_filters.append('transpose=2')  # 90 degrees counter-clockwise
        if rotation and rotation != 0:
            video_filters.append('sidedata=mode=delete')

        # Add scale and setsar
        video_filters.append('scale=720x1280')
        video_filters.append('setsar=1:1')

        # Add subtitles if enabled
        if self.isSubtitles():
            video_filters.append(f"subtitles={srt}:force_style='Alignment=0,PrimaryColour=&H00FFFFFF,FontName=Impact,OutlineColour=&H40000000,BorderStyle=3,Fontsize=10,MarginV=20'")

        # Build filter_complex with standard processing
        video_filter_str = ','.join(video_filters)
        filter_complex = [
            f"[0:v]{video_filter_str}[video]",
            # f"[0:a]volume=1.5,afftdn=nr=10:nf=-20:tn=1,equalizer=f=623:w=3.5:t=h:g=-15:n=1,asetpts=NB_CONSUMED_SAMPLES/SR/TB[audio]"
            f"[0:a]volume=1.5,asetpts=PTS-STARTPTS[audio]"
        ]

        new_vid_tpl['filter_complex'] = filter_complex
        self.config['videos'].append(new_vid_tpl)
        log.info('Done appending video to ytffmpeg.yml configuration!')

    def processSubtitles(self, resource: str) -> None:
        '''
        Do the needful with the subtitles.
        '''
        srt_en = f'build/{self.filename(resource)}.en.srt'
        if self.has_video(resource):
            vid_config = self.get_video_config(resource)
        else:
            vid_config = copy.deepcopy(self.config['ytffmpeg']['defaults'])
            vid_config['attributes'] = [ 'subs' ]
            vid_config['languages'] = ['en:0']
            vid_config['map'] = { 'en': '1:s' }
            if 'input' not in vid_config:
                vid_config['input'] = []
            vid_config['input'].append({ 'i': srt_en })
        if 'attributes' in vid_config and 'subs' in vid_config['attributes']:
            if 'languages' in vid_config:
                log.info(f'Multilang video found at \x1b[1m{resource}\x1b[0m')
                for ilang in vid_config['languages']:
                    lang = ilang.split(':').pop(0)
                    log.info(f'Processing subtitles for \x1b[1m{resource}\x1b[0m in \x1b[1m{lang}\x1b[0m')
                    self.get_subtitles(resource, lang)
            else:
                self.get_subtitles(resource, self.language())
        else:
            log.info(f'Subs not enabled for \x1b[1m{resource}\x1b[0m')

    def generateTitle(self, resource: str) -> str:
        '''
        Generate a title for a video based on the subtitles.
        Reads the text transcript file for the resource and sends its content to the LLM.
        '''
        txt_path = f'build/{self.filename(resource)}.txt'

        if not os.path.exists(txt_path):
            log.warning(f'Transcript file {txt_path} not found. Cannot generate title.')
            return ''

        log.info(f'Generating title for \x1b[1m{resource}\x1b[0m from transcript at {txt_path}')

        # Read the transcript file content
        subtitle_content = open(txt_path, 'r', encoding='utf-8').read()

        messages = []
        messages.append(SystemMessage(content=GENERATE_TITLE_PROMPT))
        messages.append(HumanMessage(content=subtitle_content))
        response = self.llm.invoke(messages)
        return response.content.strip()

    def generateDescription(self, resource: str) -> str:
        '''
        Generate a description for a video based on the subtitles.
        Reads the text transcript file for the resource and sends its content to the LLM.
        '''
        txt_path = f'build/{self.filename(resource)}.txt'

        if not os.path.exists(txt_path):
            log.warning(f'Transcript file {txt_path} not found. Cannot generate description.')
            return ''

        log.info(f'Generating description for \x1b[1m{resource}\x1b[0m from transcript at {txt_path}')

        # Read the transcript file content
        subtitle_content = open(txt_path, 'r', encoding='utf-8').read()

        messages = []
        messages.append(SystemMessage(content=GENERATE_DESCRIPTION_PROMPT))
        messages.append(HumanMessage(content=subtitle_content))
        response = self.llm.invoke(messages)
        return response.content.strip()

    def save(self) -> None:
        '''
        Write ytffmpeg.yml updates to disk.
        '''
        log.info('Writing out ytffmpeg.yml configuration...')
        write_yaml('ytffmpeg.yml', { 'videos': self.config['videos'] })
        log.info('Done writing out ytffmpeg.yml configuration!')

    def execute(self) -> int:
        '''
        Entrypoint for execution
        '''
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
                    if self.isSubtitles():
                        self.processSubtitles(processed_resource)
                    self.appendVideo(processed_resource)
                else:
                    # Standard flow: convert MP4→MKV first, then process
                    log.info('No silence detection enabled, converting MP4→MKV...')
                    q = Queue()
                    conversion = Process(target=self.mp4tompv, args=(resource, q))
                    conversion.start()
                    conversion.join()

                    while q.empty() is False:
                        converted_resource = q.get()
                        # Generate subtitles from the converted video
                        if self.isSubtitles():
                            self.processSubtitles(converted_resource)
                        self.appendVideo(converted_resource)

                log.info(f'Done processing \x1b[1m{resource}\x1b[0m!')
            elif resource.endswith('.mkv'):
                log.info(f'Processing {resource}...')
                # Apply silence removal if enabled
                processed_resource = self.removeSilence(resource)
                # Generate subtitles from the final video (trimmed or original)
                if self.isSubtitles():
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
    cmd = RefreshCommand(config)
    return cmd.execute()
