# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ytffmpeg is a Python-based video processing automation tool that simplifies complex FFmpeg
operations for creating social media content. It provides:

- YAML-driven configuration for video transformations
- Automatic subtitle generation using OpenAI Whisper with GPU auto-detection
- Multi-language subtitle translation via Argos Translate
- GPU resource management to prevent OOM errors during concurrent transcription
- Filter complex abstraction layer for FFmpeg operations

## Development Commands

### Environment Setup

```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
pip install -e .
```

### Testing

```bash
# Run all tests
python tests/runtests.py

# Run with pytest directly
pytest tests/
```

### Building and Installation

```bash
# Build package
uv build

# Install locally for development
pip install -e .
```

### Running the Application

```bash
# Main entry point
ytffmpeg --help

# Common workflows
ytffmpeg new                    # Create new project structure
ytffmpeg refresh                # Process MP4s, convert to MKV, generate subtitles
ytffmpeg build [output.mp4]     # Build final video from configuration
ytffmpeg gensubs video.mkv      # Generate subtitles for specific file
ytffmpeg publish                # Publish to configured endpoints (SFTP)
ytffmpeg serve                  # Start web interface (default: http://localhost:9091)
```

## Architecture

### Core Components

**Web Interface** (`lib/ytffmpeg/webserv.py`, `web/`)

- Browser-based UI for video upload and project management
- CherryPy-based HTTP server with REST API endpoints
- Background processing using multiprocessing for non-blocking uploads
- Static file serving for HTML/CSS/JS assets
- Key endpoints:
  - `GET /` - Video upload form
  - `GET /videos` - Projects list page
  - `GET /api/projects` - JSON list of all projects
  - `POST /api/process` - Upload and process videos
- Configuration options:
  - `--workspace`: Directory for project storage (default: `~/ytffmpeg-projects`)
  - `--http-port`: Web server port (default: 9091)
  - `--webroot`: Custom web assets directory
- See `doc/WEBSERVER.md` for detailed documentation

**CLI Module** (`lib/ytffmpeg/cli/`)

- `base.py`: BaseCommand class with shared functionality:
  - GPU lock mechanism using fcntl for preventing concurrent Whisper instances
  - Automatic Whisper model selection based on GPU VRAM detection (via nvidia-smi or torch)
  - Subtitle generation, parsing, and translation utilities
  - Configuration loading and merging (system → user → project)
- `new.py`: Project scaffolding (creates build/, resources/, ytffmpeg.yml)
- `refresh.py`: MP4→MKV conversion, subtitle generation, YAML updates
- `build.py`: Final video assembly using filter_complex definitions
- `publish.py`: Video publishing to configured endpoints

**Filter Complex System** (`lib/ytffmpeg/filter_complex.py`)

- `FilterComplexFunctionUnit`: Parses and represents individual FFmpeg filters
- `FilterComplexStream`: Represents input→functions→output stream chains
- `FilterComplexFunctionList`: Collection of filter functions
- Provides abstraction over FFmpeg's filter_complex syntax for programmatic manipulation

**Configuration** (`lib/ytffmpeg/schema.json`)

- JSON Schema defining ytffmpeg.yml structure
- Two-level configuration: global `ytffmpeg` section + per-video `videos` array
- Configuration hierarchy: `/etc/ytffmpeg/config.yml` → `~/.config/ytffmpeg/config.yml` → `./ytffmpeg.yml`

**Notification System** (`lib/ytffmpeg/notify.py`)

- SNS notification support for build completion/failures
- Replaced Discord webhooks in recent refactor

### GPU Resource Management

The `gpu_lock()` context manager in `base.py` prevents multiple Whisper instances from running simultaneously:

- Uses POSIX file locking (fcntl.flock) on `~/.cache/ytffmpeg/gpu.lock`
- Retry logic with random delays to avoid race conditions
- Configurable timeout (default: 1 hour)
- Only applies to CUDA/auto device modes, not CPU

### Whisper Model Selection

Automatic model selection in `select_whisper_model()`:

