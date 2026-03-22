# MKZ Forge

This is a Python project I use and maintain to automate various aspects of my video editing
process to publish on video supporting platforms like TikTok, YouTube, LinkedIn and Substack.

FFMPEG is a great video editor by itself, but it's difficult to manage that incredible description
library it has.

This project handles the following process for me:

* **Convert MP4 files to MKV** files to compress for disk space.
* **Cut Silence** from videos to remove the "uhm"s and "uuh"s.
* **Combine videos** so multiple uploads can result in a single artifact to publish.
* **Generate subtitles** using OpenAI's `whisper` libraries for hardsubs/captions.
* **Generate Metadata** for title and description based on the content of the video.
* **Generate Thumbnail** using Google's GenAI Image generation API.
* **Pristine Video Production** for that final product you see on video platforms posted by me.

In a single upload (or multi-file upload), I can quickly generate videos that already have
captions hardcoded into them, metadata attached so platforms can easily and quickly categorize
my videos for publishing (if they support that kind of thing).

With this project, I hope to make it easier for program-oriented folks like me to have a
descriptive file that converts your videos for you instead of having to remember complex filter
graphs. Simply describe what you want the video to do and this app will help you in executing those
changes.

This is a very context-specific application that is catered to my needs. I never expected it to
become popular, but if it does, here's to all who may contribute to this project or find it useful
in their own video editing process endeavours.

## Usage

When recording from phone or cam, it's difficult to manage all the media and content that comes in
without paying for crazy software to get it done. With this open-source product, you can simply
`pip install mkzforge` and go!

This project honours configuration defined in a system-wide configuration file in `/etc/mkzforge/config.yml`,
user-specific configuration defined in `~/.config/mkzforge/config.yml`, with the configurations merged
together in that order as defined.

To create a new project, let's use this:

```bash
mkzforge new
```

This will render a new project with the following directory structure:

```none
.
├── build/
├── readme.md
├── resources/
└── mkzforge.yml
```

You can drop your MP4 files from your devices into the `./resources/` directory.

Next, we can run

```bash
mkzforge normalize
```

to refresh the YAML file that is the configuration driving the
changes we will be performing here.

This may take a moment as ffmpeg converts your MP4 format videos into MKV format under high
compression as lossless as possible. This will reduce the amount of disk that is consumed by the
videos recorded and saved raw from devices. Subtitles will also be automatically generated from
the video files using Whisper! The system automatically detects your GPU VRAM and selects the
best Whisper model that fits (preferring `large-v3` for high-end GPUs).

**Concurrent Processing:** If you run multiple mkzforge instances simultaneously, they will
automatically queue for GPU access using a file-based lock to prevent OOM (Out Of Memory) errors.
Each instance waits its turn instead of competing for GPU resources.

You can suppress auto-subtitle generation with the `--no-subtitles` argument.

Once your videos have been compressed and subtitles generated for them, you will have artifacts
available in the `./build/` directory as well.

INFO: See doc/configuration.md for more information about `mkzforge.yml` configuration.

You can use this:

```bash
mkzforge gensubs [path-to-file.mkv]
```

This will generate subtitles in `build/path-to-file.${LANG}.srt` for any video file you give this
command. This is not necessary if you used `mkzforge refresh` to generate subs from a video
resource. I used this to get access to the sub-generation functionality this app provided with this
command and so I exposed that function to this command here. You can elect to do more with it after
that.

Once your videos have been compressed and your configuration updated, you will see the YAML
has been updated with the new video. If you have a preferred name for it, you should rename
the file prior to running `mkzforge refresh`.

Observe that subtitles will also be generated as a result of this update. To avoid this, you can
use `--no-subtitles` when executing `mkzforge refresh --no-auto-subtitles` and it will go a bit faster.

You can update the YAML configuration to have it execute a number of filters and stream the videos
together into a final cut that can be used for social media sites and such.

The top-level `videos` is an array which will contain the set of video descriptions you will use
to describe how you want transformations done on those videos.

To learn more about the mkzforge.yml file, see docs/mkzforge.md

Once you have your transformations written out, you can use this:

```bash
mkzforge build build/myvideo.mp4
```

This will build your video. If you omit any arguments, it'll attempt to build all videos in your
project and ensure they are ready to go!

This project takes some of the rough edges off of the `filter_complex` argument in ffmpeg.

This started off as a simple script to try and automate some of the rough edges of my process
when recording content and publishing to the platforms.

## Multi-Language Subtitle Support

mkzforge now supports automatic translation of subtitles to multiple languages using Argos Translate!

### Quick Start

1. **Configure languages in your `mkzforge.yml`:**

    ```yaml
    mkzforge:
      language: en           # Base language for Whisper transcription
      languages:             # Translate to these languages
        - en                 # English (from Whisper)
        - es                 # Spanish (translated)
        - fr                 # French (translated)
        - de                 # German (translated)
    ```

2. **Run refresh to generate and translate subtitles:**

    ```bash
    mkzforge refresh
    ```

    This will:

    * Generate English subtitles using Whisper
    * Automatically translate to Spanish, French, and German
    * Preserve timing information from the original subtitles
    * Create separate SRT files for each language in `build/`

3. **Build your video with all subtitle tracks:**

```bash
mkzforge build
```

The final video will contain all subtitle tracks, properly mapped and labeled.

### How Translation Works

**Context-Aware Translation**: The entire transcript is translated as one document to preserve
meaning, intent, and context. This produces much better results than translating line-by-line.

**Timing Preservation**: After translation, the system intelligently splits the translated text to
match the original subtitle timing, distributing words proportionally across subtitle entries.

**Automatic Package Management**: Argos Translate language packages are downloaded and installed
automatically on first use.

### Example Output

After running `mkzforge refresh` with multi-language support:

```plain
build/
├── my-video.mkv              # Processed video
├── my-video.txt              # Full English transcript
├── my-video.en.srt           # English subtitles (Whisper)
├── my-video.es.srt           # Spanish translation
├── my-video.fr.srt           # French translation
├── my-video.de.srt           # German translation
└── my-video.mp4              # Final video with all subtitle tracks
```

### Supported Languages

Any language pair supported by Argos Translate, including:

* Spanish (es), French (fr), German (de), Portuguese (pt)
* Italian (it), Russian (ru), Chinese (zh), Japanese (ja)
* Arabic (ar), Hindi (hi), Korean (ko)
* And many more!

For detailed documentation, see [CHANGES.md](CHANGES.md).

## @FutureFeature

Features I'd like to add to this include:

* `mkzforge publish` to publish to your configured social media platforms
  * I want to support YouTube, TikTok, and Mastadon.
  * Right now, only an SFTP endpoint is supported (uses [Fabric](https://www.fabfile.org/)).
* Stream specifier error clarification: It would be nice to know that a stream is disconnected
  right there in vscode or some editor of sorts. I hope a project like this can make that more
  easily accesible as a potential by simulating the results of the configuration in ffmpeg's
  `filter_complex` parameter.
