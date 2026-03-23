# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MKZ Forge is a Python video processing automation tool that wraps FFmpeg's `filter_complex` into a
YAML-driven pipeline. It handles the full workflow: MP4→MKV normalization, silence removal,
Whisper subtitle generation, multi-language translation, LLM metadata generation, Gemini thumbnail
generation, and publishing.

## Commands

### Install & Setup

```bash
uv pip install -e . # standard editable install
```

### Running

```bash
mkzforge --help
mkzforge new [path]           # Create new project
mkzforge normalize            # Normalize videos (compress, silence removal, subtitles)
mkzforge build [output]       # Build final video from mkzforge.yml
mkzforge gensubs [video]      # Generate subtitles only
mkzforge metadata             # Generate LLM title/description
mkzforge genimage             # Generate Gemini thumbnail
mkzforge publish [file]       # Publish to SFTP/YouTube/TikTok
mkzforge serve [--workspace /path] [--http-port 9091]  # Start web interface
```

### Testing

```bash
uv run pytest                  # Run all tests, including the virtualenv.
```

Tests are split into `tests/mkzforgeunit/` (unit) and `tests/mkzforgefunc/`
(functional/integration). Fixtures live in `tests/fixtures/configs/`.

## Architecture

### Pipeline Flow

1. `mkzforge normalize` → converts MP4→MKV (H.265 crf=28), removes silence via FFmpeg `silencedetect`,
   runs Whisper for subtitles, translates via Argos Translate, calls LLM for metadata
2. `mkzforge build` → reads `mkzforge.yml`, constructs FFmpeg filter graph via `filter_complex.py`
   DSL, produces final MP4
3. `mkzforge publish` → uploads via SFTP (Fabric), with hooks for YouTube/TikTok

### Key Modules

| Module | Purpose |
|--------|---------|
| `cli/__init__.py` | Argument parsing, action dispatch, config merging |
| `videos.py` | MP4→MKV, silence detection, video compilation |
| `subtitles.py` | Whisper integration, SRT parsing/writing |
| `i18n.py` | Argos Translate integration, subtitle re-timing |
| `filter_complex.py` | FFmpeg filter graph DSL abstraction |
| `metadata.py` | LangChain LLM calls for titles/descriptions |
| `genimg.py` | Google Gemini image generation, SVG thumbnails |
| `webserv.py` | CherryPy REST API + background workers |
| `notify.py` | AWS SNS singleton |
| `utils.py` | Config loading, GPU VRAM detection |
| `types.py` | Enums: `Devices`, `Action`, `WhisperTask` |
| `const.py` | Supported languages, API key constants |

### Config Loading Order (merged, last wins)

1. `/etc/mkzforge/config.yml`
2. `~/.config/mkzforge/config.yml`
3. `./mkzforge.yml` (project-specific)
4. CLI arguments

### Project Directory Structure

```plain
my-project/
├── mkzforge.yml    # YAML config describing build pipeline
├── resources/      # Input MP4/MKV files
└── build/          # Generated outputs (MKV, SRT, MP4, PNG)
```

### `mkzforge.yml` Schema

```yaml
videos:
  - input: [list of files/sources]
    output: output.mp4
    attributes: [subs, no-video, no-audio, vsync, no-publish, thumbnail]
    languages: [en, es, fr]
    filter_complex: [ffmpeg filter directives]
    metadata:
      title: "..."
      description: "..."
    map:
      video: "[v]"
      audio: "[a]"
      subs: 0
```

Full schema documented in `lib/mkzforge/schema.json` and `doc/configuration.md`.

### Whisper Model Auto-Selection (by GPU VRAM)

- ≥10GB → `large-v3`; 8–10GB → `large-v2`; 6–8GB → `medium`; 3–6GB → `small`; <3GB → `base`; CPU
  fallback → `small`

### GPU Locking

File-based lock prevents concurrent GPU usage across multiple `mkzforge` processes.

## Key Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `LANGUAGE` | `en` | Base transcription language |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `WHISPER_MODEL` | auto | Override Whisper model selection |
| `LLM_MODEL` | `gpt-oss:20b` | LLM model name |
| `LLM_PROVIDER` | `ollama` | LLM provider |
| `GOOGLE_API_KEY` | — | Gemini API key |
| `GEMINI_IMAGE_MODEL` | `gemini-2.5-flash-image` | Gemini model |
| `HTTP_PORT` | `9091` | Web server port |
| `OMP_NUM_THREADS` | `nproc` | CPU thread count |

## Versioning

Uses `setuptools-scm` — version is derived from git tags (`v*` format). Version is written to
`lib/mkzforge/_version.py` automatically.
