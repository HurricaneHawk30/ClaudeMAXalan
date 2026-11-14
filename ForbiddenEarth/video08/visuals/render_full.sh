#!/bin/bash
# Full render: 4 video-only segments in parallel; then work/finish.sh (concat, -16 LUFS narration, chat copy, 720p review)
cd "$(dirname "$0")"
P=/home/user/kvenv12/bin/python
B=(0 161 323 484 645.3)
mkdir -p work/seg ../render
for i in 0 1 2 3; do
  $P render.py edl.json work/seg/seg$i.mp4 --from ${B[$i]} --to ${B[$((i+1))]} --noaudio > work/seg/seg$i.log 2>&1 &
done
wait
bash work/finish.sh
