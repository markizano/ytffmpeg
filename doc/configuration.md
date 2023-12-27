# Configuration

The configuration directives in the `ytffmpeg.yml` file drive how the program behaves.
Each project will have its own ytffmpeg.yml configuration available in the root of the
project (acting like many other projects' `package.json` for npm and `Makefile` for make).

There will also be available is `~/.config/ytffmpeg/config.yml` which will be global configuration for the
program itself and how files are generated and processed.

The following descriptions of the configuration are using the `jq` reference of where a part
of a data structure exists and more description around that data structure and its function
within `ytffmpeg`.

# Behaviour

At the top level data structure, you can configure `ytffmpeg` with `.ytffmpeg`. This is a
dictionary containing the configuration directives.

## .ytffmpeg.subtitles
- Type: string
- Default: `True`
- Description: Enables support for handling subtitles.

## .ytffmpeg.youtube
- Type: dict
- Default: `{}`
- Description: Contains the `client_id` and `client_secret` used to communicate with YouTube.

## .ytffmpeg.tiktok
- Type: dict
- Default: `{}`
- Description: Contains the `client_id` and `client_secret` used to communicate with TikTok.

*@TODO*: Support for Reels?

# Videos

At the top of the data structure, we have `.videos[]` which is an array of objects containing the
videos we will be tracking, modifying and converting into our project.

## .videos[].input

In each video description, it will need a series of inputs to feed the video stream.
At least 1 video input is required.

All parts of this data structure will eventually be fed into the "-i" argument as such.

In this way, if there's a loop or custom framerate, those may be specified as part of this input file.
All components of this data structure are fed into their respective arguments.

### Example

The following YAML data structure:

    videos:
      -
        input:
        - 
          loop: true
          framerate: 30
          t: 5
          i: resources/intro.png


Would result in these arguments being passed to ffmpeg:

    ffmpeg -framerate 30 -t 5 -loop true -i resources/intro.png

Known limitation: Due to Pythonic ways of handling dictionaries, the order may be arbitrary until
a proper sorting solution can be put into place.


