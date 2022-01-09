    {
      "input": [
        {
          "i": "assets/transition.mp4"
        }, {
          "loop": "1",
          "t": "00:05",
          "i": "assets/transition_$tname.png"
        }, {
          "i": "assets/transition_$tname.m4a"
        }
      ],
      "output": "build/${index}.1_$tname.mp4",
      "filter_complex": [
        "[0:v]split[v0][v1]",
        "[v0]fade=out:st=1:d=1[enter]",
        "[v1]format=rgba,setpts=PTS+3/TB,fade=in:st=3:d=1:alpha=1[exit]",
        "[1:v]setsar=1:1,trim=start=0:end=3,setpts=PTS+1/TB,fade=in:st=1:d=1:alpha=1,fade=out:st=3:d=1:alpha=1[what]",
        "[enter][what]overlay=0:0:enable='between(t, 1, 3)':shortest=1[first]",
        "[first][exit]overlay=0:0:enable='between(t, 3, 5)'[video]",
        "[2:a]aresample=48000[audio]"
      ],
      "attributes": [
        "vsync"
      ]
    },
