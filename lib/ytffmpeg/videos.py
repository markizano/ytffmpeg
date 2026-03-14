'''
Video processing functions.
Input a path to a video, perform some operation on it, output the updated/transmuted video.
Some functions take a video path to inspect and output a filter complex to execute against it.
'''
import os
import re
import ffmpeg
from multiprocessing import Queue
from ytffmpeg import getLogger, utils, subtitles
log = getLogger(__name__)

def mp4tomkv(resource: str, q: Queue, overwrite: bool = False, delete_mp4: bool = False) -> str:
    '''
    Convert an MP4 file to MKV.
    Strip metadata and video sidedata.
    Compress using crf=28.
    Meant to be executed as a `multiprocessing.Process()`
    '''
    log.info(f'Converting {resource} to mkv.')
    mkvfile = resource.replace('.mp4', '.mkv')
    if os.path.exists(mkvfile):
        if overwrite:
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
    if delete_mp4:
        log.debug(f'Deleting {resource} to save on disk space.')
        os.unlink(resource)
    q.put(mkvfile)
    return mkvfile

def getVideoDuration(resource: str) -> float:
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

def detectSilence(
    resource: str,
    silence_threshold: int = 30,
    silence_duration: float = 1.2,
    silence_pad_ms: int = 350,
) -> list[str]:
    '''
    Detect silence in a video file and return filter_complex strings to remove silent segments.
    Params:

        resource: The video file in question to detect silence. Usually out of the `resources/`
            folder.
        silence_threshold: What sound level in dB to count as "silence"
        silence_duration: How long in seconds should we count said silence to be clipped.
        silence_pad: Silence stripping can be agressive. Pad/restore the before & after silence by
            this many miliseconds of video to make the clips seem more natural/clean.

    Returns: List of filter complex strings representing silence removal
    '''
    log.info(f'Detecting silence in \x1b[1m{resource}\x1b[0m...')

    # Use FFmpeg silencedetect filter to find silent segments
    silence_output = []
    log.info(f'Using silence threshold: -{silence_threshold}dB, duration: {silence_duration}s')

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

    silence_starts = [round(float(match), 3) for match in re.findall(silence_start_pattern, output)]
    silence_ends = [round(float(match), 3) for match in re.findall(silence_end_pattern, output)]

    if not silence_starts or not silence_ends:
        log.info('No significant silence detected.')
        return []

    # Get padding value in seconds (from milliseconds)
    silence_pad = silence_pad_ms / 1000.0  # Convert ms to seconds
    log.info(f'Using silence padding: {silence_pad}s ({silence_pad_ms}ms)')

    # Create segments to keep (non-silent parts)
    segments = []
    current_time = 0.0
    total_duration = getVideoDuration(resource)
    log.info(f'Total video duration: {total_duration}')

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

def removeSilence(
    resource: str,
    overwrite: bool = False,
    delete_mp4: bool = False,
    silence_threshold: int = 30,
    silence_duration: float = 1.2,
    silence_pad_ms: int = 350,
) -> str:
    '''
    Process a video to remove silent segments and output to build/ directory.
    If the input is MP4, also handles conversion to MKV with CRF 28.
    Returns the path to the trimmed video.
    '''
    # Get silence filters
    silence_filters = detectSilence(resource, silence_threshold, silence_duration, silence_pad_ms)
    if not silence_filters:
        log.info('No silence detected, using original video.')
        return resource

    # Create output path in build/
    output_path = f'build/{utils.filename(resource)}.mkv'

    if os.path.exists(output_path):
        if overwrite:
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
            .option('noautorotate')
            .input(resource)
            .output(
                output_path,
                **out_opts
            )
        )

        stream.execute()
        log.info(f'Successfully created silence-trimmed video at \x1b[1m{output_path}\x1b[0m!')

        # If original was MP4 and delete_mp4 is enabled, delete it
        if resource.endswith('.mp4') and delete_mp4:
            log.debug(f'Deleting {resource} to save on disk space.')
            os.unlink(resource)

        return output_path

    except Exception as e:
        log.error(f'Error processing silence removal: {e}')
        log.warning('Using original video instead.')
        return resource

def getVideoRotation(resource: str) -> int:
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

