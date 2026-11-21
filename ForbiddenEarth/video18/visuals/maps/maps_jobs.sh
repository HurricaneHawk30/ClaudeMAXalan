#!/bin/bash
# map zooms for video18 (15 places); frames converted to JPEG q92 right after rendering
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra="$9"} ${10:+--center="${10}"} ${11:+--label_side "${11}"} ${12:+--dashed} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"
  $P -c "import glob,os,sys;from PIL import Image
for f in sorted(glob.glob(sys.argv[1]+'/*.png')): Image.open(f).convert('RGB').save(f[:-4]+'.jpg',quality=92); os.remove(f)" "$6"; }
job 24.3300 40.1600 "Greece" "MOUNT ATHOS" "GREECE" frames_athos "" 220 &
job 135.4875 34.5641 "Japan" "DAISEN KOFUN" "SAKAI, JAPAN" frames_daisen "" 80 "135.50,34.69,OSAKA" "135.49,34.62"; wait
job 90.2500 40.3000 "China" "LOP NUR" "XINJIANG, CHINA" frames_lop_nur "" 700 &
job -1.6900 51.1300 "United Kingdom" "PORTON DOWN" "WILTSHIRE, ENGLAND" frames_porton_down "ENGLAND" 60 "-1.795,51.069,SALISBURY" "-1.74,51.10"; wait
job -1.6900 54.0100 "United Kingdom" "RAF MENWITH HILL" "NORTH YORKSHIRE, ENGLAND" frames_menwith_hill "ENGLAND" 120 "-1.54,53.99,HARROGATE" "-1.62,54.00" &
job 133.7370 -23.7990 "Australia" "PINE GAP" "NORTHERN TERRITORY, AUSTRALIA" frames_pine_gap "" 80 "133.88,-23.70,ALICE SPRINGS" "133.81,-23.75"; wait
job 72.4200 -7.3100 "British Indian Ocean Territory" "DIEGO GARCIA" "CHAGOS ISLANDS" frames_diego_garcia "INDIAN OCEAN" 900 &
job 108.7500 48.7600 "Mongolia" "BURKHAN KHALDUN" "KHENTII, MONGOLIA" frames_great_taboo "" 350 "106.92,47.92,ULAANBAATAR" "107.8,48.35"; wait
job 37.6200 55.7500 "Russia" "METRO-2" "MOSCOW, RUSSIA" frames_metro2 "RUSSIA" 120 &
job 58.2600 54.2500 "Russia" "MOUNT YAMANTAU" "SOUTHERN URALS, RUSSIA" frames_yamantau "RUSSIA" 120 "57.80,54.06,MEZHGORYE" "58.02,54.15"; wait
job 12.4530 41.9040 "Vatican,Italy" "VATICAN APOSTOLIC ARCHIVE" "VATICAN CITY" frames_vatican_archive "ITALY" 30 &
job -0.0886 51.5140 "United Kingdom" "BANK OF ENGLAND" "LONDON, ENGLAND" frames_bank_of_england "ENGLAND" 40; wait
job 38.7200 14.1300 "Ethiopia" "AKSUM" "TIGRAY, ETHIOPIA" frames_chapel_of_tablet "" 300 &
job 126.6800 37.9500 "South Korea,North Korea" "KOREAN DMZ" "KOREAN PENINSULA" frames_korean_dmz "KOREA" 450 "126.98,37.57,SEOUL" "127.0,38.2"; wait
job -85.9700 37.8800 "United States of America" "FORT KNOX" "KENTUCKY, USA" frames_fort_knox "USA" 200 "-85.76,38.25,LOUISVILLE" "-85.88,38.05"; wait
echo MAPS18DONE
