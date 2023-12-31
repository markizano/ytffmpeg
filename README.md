# ffmpeg-youtube
Python project I use to convert my videos into stuff that can be posted on YouTube, TikTok,
Instagram and other social media sites.

FFMPEG is a great video editor by itself, but it's difficult to manage that incredible description
library it has.

With this project, I hope to make it easier for program-oriented folks like me to have a 
descriptive file that converts your videos for you instead of having to remember complex filter 
graphs. Simply describe what you want the video to do and this app will help you in executing those 
changes.

This is a very context-specific application that is catered to my needs. I never expected it to
become popular, but if it does, here's to all who may contribute to this project or find it useful
in their own video editing process endeavours.

# Usage
When recording from phone or cam, it's difficult to manage all the media and content that comes in 
without paying for crazy software to get it done. With this open-source product, you can simply 
`pip3 install ffmpeg2youtube` and go!

This project honours configuration defined in a system-wide configuration file in `/etc/ytffmpeg/config.yml`,
user-specific configuration defined in `~/.config/ytffmpeg/config.yml`, with the configurations merged
together in that order as defined. A top-level directive `.ytffmpeg` in `jq` notation would configure
how `ytffmpeg` operates globally, but also respects that data structure on a per-project level as well.

To create a new project, let's use this:

    ytffmpeg new

This will render a new project with the following directory structure:

    .
    ├── build/
    ├── readme.md
    ├── resources/
    └── ytffmpeg.yml

You can drop your MP4 files from your devices into the `./resources/` directory.

Next, we can run `ytffmpeg refresh` to refresh the YAML file that is the configuration driving the 
changes we will be performing here.

This may take a moment as ffmpeg converts your MP4 format videos into MKV format under high 
compression as lossless as possible. This will reduce the amount of disk that is consumed by the 
videos recorded and saved raw from devices. Subtitles will also be automatically generated from
the video files!

Once your videos have been compressed and subtitles generated for them, you will have artifacts
available in the `./build/` directory as well.

INFO: See doc/configuration.md for more information about `ytffmpeg.yml` configuration.

Once your videos have been compressed and your configuration updated, you will see the YAML
has been updated with the new video. If you have a preferred name for it, you should rename
the file prior to running `ytffmpeg refresh`.

Observe that subtitles will also be generated as a result of this update. To avoid this, you can
use `--no-auto-subtitles` when executing `ytffmpeg refresh --no-auto-subtitles` and it will go a bit faster. 

You can update the YAML configuration to have it execute a number of filters and stream the videos
together into a final cut that can be used for social media sites and such.

The top-level `videos` is an array which will contain the set of video descriptions you will use
to describe how you want transformations done on those videos.

To learn more about the ytffmpeg.yml file, see docs/ytffmpeg.md

Once you have your transformations written out, you can use this:

```bash
ytffmpeg build myvideo
```

This will build your video. If you omit any arguments, it'll attempt to build all videos in your
project and ensure they are ready to go!

This project takes some of the rough edges off of the `filter_complex` argument in ffmpeg.

This started off as a simple script to try and automate some of the rough edges of my process
when recording content and publishing to the platforms. Features I'd like to add to this include:
- `ytffmpeg publish` to publish to your configured social media platforms
-- I want to support YouTube, TikTok, and Mastadon.
- Stream specifier error clarification: It would be nice to know that a stream is disconnected
  right there in vscode or some editor of sorts. I hope a project like this can make that more
  easily accesible as a potential by simulating the results of the configuration in ffmpeg's
  `filter_complex` parameter.
