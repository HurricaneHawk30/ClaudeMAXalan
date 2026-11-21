#!/bin/bash
# map zooms for video17; frames converted to JPEG q92 right after rendering
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra="$9"} ${10:+--center="${10}"} ${11:+--label_side "${11}"} ${12:+--dashed} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"
  $P -c "import glob,os,sys;from PIL import Image
for f in sorted(glob.glob(sys.argv[1]+'/*.png')): Image.open(f).convert('RGB').save(f[:-4]+'.jpg',quality=92); os.remove(f)" "$6"; }
job -113.7200 48.7600 "United States of America" "GLACIER NATIONAL PARK" "MONTANA, USA" frames_glacier_np "USA" 300 "" "" "" "" &
job 37.3550 -3.0660 "United Republic of Tanzania" "KILIMANJARO" "TANZANIA" frames_kilimanjaro "TANZANIA" 250; wait
job 60.0000 45.0000 "Kazakhstan,Uzbekistan" "ARAL SEA" "KAZAKHSTAN / UZBEKISTAN" frames_aral_sea "CENTRAL ASIA" 700 &
job 35.5000 31.5000 "Israel,Jordan,Palestine" "DEAD SEA" "MIDDLE EAST" frames_dead_sea "MIDDLE EAST" 220; wait
job 12.3350 45.4370 "Italy" "VENICE" "ITALY" frames_venice "" 120 &
job 147.7000 -18.3000 "Australia" "GREAT BARRIER REEF" "QUEENSLAND, AUSTRALIA" frames_great_barrier_reef "" 1300; wait
job -90.4700 29.4000 "United States of America" "ISLE DE JEAN CHARLES" "LOUISIANA, USA" frames_isle_de_jean_charles "USA" 160 "-90.07,29.95,NEW ORLEANS" "-90.3,29.65" &
job 106.8500 -6.1300 "Indonesia" "JAKARTA" "INDONESIA" frames_jakarta "" 1600 "116.70,-0.97,NUSANTARA" "111.5,-3.5"; wait
job 7.8200 46.4200 "Switzerland" "BLATTEN" "VALAIS, SWITZERLAND" frames_blatten "" 100 &
job 179.1900 -8.5200 "Tuvalu" "TUVALU" "FUNAFUTI" frames_tuvalu "" 4500 "151.21,-33.87,SYDNEY" "166.0,-20.0"; wait
echo MAPS17DONE
