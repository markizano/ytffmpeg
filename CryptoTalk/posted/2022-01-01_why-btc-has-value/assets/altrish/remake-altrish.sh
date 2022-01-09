#!/bin/bash

ffmpeg -t 00:01.0 -r 30 -loop true -i altrish.png -f lavfi \
 -i "color=size=576x1024:duration=$(python3 -c 'print(round(1/30, 4))'):color=0x00000000,setsar=1:1" \
 -filter_complex "[0:v]format=rgba,scale='576-max(n*576/30, 0.01)':1024:eval=frame,pad=576:1024:'576-max(iw/2, 0.01)':1024:eval=frame,setsar=1:1[v0];[v0][1:v]concat[video]" \
 -map [video] -y -c:v png -vsync 2 altrish.mp4

ffmpeg -t 00:02.033 -r 30 -loop true -i youtube.png -f lavfi -i "color=size=576x1024:duration=$(python3 -c 'print(round(1/30, 4))'):color=0x00000000,setsar=1:1" \
  -filter_complex "[0:v]format=rgba,scale='0+max(if(between(n,0,30),n,60-n)*576/30, 0.01)':1024:eval=frame,pad=576:1024:'576-max(iw/2, 0.01)':1024:color=0x00000000:eval=frame,setsar=1:1,trim=start=0.033:end=2.0[v0];[v0][1:v]concat[video]" \
  -map [video] -y -c:v png -vsync 2 youtube.mp4

ffmpeg -t 00:01.033 -r 30 -loop true -i altrish-youtube.png \
  -filter_complex "[0:v]format=rgba,scale='0+max(n*576/30, 0.01)':1024:eval=frame,pad=576:1024:'576-max(iw/2, 0.01)':1024:color=0x00000000:eval=frame,setsar=1:1,trim=start=0.033:end=1.0[video]" \
  -map [video] -c:v png -vsync 2 -y altrish-youtube.mp4


ffmpeg -i altrish.mp4 -i youtube.mp4 -i altrish-youtube.mp4 -i end.mp4 \
  -t 5 -f lavfi -i anullsrc=channel_layout=5.1:sample_rate=48000 \
  -filter_complex "[0:v][1:v][2:v][3:v]concat=n=4,format=yuv420p[video];[4:a]anull[audio]" -map [video] -map [audio] \
  -vsync 2 -c:v libx264 -crf 24 -c:a aac -y altrish-youtube-final.mp4