- Detects GPU VRAM via nvidia-smi (preferred) or torch
- Model VRAM requirements:
  - `tiny`/`base`: ~1GB
  - `small`: ~2GB
  - `medium`: ~5GB
  - `large-v2`/`large-v3`: ~10GB
- Falls back to `small` for CPU or low VRAM systems
- Can be overridden via `ytffmpeg.whisper_model` config

### Multi-Language Subtitle Workflow

1. Whisper generates base language subtitles (configured via `ytffmpeg.language`)
2. For additional languages in `ytffmpeg.languages`, translation occurs:
   - Full transcript translated as one document (preserves context)
   - Translated text split back to match original timing
   - Argos Translate packages auto-downloaded as needed
3. Final video includes all subtitle tracks with proper metadata

## Configuration Structure

**Project-Level** (`ytffmpeg.yml`):

```yaml
ytffmpeg:
  language: en                  # Base language for Whisper
  languages: [en, es, fr]       # Languages in final video
  subtitles: true               # Enable subtitle generation
  whisper_model: large-v3       # Override auto-selection (optional)
  device: cuda                  # cpu, cuda, or auto
  overwrite: false              # Overwrite existing files
  cut_silence: false            # Enable silence removal

videos:
  - input:
      - i: resources/video.mkv
      - i: resources/overlay.png
        loop: true
        t: 5
        framerate: 30
    filter_complex:
      - "[0:v]scale=1280x720[video]"
      - "[0:a]volume=1.5[audio]"
    map:
      en: 2:s
    metadata:
      title: "Video Title"
      description: "Description"
      date: 2024-01-01
    output: build/final.mp4
```

## Common Patterns

### Adding New FFmpeg Filters

When adding support for new FFmpeg filters, work with `FilterComplexFunctionUnit` in `filter_complex.py`. The parser automatically handles:

- Named parameters: `trim=start=1.15:end=4.5`
- Positional args: `fade=in:st=0:d=1`
- Mixed syntax: `overlay=x=10:y=20:enable='between(t,0,5)'`

### Extending CLI Commands

New CLI commands should:

1. Subclass `BaseCommand` in `cli/base.py`
2. Implement command logic
3. Register in `cli/__init__.py`
4. Add to project scripts in `pyproject.toml` if needed

### Testing GPU-Related Features

Tests in `tests/ytffmpegunit/gpu_lock.py` demonstrate:

- Concurrent lock acquisition testing
- Timeout handling
- CPU vs CUDA mode differences

## File Locations

**Source Code**: `lib/ytffmpeg/`
**Tests**: `tests/`
**Documentation**: `doc/` (mostly reference to README.md)
**Examples**: `examples/` (sample ytffmpeg.yml files for different use cases)
**Contrib**: `contrib/` (third-party integrations and deployment scripts)
  - `contrib/sysvinit/` - SysV init scripts for Devuan/non-systemd systems
**System Config**: `/etc/ytffmpeg/config.yml` (optional)
**User Config**: `~/.config/ytffmpeg/config.yml` (optional)

## Dependencies

- **FFmpeg**: Core video processing engine (external binary)
- **OpenAI Whisper**: Subtitle transcription (GPU-accelerated)
- **Argos Translate**: Multi-language subtitle translation
- **kizano**: Utility library for logging, config, YAML parsing
- **langchain**: LLM integration (used for future features)
- **PyYAML**: Configuration parsing with schema validation
- **boto3**: AWS SNS notifications

## Special Considerations

**Name Correction in Subtitles**: `correct_subtitles()` in `base.py` uses regex to fix common Whisper transcription errors for project-specific terms (Markizano, Kizano, Draconus, Tanninovian). This runs automatically after subtitle generation.

**MP4 vs MKV**: The `refresh` command converts MP4 to MKV for:

- Better compression with minimal quality loss
- Container support for multiple subtitle tracks
- Metadata preservation

**Silence Detection**: When `cut_silence: true`, uses FFmpeg's silencedetect/silenceremove filters with configurable thresholds (`silence_threshold`, `silence_duration`, `silence_pad`).