def appendVideo(videos: list[dict], resource: str) -> list[dict]:
    '''
    Append a video to the ytffmpeg.yml configuration.
    If title or description are empty in the config defaults, they will be auto-generated from
    subtitles.

    Params:

        videos: The {'videos': []} array from `ytffmpeg.yml`.
        resource: The video from the `resources/` directory.

    Returns: The updated video configuration with the appended video in the config.
    '''
    if utils.hasVideo(videos, resource):
        log.info(f'\x1b[1m{resource}\x1b[0m is already in the ytffmpeg.yml configuration.')
        return
    log.info(f'Appending \x1b[1m{resource}\x1b[0m to ytffmpeg.yml configuration.')
    srt = f'build/{utils.filename(resource)}.en.srt'
    new_vid_tpl = {
        'input': [
            { 'i': resource },
        ],
        'output': f'build/{utils.filename(resource)}.mp4',
        'metadata': {
            'title': '',
            'description': '',
        }
    }

    # Detect video rotation from display matrix metadata
    rotation = getVideoRotation(resource)

    #@TODO Circle back on this. This seems like it should be its own operation.
    # # Check if title is empty in config and generate if needed
    # current_title = new_vid_tpl['metadata'].get('title', '')
    # if not current_title:
    #     log.info('Title is empty in config, generating from subtitles...')
    #     generated_title = subtitles.generateTitle(resource)
    #     if generated_title:
    #         new_vid_tpl['metadata']['title'] = generated_title
    #         log.info(f'Generated title: {generated_title}')
    #     else:
    #         log.warning('Failed to generate title, using empty string.')
    #         new_vid_tpl['metadata']['title'] = ''

    # # Check if description is empty in config and generate if needed
    # current_description = new_vid_tpl['metadata'].get('description', '')
    # if not current_description:
    #     log.info('Description is empty in config, generating from subtitles...')
    #     generated_description = subtitles.generateDescription(resource)
    #     if generated_description:
    #         new_vid_tpl['metadata']['description'] = generated_description
    #         log.info(f'Generated description: {generated_description}')
    #     else:
    #         log.warning('Failed to generate description, using empty string.')
    #         new_vid_tpl['metadata']['description'] = ''

    if self.isSubtitles():
        # Detect all available subtitle files for this resource
        base_filename = utils.filename(resource)
        available_subs = []

        # Check for subtitle files in build directory
        from glob import glob as file_glob
        srt_pattern = f'build/{base_filename}.*.srt'
        srt_files = file_glob(srt_pattern)

        # Extract language codes from subtitle files
        for srt_file in srt_files:
            # Extract language code from filename (e.g., "web-4.0.en.srt" -> "en")
            parts = os.path.basename(srt_file).split('.')
            if len(parts) >= 3 and parts[-1] == 'srt':
                lang_code = parts[-2]
                available_subs.append((lang_code, srt_file))

        if not available_subs:
            # Fallback to single English subtitle
            new_vid_tpl['languages'] = ['en:0']
            new_vid_tpl['attributes'] = [ 'subs' ]
            new_vid_tpl['map'] = { 'en': '1:s' }
            new_vid_tpl['input'].append({ 'i': srt })
        else:
            # Multi-language setup
            new_vid_tpl['attributes'] = [ 'subs' ]
            new_vid_tpl['languages'] = []
            new_vid_tpl['map'] = {}

            # Sort by language code for consistent ordering
            available_subs.sort(key=lambda x: x[0])

            for idx, (lang_code, srt_file) in enumerate(available_subs):
                new_vid_tpl['input'].append({ 'i': srt_file })
                # Stream index starts at 1 (0 is the video)
                stream_idx = idx + 1
                new_vid_tpl['languages'].append(f'{lang_code}:{idx}')
                new_vid_tpl['map'][lang_code] = f'{stream_idx}:s'

            log.info(f'Configured {len(available_subs)} subtitle tracks: {[lang for lang, _ in available_subs]}')

    # Build video filter chain with rotation handling
    video_filters = []

    # Add transpose filter based on rotation
    # 90 deg clockwise: -180; 90 deg counter-cw: 0; portrait: 90; upside-down: -90
    if rotation == 90:
        log.info('Adding transpose=2 for 90° rotation')
        video_filters.append('transpose=2')  # 90 degrees clockwise
    elif rotation == -90:
        log.info('Adding transpose=1 for 180° rotation')
        video_filters.append('transpose=1')  # 90 degrees counter-clockwise/upside down
    if rotation and rotation != 0:
        video_filters.append('sidedata=mode=delete')

    # Add scale and setsar
    # @markizano: Removed since 1080p is now OK. May delete these lines at some point.
    # video_filters.append('scale=720x1280')
    # video_filters.append('setsar=1:1')

    # Add subtitles if enabled
    if self.isSubtitles():
        # @TODO: Detect when split screen OBS view and change font settings.
        font_style = ','.join([
            'Alignment=0',
            'PrimaryColour=&H00FFFFFF',
            'FontName=Impact',
            'OutlineColour=&H40000000',
            'BorderStyle=3',
            'Fontsize=14',
            'MarginV=60',
            'MarginL=30'
        ])
        video_filters.append(f"subtitles={srt}:force_style='{font_style}'")

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
