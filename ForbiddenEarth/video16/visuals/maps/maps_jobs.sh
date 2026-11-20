#!/bin/bash
# map zooms for video16; frames converted to JPEG q92 right after rendering
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra="$9"} ${10:+--center="${10}"} ${11:+--label_side "${11}"} ${12:+--dashed} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"
  $P -c "import glob,os,sys;from PIL import Image
for f in sorted(glob.glob(sys.argv[1]+'/*.png')): Image.open(f).convert('RGB').save(f[:-4]+'.jpg',quality=92); os.remove(f)" "$6"; }
job -2.8990 53.5560 "United Kingdom" "ARGLETON" "WEST LANCASHIRE, ENGLAND" frames_argleton "ENGLAND" 120 "" "" "" 1 &
job -74.7790 42.1028 "United States of America" "AGLOE" "NEW YORK, USA" frames_agloe "USA" 200 "" "" "" 1; wait
job -14.5000 51.4000 "Ireland" "HY-BRASIL" "ATLANTIC OCEAN" frames_hy_brasil "IRELAND" 700 "" "-11.5,52.5" "" 1 &
job 140.0000 77.6000 "Russia" "SANNIKOV LAND" "ARCTIC OCEAN" frames_sannikov_land "RUSSIA" 900 "149.5,76.73,BENNETT ISLAND" "143.5,76.5" "" 1; wait
job 159.9300 -19.2200 "New Caledonia" "SANDY ISLAND" "CORAL SEA" frames_sandy_island "NEW CALEDONIA" 1600 "" "159.5,-22.0" "" 1 &
job -91.3700 22.5500 "Mexico" "BERMEJA" "GULF OF MEXICO" frames_bermeja "MEXICO" 700 "-89.62,20.97,MÉRIDA" "-90.6,21.8" "" 1; wait
job -61.1300 77.1800 "Greenland" "CAMP CENTURY" "NORTHWEST GREENLAND" frames_camp_century "" 600 "" "" "" "" &
job 30.0650 51.3050 "Ukraine" "DUGA RADAR" "CHERNOBYL ZONE, UKRAINE" frames_duga "" 220 "30.52,50.45,KYIV" "30.3,50.9"; wait
job 43.3200 54.9300 "Russia" "SAROV" "NIZHNY NOVGOROD REGION, RUSSIA" frames_sarov "" 700 "37.62,55.75,MOSCOW" "40.5,55.3" &
job -115.8100 37.2400 "United States of America" "AREA 51" "NEVADA, USA" frames_area_51 "USA" 320 "-115.14,36.17,LAS VEGAS" "-115.45,36.75"; wait
echo MAPS16DONE
