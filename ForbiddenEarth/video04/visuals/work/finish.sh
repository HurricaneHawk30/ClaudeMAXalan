#!/bin/bash
# concat segments, 2-pass loudnorm narration (-16 LUFS), master + chat copy (<400 MiB) + 720p review (<45 MB)
set -e
cd "$(dirname "$0")"; R=../../render; D=667.6; P2=/tmp/claude-0/-home-user/12027b16-2a12-523a-ad1e-02bc5c85b1e4/scratchpad/2p
mkdir -p $P2
printf "file 'seg/seg0b.mp4'\nfile 'seg/seg1.mp4'\nfile 'seg/seg2.mp4'\nfile 'seg/seg3.mp4'\n" > concat.txt
ffmpeg -y -v error -f concat -safe 0 -i concat.txt -c copy video_noaudio.mp4
AF="apad,atrim=0:$D,aresample=48000,afade=t=out:st=$(echo "$D-0.8" | bc):d=0.8"
J=$(ffmpeg -hide_banner -i ../../voice/full.mp3 -af "$AF,loudnorm=I=-15.6:TP=-1.5:LRA=11:print_format=json" -ac 2 -f null - 2>&1 | sed -n '/^{/,/^}/p')
g(){ echo "$J" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -y -v error -i ../../voice/full.mp3 -af "$AF,loudnorm=I=-15.6:TP=-1.5:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000" -ac 2 -c:a aac -b:a 192k audio.m4a
ffmpeg -y -v error -i video_noaudio.mp4 -i audio.m4a -map 0:v -map 1:a -c copy -t $D -movflags +faststart $R/full_1080p.mp4
# chat copy
ffmpeg -y -v error -i $R/full_1080p.mp4 -c:v libx264 -preset slow -b:v 4500k -pass 1 -passlogfile $P2/c -an -f null /dev/null
ffmpeg -y -v error -i $R/full_1080p.mp4 -c:v libx264 -preset slow -b:v 4500k -pass 2 -passlogfile $P2/c -pix_fmt yuv420p -c:a copy -movflags +faststart $R/ForbiddenEarth_video04_1080p.mp4
# 720p review
ffmpeg -y -v error -i $R/full_1080p.mp4 -vf scale=1280:720 -c:v libx264 -preset slow -b:v 420k -pass 1 -passlogfile $P2/r -an -f null /dev/null
ffmpeg -y -v error -i $R/full_1080p.mp4 -vf scale=1280:720 -c:v libx264 -preset slow -b:v 420k -pass 2 -passlogfile $P2/r -pix_fmt yuv420p -c:a aac -b:a 64k -movflags +faststart $R/review_720p.mp4
ffmpeg -hide_banner -i $R/full_1080p.mp4 -af ebur128 -f null - 2>&1 | grep -A2 "Integrated loudness" | grep " I:"
ls -l $R/*.mp4
echo FINISHDONE
