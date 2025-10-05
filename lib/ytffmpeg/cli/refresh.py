'''
This module will check the resources directory for any mis-matched media, convert it,
auto-generate subtitles for it using the `whisper` script directly, and optionally
detect and remove silent segments if configured to do so.
'''

import os
import copy
import ffmpeg
import re
from multiprocessing import Process, Queue
from glob import glob

from kizano.utils import write_yaml
from kizano import getLogger
log = getLogger(__name__)

from .base import BaseCommand
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
            'metadata:s:a': 'language=eng'
        }
        (
            ffmpeg.FFmpeg()
              .option('hide_banner')
              .input(resource)
              .output(mkvfile, **out_opts)
        ).execute()
        if self.config['ytffmpeg'].get('delete_mp4', False):
            log.debug(f'Deleting {resource} to save on disk space.')
            os.unlink(resource)
        q.put(mkvfile)
        return mkvfile

    def detect_silence(self, resource: str) -> list[str]:
        '''
        Detect silence in a video file and return filter_complex strings to remove silent segments.
        '''
        if not self.config['ytffmpeg'].get('cut_silence', False):
            log.debug('Silence detection disabled in configuration.')
            return []

        log.info(f'Detecting silence in \x1b[1m{resource}\x1b[0m...')

        # Use FFmpeg silencedetect filter to find silent segments
        silence_output = []

        try:
            stream = (
                ffmpeg.FFmpeg()
                .option('hide_banner')
                .input(resource)
                .output('-', vn=None, f='null', af='silencedetect=noise=-30dB:d=1')
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

        # Create segments to keep (non-silent parts)
        segments = []
        current_time = 0.0

        for i, start in enumerate(silence_starts):
            # Add segment before silence
            if start > current_time:
                segments.append((current_time, start))

            # Update current time to end of silence (if available)
            if i < len(silence_ends):
                current_time = silence_ends[i]

        # Add final segment if there's content after the last silence
        if silence_ends and current_time < silence_ends[-1]:
            # Get video duration to determine final segment
            try:
                duration_output = []

                # This ffprobe will output the number of seconds in the video.
                probe_stream = (
                    ffmpeg.FFmpeg(executable="ffprobe")
                    .option('v', 'quiet')
                    .option('show_entries', 'format=duration')
                    .option('of', 'csv=p=0')
                    .input(resource)
                )

                @probe_stream.on('stdout')
                def on_stdout(line):
                    duration_output.append(line.strip())

                probe_stream.execute()
                total_duration = float(duration_output[0]) if duration_output else 0
                if current_time < total_duration:
                    segments.append((current_time, total_duration))
            except:
                log.warning('Could not determine video duration for final segment.')

        if not segments:
            log.info('No segments to keep after silence removal.')
            return []

        log.info(f'Found {len(segments)} segments to keep after removing silence.')

        # Generate filter_complex strings for trimming and concatenating segments
        trim_filters = []
        for i, (start, end) in enumerate(segments):
            trim_filters.append(f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}]")
            trim_filters.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]")

        # Create concat filter for video and audio
        if len(segments) > 1:
            video_inputs = ''.join([f'[v{i}]' for i in range(len(segments))])
            audio_inputs = ''.join([f'[a{i}]' for i in range(len(segments))])
            concat_filter = f"{video_inputs}concat=n={len(segments)}:v=1:a=0[trimmed_video];{audio_inputs}concat=n={len(segments)}:v=0:a=1[trimmed_audio]"
            trim_filters.append(concat_filter)
        else:
            # Single segment, just rename outputs
            trim_filters.append("[v0]null[trimmed_video]")
            trim_filters.append("[a0]anull[trimmed_audio]")

        return trim_filters

    def append_video(self, resource: str) -> None:
        '''
        Append a video to the ytffmpeg.yml configuration.
        '''
        if self.has_video(resource):
            log.info(f'\x1b[1m{resource}\x1b[0m is already in the ytffmpeg.yml configuration.')
            return
        log.info(f'Appending \x1b[1m{resource}\x1b[0m to ytffmpeg.yml configuration.')
        lang = self.config.language or 'en'
        srt = f'build/{self.filename(resource)}.{lang}.srt'
        new_vid_tpl = copy.deepcopy(self.config['ytffmpeg']['defaults'])
        new_vid_tpl.update({
            'input': [
                { 'i': resource },
            ],
            'output': f'build/{self.filename(resource)}.mp4' if not self.isSilenceDetector() else f'resources/{self.filename(resource)}_trimmed.mp4',
        })
        new_vid_tpl['metadata']['title'] = new_vid_tpl['metadata']['description'] = ''

        if self.isSubtitles():
            new_vid_tpl['languages'] = ['en:0']
            new_vid_tpl['attributes'] = [ 'subs' ]
            new_vid_tpl['map'] = { 'en': '1:s' }
            new_vid_tpl['input'].append({ 'i': srt })

        # Build filter_complex - check if silence detection is enabled
        filter_complex = []

        # Check if silence detection is enabled and get filters
        if self.isSilenceDetector():
            silence_filters = self.detect_silence(resource)
            if silence_filters:
                # Add silence detection filters first
                filter_complex.extend(silence_filters)
                # Use trimmed outputs as input for subsequent filters
                video_input = "[trimmed_video]"
                audio_input = "[trimmed_audio]"
            else:
                # Use original inputs if no silence detected
                video_input = "[0:v]"
                audio_input = "[0:a]"
        else:
            # Use original inputs when silence detection is disabled
            video_input = "[0:v]"
            audio_input = "[0:a]"

        # Add the existing video and audio processing filters
        filter_complex.extend([
            f"{video_input}scale=720x1280,setsar=1:1,subtitles={srt}:force_style='Alignment=0,PrimaryColour=&H00FFFFFF,FontName=Impact,OutlineColour=&H40000000,BorderStyle=3,Fontsize=10,MarginV=20'[video]",
            f"{audio_input}volume=1.5,afftdn=nr=10:nf=-20:tn=1,equalizer=f=623:w=3.5:t=h:g=-15:n=1,asetpts=NB_CONSUMED_SAMPLES/SR/TB[audio]"
        ])

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
            vid_config['input'].append({ 'i': srt_en })
        if 'attributes' in vid_config and 'subs' in vid_config['attributes']:
            if 'languages' in vid_config:
                log.info(f'Multilang video found at \x1b[1m{resource}\x1b[0m')
                for ilang in vid_config['languages']:
                    lang = ilang.split(':').pop(0)
                    log.info(f'Processing subtitles for \x1b[1m{resource}\x1b[0m in \x1b[1m{lang}\x1b[0m')
                    self.get_subtitles(resource, lang)
            else:
                self.get_subtitles(resource, self.language)
        else:
            log.info(f'Subs not enabled for \x1b[1m{resource}\x1b[0m')


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
        self.language = self.config['ytffmpeg'].get('language', os.environ.get('LANGUAGE', 'en'))
        for resource in resources:
            if resource.endswith('.mp4'):
                log.info(f'Processing {resource}...')
                # Start the mpv conversion in a subprocess.
                q = Queue()
                conversion = Process(target=self.mp4tompv, args=(resource, q))
                conversion.start()
                if self.isSubtitles():
                    self.processSubtitles(resource)
                conversion.join()
                while q.empty() is False:
                    self.append_video(q.get())
                log.info(f'Done processing \x1b[1m{resource}\x1b[0m!')
            elif resource.endswith('.mkv'):
                log.info(f'Processing {resource}...')
                if self.isSubtitles():
                    self.processSubtitles(resource)
                self.append_video(resource)
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
    Check to see if any media in `./resources` needs subtitles generated.
    Detect and remove silent segments if `.ytffmpeg.cut_silence` is enabled.

    If it's in MP4 format, it will need both subtitles and MKV conversion.
    When converting from MP4 to MKV format, the previous metadata is removed, then the following
    metadata is attached to both the audio and the video streams separately: language=eng.
    The video codec is converted to libx264 and the audio codec is converted to ac3.
    The CRF is turned up to 28.
    The resulting MP4 file is then deleted if `.ytffmpeg.delete_mp4` is set to `True`.

    If `.ytffmpeg.cut_silence` is set to `True`, the tool will detect silent segments
    (using -30dB threshold with 1 second minimum duration) and automatically generate
    filter_complex strings to remove those segments during the build process.
    '''
    log.info('Refreshing resources directory.')
    cmd = RefreshCommand(config)
    return cmd.execute()
