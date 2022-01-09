
all: build/final.mp4

clean:
	rm -fv build/*.mp4

build/00_intro.mp4:
	ffmpeg -hide_banner -i dApps/VID_20211017_143957287.mp4 -vf scale=576x1024,setsar=1:1 -c:a aac -c:v h264 -map_metadata -1 -y build/00_intro.mp4

build/01_TheWhat.mp4:
	ffmpeg -hide_banner -i dApps/VID_20211017_144051782.mp4 -vf scale=576x1024,setsar=1:1 -c:a aac -c:v h264 -map_metadata -1 -y build/01_TheWhat.mp4

build/02_compoundExample.mp4:
	ffmpeg -hide_banner -i screenshares/compound-dApp.mp4 \
	  -filter_complex [0:v]scale=576x1024,setsar=1:1,trim=start=0.5:end=26.0,setpts=PTS-STARTPTS[video]\;[0:a]atrim=start=0.5:end=26.0,asetpts=PTS-STARTPTS[audio] \
	  -map [video] -map [audio] -c:a aac -c:v h264 -map_metadata -1 -y build/02_compoundExample.mp4

build/03_ButWait-TheresMore.mp4:
	ffmpeg -hide_banner -i dApps/VID_20211017_144720989.mp4 \
	  -filter_complex [0:v]scale=576x1024,setsar=1:1,trim=start=0:end=12.3,setpts=PTS-STARTPTS[video]\;[0:a]atrim=start=0:end=12.3,asetpts=PTS-STARTPTS[audio] \
	  -map [video] -map [audio] -c:a aac -c:v h264 -map_metadata -1 -y build/03_ButWait-TheresMore.mp4

build/04_WhoAmI.mp4:
	ffmpeg -hide_banner -i dApps/VID_20211017_144849680.mp4 -vf scale=576x1024,setsar=1:1 -c:a aac -c:v h264 -map_metadata -1 -y build/04_WhoAmI.mp4

build/final.mp4: build/00_intro.mp4 build/01_TheWhat.mp4 build/02_compoundExample.mp4 build/03_ButWait-TheresMore.mp4 build/04_WhoAmI.mp4
	ffmpeg -hide_banner -i build/00_intro.mp4 -i build/01_TheWhat.mp4 -i build/02_compoundExample.mp4 -i build/03_ButWait-TheresMore.mp4 -i build/04_WhoAmI.mp4 -filter_complex "[0:v][1:v][2:v][3:v][4:v]concat=n=5[video];[0:a][1:a][2:a][3:a][4:a]concat=v=0:a=1:n=5[audio]" -map [video] -map [audio] -map_metadata -1 -c:v h264 -c:a aac -vsync 2 -y build/final.mp4

