# Configuration

The configuration directives in the `ytffmpeg.yml` file drive how the program behaves.
Each project will have its own `ytffmpeg.yml` configuration available in the root of the
project (acting like many other projects' `package.json` for npm and `Makefile` for make).

You can use `/etc/ytffmpeg/config.yml` for system-wide global configuration for how `ytffmpeg`
will behave. You can use `~/.config/ytffmpeg/config.yml` for user-preferences on how `ytffmpeg`
shall behave. Configuration directives referenced here under the `jq` notation for `.ytffmpeg[]`
will control how `ytffmpeg` behaves.

The following descriptions of the configuration are using the `jq` reference of where a part
of a data structure exists and more description around that data structure and its function
within `ytffmpeg`.

# Environment Variables

## LANGUAGE
- Default: "en"
- Choices: One of the country codes as defined by `ytffmpeg.cli.base::BaseCommand.LANGS`
- Description: Default language to write out for the SRT file.
- @TODO: make it possible to support a list of comma-delimited languages?

## OMP_NUM_THREADS
- Default: "`nproc`"
- Description: When running on CPU, make sure to set the same number of threads.
  Many frameworks will read the environment variable OMP_NUM_THREADS, which can be set when
  running your script

## LOG_LEVEL
- Default: "INFO"
- Description: `kizano.getLogger()` respects the environment varibale for the log level.
  The command lines have also been tweaked to enable this feature.

## WHISPER_MODEL
- Default: guillaumekln/faster-whisper-large-v2
- Description: Define a different LLM model to use to translate text. These are downloaded
  from https://huggingface.co/

## FFMPEG_BIN
- Default: `ffmpeg`
- Description: Specify an alternate path to the `ffmpeg` binary to execute.

# Behaviour

At the top level data structure, you can configure `ytffmpeg` with `.ytffmpeg`. This is a
dictionary containing the configuration directives. Again, this can be configured system-wide
in `/etc/ytffmpeg/config.yml` or on a user-basis in `~/.config/ytffmpeg/config.yml`.

## .ytffmpeg.subtitles
- Type: string
- Default: `True`
- Description: Enables support for handling subtitles.
  Cli argument `--no-auto-subtitles` can be used to set this to `False` on a per-execution basis.

## .ytffmpeg.overwrite
- Type: boolean
- Default: `False`
- Description: Controls whether to overwrite files when generating assets. Useful when wanting
  to avoid reading from cache and just forcefully generate a fresh subset of build artifacts from
  the resources.
  Can be set to true per-execution with the `-f` or `--force` cli argument.

## .ytffmpeg.delete_mp4
- Type: boolean
- Default: `False`
- Description: Controls whether `ytffmpeg` will delete the MP4 files after successfully converting
  them to a compressed MKV format.

## .ytffmpeg.log_level
- Type: str
- Default: INFO
- Description: Choice of DEBUG, INFO, WARNING, ERROR, CRITICAL for logging level. (mostly DEBUG and INFO are used).

## .ytffmpeg.youtube
- Type: dict
- Default: `{}`
- Description: Contains the `client_id` and `client_secret` used to communicate with YouTube.
  @FutureFeature as of 1.0.0

## .ytffmpeg.tiktok
- Type: dict
- Default: `{}`
- Description: Contains the `client_id` and `client_secret` used to communicate with TikTok.
  @FutureFeature as of 1.0.0

*@TODO*: Support for Reels?

# Videos

At the top of the data structure, we have `.videos[]` which is an array of objects containing the
videos we will be tracking, modifying and converting into our project.

## .videos[].input
- Type: Array of {str|dict}. If `str`, read as input video. If `dict`, then each of the keys of
  said dictionary will be fed into the `-i` arguments to ffmpeg and a key of "i" is required.
- Default: None
- *Required!*
- Description: In each video description, it will need a series of inputs to feed the video stream.
  At least 1 video input is required.

All parts of this data structure will eventually be fed into the "-i" argument as such.

In this way, if there's a loop or custom framerate, those may be specified as part of this input file.
All components of this data structure are fed into their respective arguments.

### Example

The following YAML data structure:

```yaml
videos:
  -
    input:
    - 
      loop: true
      framerate: 30
      t: 5
      i: resources/intro.png
```

Would result in these arguments being passed to ffmpeg:

```bash
ffmpeg -framerate 30 -t 5 -loop true -i resources/intro.png
```

The `-f` argument is provided first and the `-i` argument is provided last to ensure all options that describe
"this" input are defined before providing the input to `ffmpeg`.

## .videos[].output
- Type: str
- Default: ''
- *Required!*
- Description: Target output video. Only one output is allowed.

## .videos[].attributes
- Type: List of strings.
- Default: []
- Description: Custom attributes that will make ytffmpeg treat this video differently.
- Values:
- - `no-video`: Don't process video for this stream.
- - `no-audio`: Don't process audio for this stream.
- - `subs`: This video uses subtitles.
- - `vsync`: Whether to enable breaking the synchronization of video-to-audio timestamps.
    (See `fps_mode` in `ffmpeg` man page for more details).

## .videos[].languages
- Type: List of strings.
- Default: `['en']`
- Description: Provides the supported languages if international support is needed.
  Will attempt to stream an additional subtitle stream for each language.
  (may not be compatible with the `mp4/mjpeg4` container)

## .videos[].metadata
- Type: dict
- Default: See `.ytffmpeg.defaults.metadata`. Unconfigured default will be empty.
- Description: Sets metadata for this video. By default, all output metadata is stripped prior
  to writring encoding result.

## .videos[].map
- Type: dict
- Default: {}
- Description: Map these streams into the resulting video. Streams available are as follows:

```yaml
videos:
  -
    # ...
    map:
      video: '[video]'
      audio: '[audio]'
      subs: '2:s'
    # ...
```

## .videos[].filter_complex
- Type: list{str|dict}
- Default: []
- Description: List of strings that are concatenated to represent the filter complex graph from within FFmpeg.
  This is the crux of this application and the headspace I want to try to automate for myself.

I plan on driving into this data structure further to interpolate everything it has to offer and provide
additional functionality on top of this by allowing for either data structures to describe the functions
and their respective arguments with proper quoting and all that.
Also, I want to provide "shortcuts" to certain function bundles. For example, it would be great to be able
to create custom "functions" that `ytffmpeg` will see and interpret differently before passing to `ffmpeg`.
Example: I use `scale,setsar` often as a pair. I also use `trim,setpts` as another pair of functions that
are often strung together. When dealing with video streams and cuts, you find that certain things must
always be done or set and if you aren't in the business of making videos all the time, it's not always
obvious. This is an attempt to make some of that more accessible by providing alternate/additional
functionality to make the filter_complex part easier to access for the non-programmer.


# Samples
Here's a sample JSON that I have used for extensive video production:

```json
    {
      "videos": [
        {
          "input": [
              { "f": "lavfi", "i": "color=color=0x00000000:size=1920x1080,format=rgba,setsar=1:1"},

              { "i": "resources/Yaba1.0/yaba.intro.mp4" },
              { "i": "resources/Yaba1.0/github-download.mp4" },

              { "i": "resources/Yaba1.0/screenrecord.home.mp4" },
              { "i": "resources/Yaba1.0/yaba.home.mp4" },

              { "i": "resources/Yaba1.0/screenrecord.settings.mp4" },
              { "i": "resources/Yaba1.0/yaba.settings.mp4" },

              { "i": "resources/Yaba1.0/screenrecord.institutions.mp4" },
              { "i": "resources/Yaba1.0/yaba.institutions.mp4" },

              { "i": "resources/Yaba1.0/screenrecord.accounts.mp4" },
              { "i": "resources/Yaba1.0/yaba.accounts.mp4" },

              { "i": "resources/Yaba1.0/screenrecord.account.mp4" },
              { "i": "resources/Yaba1.0/yaba.account.mp4" },

              { "i": "resources/Yaba1.0/screenrecord.budgeting.mp4" },
              { "i": "resources/Yaba1.0/yaba.budgeting.mp4" },

              { "i": "resources/Yaba1.0/screenrecord.charts.mp4" },
              { "i": "resources/Yaba1.0/yaba.charts.mp4" },

              { "i": "resources/Yaba1.0/screenrecord.prospecting.mp4" },
              { "i": "resources/Yaba1.0/yaba.prospect.mp4" },

              { "i": "resources/Yaba1.0/yaba.closing.mp4" }
          ],
          "output": "1.0/Yaba1.0.mp4",
          "attributes": [ "vsync" ],
          "filter_complex": [
            "[1:v]fps=29,trim=start=4.5:end=256.5,setpts=PTS-STARTPTS[vIntro0_]",
            "[vIntro0_]drawtext=fontfile=/home/YouTube/resources/DejaVuSans.ttf:text='yaba.markizano.net':fontcolor=black:fontsize=120:box=1:boxcolor=white@0.8:boxborderw=25:x=590:y=590:alpha='if(lt(t,94.5),0,if(lt(t,96),(t-96)/1,if(lt(t,98),1,if(lt(t,95.5),(1-(t-99.5))/1,0))))'[vIntro0]",
            "[1:a]atrim=start=4.5:end=256.5,asetpts=NB_CONSUMED_SAMPLES/SR/TB[aIntro0]",

            "# Don't forget to include download-github.mp4 in here somewhere...",
            "[1:v]fps=29,trim=start=258:end=307,setpts=PTS-STARTPTS[vSecurityCheck_]",
            "[2:v]fps=29,crop=iw:ih-40:0:40,scale=1280x720,fade=in:st=0:d=2:alpha=1,setpts=(PTS-STARTPTS)*0.302748,fade=out:st=5:d=1:alpha=1,setpts=PTS+(19.5/TB)[githubDownload]",
            "[vSecurityCheck_]drawtext=fontfile=/home/YouTube/resources/DejaVuSans.ttf:text='github.com/markizano/yaba':fontcolor=black:fontsize=80:box=1:boxcolor=white@0.8:boxborderw=25:x=530:y=590:enable='between(t,17,19.5)'[toGithub]",
            "[toGithub][githubDownload]overlay=(W-w)/2:(H-h)/2:enable='between(t,19.5,26)'[withDownload]",
            "[withDownload]drawtext=fontfile=/home/YouTube/resources/DejaVuSans.ttf:text='Yaba.zip/public/index.html':fontcolor=black:fontsize=80:box=1:boxcolor=white@0.8:boxborderw=25:x=530:y=590:enable='between(t,34.5,38)'[vSecurityCheck]",
            "[1:a]atrim=start=258:end=307,asetpts=NB_CONSUMED_SAMPLES/SR/TB[aSecurityCheck]",

            "[1:v]fps=29,trim=start=321:end=362,setpts=PTS-STARTPTS[vUnencrypted]",
            "[1:a]atrim=start=321:end=362,asetpts=NB_CONSUMED_SAMPLES/SR/TB[aUnencrypted]",

            "[1:v]fps=29,trim=start=392.1:end=397.5,setpts=PTS-STARTPTS[vIntroOut]",
            "[1:a]atrim=start=392.1:end=397.5,asetpts=NB_CONSUMED_SAMPLES/SR/TB[aIntroOut]",

            "[vIntro0][vSecurityCheck][vUnencrypted][vIntroOut]concat=n=4[vIntro]",
            "[aIntro0][aSecurityCheck][aUnencrypted][aIntroOut]concat=v=0:a=1:n=4[aIntro]",

            "# Accordian horizontal transition.",
            "## Trim 4s of black space to be used in the full transition.",
            "[0:v]trim=duration=4,fps=29,setpts=PTS-STARTPTS[blackground0]",
            "[1:v]fps=29,trim=start=397.5:end=400.5,setpts=PTS-STARTPTS,fade=out:st=0:d=3:alpha=1,split[left][right]",
            "[left]crop=960:1080:0:0,scale='lerp(960,100,t/3)':1080:eval=frame[leftDoor]",
            "[right]crop=960:1080:960:0,scale='lerp(960,100,t/3)':1080:eval=frame[rightDoor]",
            "[blackground0][leftDoor]overlay='lerp(0,860,t/3)':0[withLeft]",
            "[withLeft][rightDoor]overlay=960:0[vHShift]",
            "[1:a]atrim=start=397.5:end=400.5,asetpts=NB_CONSUMED_SAMPLES/SR/TB[aHShift]",

            "# Accordian vertical transition.",
            "[4:v]crop=1080:1530:0:0,scale=760x1080,setsar=1:1,fps=29,trim=start=18:end=20,setpts=(PTS-STARTPTS)+(2/TB),fade=in:st=2:d=2:alpha=1,scale=760:'lerp(50,1080,(t-2)/2)':eval=frame[vVShift]",
            "[4:a]atrim=start=18:end=20,asetpts=NB_CONSUMED_SAMPLES/SR/TB,adelay=2s:all=1,afade=in:st=2:d=2[aVShift]",

            "# Tie the two together so we can render the transition here.",
            "[vHShift][vVShift]overlay=580:'lerp(580,0,(t-2)/2)':enable='gt(t,2)'[vTransitionOpen]",
            "[aHShift][aVShift]amix=inputs=2:weights=1|1,aresample=48000,atrim=start=0:end=4,asetpts=NB_CONSUMED_SAMPLES/SR/TB,aresample=48000[aTransitionOpen]",

            "# Setup for scaling me in the corner with the fade-in to the next page.",
            "[0:v]fps=29,trim=start=0:duration=3,setpts=PTS-STARTPTS[blackground1]",
            "[3:v]fps=29,trim=start=0:end=3,setsar=1:1,setpts=PTS-STARTPTS,fade=in:st=0:d=3[homePage]",
            "[blackground1][homePage]overlay=0:0,setpts=PTS-STARTPTS[homeFadeIn]",
            "[4:v]crop=1080:1530:0:0,scale=760:1080,setsar=1:1,fps=29,trim=start=20:end=23,setpts=PTS-STARTPTS,scale='lerp(760,360,t/3)':'lerp(1080,512,t/3)':eval=frame[vScaleDown_]",
            "[homeFadeIn][vScaleDown_]overlay='lerp(580,1560,t/3)':'lerp(0,570,t/3)':eof_action=endall[vScaleDown]",
            "[4:a]atrim=start=20:end=23,asetpts=NB_CONSUMED_SAMPLES/SR/TB,aresample=48000[aScaleDown]",

            "[vTransitionOpen][vScaleDown]concat[vTransition]",
            "[aTransitionOpen][aScaleDown]concat=v=0:a=1[aTransition]",

            "[4:v]crop=1080:1530:0:0,scale=760:1080,setsar=1:1,fps=29,trim=start=23:end=71.5,setpts=PTS-STARTPTS,scale=360x512[me_HomePage]",
            "[3:v]fps=29,trim=start=0:end=38,setpts=(PTS-STARTPTS)*1.269633,setsar=1:1[s_HomePage]",
            "[s_HomePage][me_HomePage]overlay=W-w:H-h:shortest=1:eof_action=endall[vHomePage_]",
            "[4:a]atrim=start=23:end=71.5,asetpts=NB_CONSUMED_SAMPLES/SR/TB[aHomePage_]",

            "[vTransition][vHomePage_]concat[vHomePage]",
            "[aTransition][aHomePage_]concat=v=0:a=1[aHomePage]",

            "[6:v]crop=1080:1530:0:0,scale=760:1080,setsar=1:1,fps=29,trim=start=0:end=111.5,setpts=PTS-STARTPTS,scale=360x512[me_Settings]",
            "[6:a]atrim=start=0:end=111.5,asetpts=NB_CONSUMED_SAMPLES/SR/TB[aSettings]",
            "[5:v]fps=29,trim=start=0:end=75.5,setpts=(PTS-STARTPTS)*1.476821,setsar=1:1[s_Settings]",
            "[s_Settings][me_Settings]overlay=W-w:H-h:shortest=1:eof_action=endall[vSettings]",

            "[8:v]crop=1080:1530:0:0,scale=760:1080,setsar=1:1,fps=29,trim=start=0:end=112,setpts=PTS-STARTPTS,scale=360x512[me_Institutions0]",
            "[8:v]crop=1080:1530:0:0,scale=760:1080,setsar=1:1,fps=29,trim=start=130.5:end=135.5,setpts=PTS-STARTPTS,scale=360x512[me_Institutions1]",
            "[8:a]atrim=start=0:end=112,asetpts=NB_CONSUMED_SAMPLES/SR/TB[aInstitutions0]",
            "[8:a]atrim=start=130.5:end=135.5,asetpts=NB_CONSUMED_SAMPLES/SR/TB[aInstitutions1]",
            "[7:v]fps=29,trim=start=0:end=95,setpts=(PTS-STARTPTS)*1.178947,setsar=1:1[s_Institutions0]",
            "[7:v]fps=29,trim=start=95:end=173.1,setpts=(PTS-STARTPTS)*0.063,setsar=1:1[s_Institutions1]",

            "[me_Institutions0][me_Institutions1]concat[me_Institutions]",
            "[s_Institutions0][s_Institutions1]concat[s_Institutions]",
            "[aInstitutions0][aInstitutions1]concat=v=0:a=1[aInstitutions]",

            "[s_Institutions][me_Institutions]overlay=0:H-h:shortest=1:repeatlast=1[vInstitutions]",

            "[10:v]crop=1080:1530:0:0,scale=760:1080,setsar=1:1,fps=29,trim=start=0:end=75,setpts=PTS-STARTPTS,scale=360x512[me_Accounts0]",
            "[10:v]crop=1080:1530:0:0,scale=760:1080,setsar=1:1,fps=29,trim=start=80:end=131,setpts=PTS-STARTPTS,scale=360x512[me_Accounts1]",
            "[10:a]atrim=start=0:end=75,asetpts=NB_CONSUMED_SAMPLES/SR/TB[aAccounts0]",
            "[10:a]atrim=start=80:end=131,asetpts=NB_CONSUMED_SAMPLES/SR/TB[aAccounts1]",
            "[me_Accounts0][me_Accounts1]concat[me_Accounts]",
            "[aAccounts0][aAccounts1]concat=v=0:a=1[aAccounts]",
            "[9:v]fps=29,trim=start=0:end=123,setpts=(PTS-STARTPTS)*1.024390,setsar=1:1[s_Accounts]",
            "[s_Accounts][me_Accounts]overlay=W-w:H-h:shortest=1:eof_action=endall[vAccounts]",

            "[12:v]crop=1080:1530:0:0,scale=760:1080,setsar=1:1,fps=29,trim=start=0:end=84.5,setpts=PTS-STARTPTS,scale=360x512[me_Account]",
            "[12:a]atrim=start=0:end=84.5,asetpts=NB_CONSUMED_SAMPLES/SR/TB[aAccount]",
            "[11:v]fps=29,trim=start=0:end=109,setpts=(PTS-STARTPTS)*0.775229,setsar=1:1[s_Account]",
            "[s_Account][me_Account]overlay=W-w:H-h:shortest=1:eof_action=endall[vAccount]",

            "[14:v]crop=1080:1530:0:0,scale=760:1080,setsar=1:1,fps=29,trim=start=0:end=30,setpts=PTS-STARTPTS,scale=360x512[me_Budget0]",
            "[14:v]crop=1080:1530:0:0,scale=760:1080,setsar=1:1,fps=29,trim=start=37:end=89,setpts=PTS-STARTPTS,scale=360x512[me_Budget1]",
            "[14:a]atrim=start=0:end=30,asetpts=NB_CONSUMED_SAMPLES/SR/TB[aBudget0]",
            "[14:a]atrim=start=37:end=89,asetpts=NB_CONSUMED_SAMPLES/SR/TB[aBudget1]",
            "[me_Budget0][me_Budget1]concat[me_Budget]",
            "[aBudget0][aBudget1]concat=v=0:a=1[aBudget]",
            "[13:v]fps=29,trim=start=0:end=109,setpts=(PTS-STARTPTS)*0.773584,setsar=1:1[s_Budget]",
            "[s_Budget][me_Budget]overlay=W-w:H-h:shortest=1:eof_action=endall[vBudget]",

            "[16:v]crop=1080:1530:0:0,scale=760:1080,setsar=1:1,fps=29,trim=start=1.5:end=42,setpts=PTS-STARTPTS,scale=360x512[me_Charts]",
            "[16:a]atrim=start=1.5:end=42,asetpts=NB_CONSUMED_SAMPLES/SR/TB[aCharts]",
            "[15:v]fps=29,trim=start=0:end=57.5,setpts=(PTS-STARTPTS)*0.704347,setsar=1:1[s_Charts]",
            "[s_Charts][me_Charts]overlay=W-w:H-h[vCharts]",

            "[18:v]crop=1080:1530:0:0,scale=760:1080,setsar=1:1,fps=29,trim=start=0:end=119,setpts=PTS-STARTPTS,scale=360x512[me_Prospect]",
            "[18:a]atrim=start=0:end=119,asetpts=NB_CONSUMED_SAMPLES/SR/TB[aProspect]",
            "[17:v]fps=29,trim=start=0:end=143,setpts=(PTS-STARTPTS)*0.832167,setsar=1:1[s_Prospect]",
            "[s_Prospect][me_Prospect]overlay=W-w:H-h[vProspect]",

            "[19:v]fps=29,trim=start=0:end=109.75,setpts=PTS-STARTPTS[vClosing]",
            "[19:a]atrim=start=0:end=109.75,asetpts=NB_CONSUMED_SAMPLES/SR/TB[aClosing]",

            "[vIntro][vHomePage][vSettings][vInstitutions][vAccounts][vAccount][vBudget][vCharts][vProspect][vClosing]concat=n=10[video]",
            "[aIntro][aHomePage][aSettings][aInstitutions][aAccounts][aAccount][aBudget][aCharts][aProspect][aClosing]concat=v=0:a=1:n=10[audio]"
          ]
        }
      ]
    }
```

In this example, I have created a master video containing a combination of several child video and images to overlay and mesh together.
It would be great to pull this together into a smaller data structure that required less description, but achieved the same effects
since some things must always be done together as a set, like trimming sections and setting the presentation timestamp before concatenating
the segments together to make a video segment.

FFMPEG is incredibly powerful! Let's harness that power!

