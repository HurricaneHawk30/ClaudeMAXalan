#!/bin/bash
# map zooms for video19 (10 lost treasures); frames converted to JPEG q92 right after rendering
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra="$9"} ${10:+--center="${10}"} ${11:+--label_side "${11}"} ${12:+--dashed} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"
  $P -c "import glob,os,sys;from PIL import Image
for f in sorted(glob.glob(sys.argv[1]+'/*.png')): Image.open(f).convert('RGB').save(f[:-4]+'.jpg',quality=92); os.remove(f)" "$6"; }
job 0.1900 52.8000 "United Kingdom" "THE WASH" "LINCOLNSHIRE, ENGLAND" frames_king_john "ENGLAND" 90 &
job 28.1880 -25.7460 "South Africa" "PRETORIA" "SOUTH AFRICA" frames_kruger "" 500; wait
job 13.9300 47.6430 "Austria" "LAKE TOPLITZ" "STYRIA, AUSTRIA" frames_toplitz "" 60 &
job -111.3700 33.4300 "United States of America" "SUPERSTITION MOUNTAINS" "ARIZONA, USA" frames_lost_dutchman "USA" 150; wait
job -6.2675 53.3429 "Ireland" "DUBLIN CASTLE" "DUBLIN, IRELAND" frames_irish_jewels "" 120 &
job 98.3000 4.3000 "Indonesia,Malaysia" "STRAIT OF MALACCA" "OFF SUMATRA" frames_flor_de_la_mar "" 700; wait
job 16.2840 50.7710 "Poland" "WALBRZYCH" "LOWER SILESIA, POLAND" frames_gold_train "" 120 &
job -87.0600 5.5300 "Costa Rica" "COCOS ISLAND" "COSTA RICA" frames_cocos_island "PACIFIC OCEAN" 2600 "-77.03,-12.05,LIMA" "-82.0,-3.3"; wait
job -64.3000 44.5130 "Canada" "OAK ISLAND" "NOVA SCOTIA, CANADA" frames_oak_island "CANADA" 150 &
job 20.5100 54.7100 "Russia" "KÖNIGSBERG" "NOW KALININGRAD, RUSSIA" frames_amber_room "BALTIC SEA" 1300 "30.40,59.72,ST PETERSBURG" "25.4,57.3"; wait
echo MAPS19DONE
