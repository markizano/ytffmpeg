#!/bin/bash

test -z "$prepareTS" || {
  echo -e "\e[34mprepareTS\e[0m=$prepareTS"
  for mp4 in mp4/*.mp4; do
    ffmpeg -i $mp4 -c:v mpeg2video -c:a aac -vf scale=-1:1024 -q:v 0 -map_metadata -1 -y `basename $mp4 .mp4`.ts
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

