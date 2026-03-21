'''
Video processing functions.
Input a path to a video, perform some operation on it, output the updated/transmuted video.
Some functions take a video path to inspect and output a filter complex to execute against it.
'''
import os
import re
import time
import ffmpeg
import subprocess
from glob import glob
from copy import deepcopy as copy
from ytffmpeg import getLogger, utils
log = getLogger(__name__)

def mp4tomkv(resource: str) -> str:
    '''
    Convert an MP4 file to MKV.
    Strip metadata and video sidedata.
    Compress using crf=28.
    '''
    log.info(f'Converting {resource} to mkv.')
    mkvfile = resource.replace('.mp4', '.mkv')
    out_opts = {
        'vf': 'sidedata=mode=delete',
        'f': 'matroska',
        'c:v': 'libx265',
        'c:a': 'ac3',
        'crf': 28,
        'pix_fmt': 'yuv420p',
        'map_metadata': '-1',
        'metadata:s:a:0': 'language=eng',
    }
    (
        ffmpeg.FFmpeg()
        .option('hide_banner')
        .option('y')
        .input(resource)
        .output(mkvfile, **out_opts)
    ).execute()
    log.debug(f'Deleting {resource} to save on disk space.')
    os.unlink(resource)
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
    trim_filters.extend(utils.mergefilters(segments))
    log.info(f'Done detecting silence for {resource}!')
    return trim_filters

def removeSilence(resource: str, **kwargs) -> str:
    '''
    Process a video to remove silent segments and output to build/ directory.
    If the input is MP4, also handles conversion to MKV with CRF 28.
    Returns the path to the trimmed video.
    '''
    # Get silence filters
    silence_filters = detectSilence(resource, **kwargs)
    if not silence_filters:
        log.info('No silence detected, using original video.')
        return resource

    video_cfg = newVideo(resource)
    updateVideo(video_cfg, filter_complex=silence_filters)
    ytffmpeg_cfg = utils.load()
    ytffmpeg_cfg['videos'].append(video_cfg)
    utils.save(ytffmpeg_cfg)
    log.info(f'Processing silence removal for \x1b[1m{resource}\x1b[0m...')
    cv = compileVideo(video_cfg, **kwargs)
    output_path = video_cfg['output']
    if cv != 0:
        log.warning('compileVideo() at this step did not succeed. This may cause downstream effects from here...')
    else:
        log.info(f'Successfully created silence-trimmed video at \x1b[1m{output_path}\x1b[0m!')
    return output_path

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

def newVideo(resource: str) -> dict:
    '''
    Generate a video config to append to the ytffmpeg.yml configuration.
    If title or description are empty in the config defaults, they will be auto-generated from
    subtitles.

    Returns: The video configuration you can add to `ytffmpeg.yml`.
    '''
    log.info(f'Generating \x1b[1m{resource}\x1b[0m to add to ytffmpeg.yml configuration.')
    return {
        'input': [
            { 'i': resource },
        ],
        'output': f'build/{utils.filename(resource)}.mp4',
        'metadata': {},
        'attributes': [],
    }

def updateVideo(video_cfg: dict, **kwargs) -> dict:
    '''
    Once we have more details about a video, update the data structure accordingly.

    title: str -- Assign the metadata title.
    description: str -- Assign the metadata description.
    subs: dict[str, str] -- key-value mapping of language:filename for subtitles.
    filter_complex: list[str] -- List of strings to use for the filter complex. By default
        include the standard hard-sub filter complex.
    '''

    # If metadata is defined, then assign it where it belongs in the data structure.
    for metadata in ['title', 'description']:
        if metadata in kwargs and kwargs[metadata]:
            video_cfg['metadata'][metadata] = kwargs[metadata]

    if 'attributes' in kwargs and kwargs['attributes']:
        for attribute in kwargs['attributes']:
            if attribute not in video_cfg['attributes']:
                video_cfg['attributes'].append(attribute)

    if 'subs' in kwargs and kwargs['subs']:
        if 'subs' not in video_cfg['attributes']:
            video_cfg['attributes'].append('subs')
        if 'map' not in video_cfg:
            video_cfg['map'] = {}
        if 'languages' not in video_cfg:
            video_cfg['languages'] = []
        for idx, sub in enumerate(kwargs['subs']):
            lang, srtfile = sub
            video_cfg['languages'].append(f'{lang}:{idx}')
            i = len(video_cfg['input'])
            video_cfg['map'][lang] = f'{i}:s'
            video_cfg['input'].append({'i': srtfile})

    if 'filter_complex' in kwargs:
        if kwargs['filter_complex']:
            video_cfg['filter_complex'] = kwargs['filter_complex']
        else:
            # Build video filter chain with rotation handling
            video_filters = []

            # Detect video rotation from display matrix metadata
            rotation = getVideoRotation(video_cfg['input'][0]['i'])

            # Add transpose filter based on rotation BEFORE subtitles.
            # 90 deg clockwise: -180; 90 deg counter-cw: 0; portrait: 90; upside-down: -90
            if rotation == 90:
                log.info('Adding transpose=2 for 90° rotation')
                video_filters.append('transpose=2')  # 90 degrees clockwise
            elif rotation == -90:
                log.info('Adding transpose=1 for 180° rotation')
                video_filters.append('transpose=1')  # 90 degrees counter-clockwise/upside down
            if rotation and rotation != 0:
                video_filters.append('sidedata=mode=delete')

            # Remember: https://www.abyssale.com/blog/how-to-change-the-appearances-of-subtitles-with-ffmpeg
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
            # Get the first SRT file as input.
            srtfile = None
            for inputVid in video_cfg['input']:
                if inputVid['i'].endswith('.srt'):
                    srtfile = inputVid['i']
                    break
            if srtfile == None:
                raise ValueError(f'Input video has no SRT file: {video_cfg}')
            video_filters.append(f"subtitles={srtfile}:force_style='{font_style}'")

            # Build filter_complex with standard processing
            video_filter_str = ','.join(video_filters)
            video_cfg['filter_complex'] = [
                f"[0:v]{video_filter_str}[video]",
                # f"[0:a]volume=1.5,afftdn=nr=10:nf=-20:tn=1,equalizer=f=623:w=3.5:t=h:g=-15:n=1,asetpts=NB_CONSUMED_SAMPLES/SR/TB[audio]"
                f"[0:a]volume=1.5,asetpts=PTS-STARTPTS[audio]"
            ]

    log.info(f'New Video config: {video_cfg}')
    return video_cfg

