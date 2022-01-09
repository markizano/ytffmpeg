#!/bin/bash -e

test -z "$prepareTS" || {
  echo -e "\e[34mprepareTS\e[0m=$prepareTS"
  #ffmpeg -i mp4/00.mp4 -t 00:00:07.8 -q:v 0 -vf scale=-1:1024 -c:v mpeg2video -c:a aac -y 00.ts
  #ffmpeg -i mp4/01.mp4 -t 00:00:15.7 -q:v 0 -vf scale=-1:1024 -c:v mpeg2video -c:a aac -y 01.ts
  for mp4 in */*.mp4; do
    ts=`basename $mp4 .mp4`
    t=''
    test "$ts" == 00 && {
      t='-t 00:00:07.8'
    }
    test "$ts" == 01 && {
      t='-t 00:00:15.7'
    }
    test "$ts" == 03 && {
      t='-t 00:00:03.2'
    }
    ffmpeg -i $mp4 $t -q:v 0 -vf scale=-1:1024 -c:v mpeg2video -c:a aac -map_metadata -1 -y $ts.ts;
  done
}

test -z "$concat" || {
  echo -e "\e[34mconcat\e[0m=$concat"
  truncate -s0 concat.txt
  for ts in ??.ts; do
    echo "file './$ts'" >> concat.txt
  done
  ffmpeg -safe 0 -f concat -i concat.txt -q:v 0 -y final.ts
}

# Do what you need to do with Audacity.
test -z "$final" || {
  echo -e "\e[34mfinal\e[0m=$final"
  ffmpeg -i final.ts -i final.ac3 -c:v libx264 -c:a aac -map 0:v:0 -map 1:a:0 -y final.mp4
}

