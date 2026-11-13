#!/bin/bash
# Full render: 4 video-only segments in parallel -> concat -> mux narration (stereo, -16 LUFS)
cd "$(dirname "$0")"
P=/home/user/kvenv12/bin/python
B=(0 176 352 527 701.8)
for i in 0 1 2 3; do
  $P render.py edl.json work/seg/seg$i.mp4 --from ${B[$i]} --to ${B[$((i+1))]} --noaudio > work/seg/seg$i.log 2>&1 &
done
wait
printf "file 'seg0.mp4'\nfile 'seg1.mp4'\nfile 'seg2.mp4'\nfile 'seg3.mp4'\n" > work/seg/list.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i work/seg/list.txt -i ../voice/full.mp3 -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,afade=t=out:st=701.0:d=0.8" -ac 2 -c:a aac -b:a 192k \
  -t 701.8 -movflags +faststart ../render/full_1080p.mp4
echo RENDERDONE