def inputToArgList(raw_input_video: str|dict):
    '''
    Take the data structure that represents an input and convert into the argument list ffmpeg
    expects.
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

def preProcessResources(ytffmpeg_cfg: dict, **kwargs) -> str:
    '''
    Handle the case of >1 resource.
    When we have >1 resource, need to:
    * mp4-to-mkv
    * cut-silence
    * concat the results.

    Return: Path to post-processed video path.
    '''
    to_concat: list[dict] = []
    for resource in utils.getResources():
        if utils.hasInput(ytffmpeg_cfg['videos']): continue
        mp4tomkv(resource)
        trimmed_video = removeSilence(resource, **kwargs)
        to_concat.append({'i': trimmed_video})
    # Once we are done iterating videos that need compress & cut, combine them.
    concat_filter_complex = utils.mergefilters(to_concat)
    outfile = f'resources/{ytffmpeg_cfg["name"]}.mkv'
    if os.path.exists(outfile):
        log.warning(f'The {outfile} exists, writing to `resources/_{ytffmpeg_cfg["name"]}.mkv`')
        outfile = f'resources/_{ytffmpeg_cfg["name"]}.mkv'
    video_cfg = {
        'input': to_concat,
        'output': outfile,
        'filter_complex': concat_filter_complex,
    }
    ytffmpeg_cfg['videos'].append(video_cfg)
    utils.save(ytffmpeg_cfg['videos'])
    cv = compileVideo(video_cfg, **kwargs)
    if cv != 0:
        log.warning('compileVideo() at this step did not succeed. This may cause downstream effects from here...')
    return outfile

def compileVideo(video_opts: dict, overwrite: bool = False) -> int:
    '''
    Craft the FFMpeg command and execute on the video conversion.
    '''
    with utils.video_processing_lock('build'):
        now = time.time()
        final_cmd = [os.getenv('FFMPEG_BIN', 'ffmpeg'), '-hide_banner']
        assert 'input' in video_opts, 'No input specified for video!'
        assert 'output' in video_opts, 'No output specified for video!'
        assert isinstance(video_opts['input'], list), 'Input must be an array!'
        vidnow = time.time()
        output = video_opts["output"]
        if output is None:
            log.warning(f'Skipping vid because output is set to None.')
            return 1
        attributes = video_opts.get('attributes', [])
        log.info(f'Processing video: \x1b[1m{output}\x1b[0m')
        # self._preBuildHooks(video_opts)

        # Process ffmpeg input/output options.
        ## Append the `-i` arguments accordingly.
        for input_video in video_opts['input']:
            final_cmd.extend(inputToArgList(input_video))
        # With the pre-hook, this should just execute now.
        if os.path.exists('thumbnail.png'):
            final_cmd.append('-i')
            final_cmd.append('thumbnail.png')
        # Process a filter_complex if we have one.
        if 'filter_complex' in video_opts:
            filter_complex = f'build/{utils.filename(output)}.filter_complex'
            with open(filter_complex, 'w', encoding='utf-8') as fc:
                for fc_line in video_opts['filter_complex']:
                    if fc_line.startswith('#'): continue
                    fc.write(fc_line + '\n')
                    fc.flush()
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
            if overwrite:
                log.info(f'Overwriting existing \x1b[1m{output}\x1b[0m!')
            else:
                log.info(f'File \x1b[1m{output}\x1b[0m already exists!')
                return 0
        subprocess.run(final_cmd, shell=False)
        vidthen = time.time()
        log.info(f'Done processing \x1b[1m{output}\x1b[0m in {round(vidthen-vidnow,4)} seconds!')
        os.system('stty echo -brkint -imaxbel icanon iexten icrnl')
        then = time.time()
        log.info(f'Completed all media in \x1b[4m{round(then-now, 2)}\x1b[0m seconds!')
    return 0
