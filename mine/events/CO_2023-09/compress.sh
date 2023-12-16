#!/bin/bash

set -ex
cd /home/YouTube/mine/events/CO_2023-09
change='-c:v libx265 -c:a ac3 -vf fps=30 -map_metadata -1 -y'
ffmpeg -i VID_20230926_195900541.mp4 -c:v libx265 -c:a ac3 -vf fps=60 -map_metadata -1 fire.mkv
ffmpeg -i VID_20230923_123303120.mp4 $change cherry-park-en.mkv
ffmpeg -i VID_20230924_093549644.mp4 $change cyrig.mkv
ffmpeg -i VID_20230924_113155507.mp4 $change dont-run-as-admin.mkv
ffmpeg -i VID_20230924_115022091.mp4 $change TOC-kizanos-fintech.mkv
ffmpeg -i VID_20230925_194516204.mp4 $change rant-about-covid-to-slaves.mkv
ffmpeg -i VID_20230926_102405471.mp4 $change rant-on-monogamy.mkv
ffmpeg -i VID_20230926_131228599.mp4 $change rant-on-women.mkv
ffmpeg -i VID_20230926_181715565.mp4 $change pan-of-property.mkv
ffmpeg -i VID_20230926_201823113.mp4 $change personal-fire.mkv
ffmpeg -i VID_20230926_204047148.mp4 $change sharing-fire.mkv
ffmpeg -i VID_20230927_070646680.mp4 $change morning-sun.mkv
ffmpeg -i VID_20230927_133443867.mp4 $change question-monogomy.mkv
ffmpeg -i VID_20230927_174758184.mp4 $change my-own-garden.mkv
ffmpeg -i VID_20230927_175202315.mp4 $change trees-to-take-down.mkv
ffmpeg -i VID_20230928_095613086.mp4 $change being-single-review_2023-09-28.mkv

