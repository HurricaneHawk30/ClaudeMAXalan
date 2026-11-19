#!/bin/bash
# lon lat "countries" "LABEL" "SUB" out [country_label] [end_km] [extra] [center]
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra="$9"} ${10:+--center="${10}"} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"; }
job -70.0700 -32.8300 "Chile" "LOS CARACOLES" "ANDES, CHILE" frames_caracoles "" 300 &
job -111.5000 64.0000 "Canada" "TIBBITT TO CONTWOYTO" "NORTHWEST TERRITORIES, CANADA" frames_ice_road "" 700; wait
job 29.3600 -29.5900 "South Africa" "SANI PASS" "SOUTH AFRICA / LESOTHO" frames_sani_pass "" 250 &
job -149.5000 68.1300 "United States of America" "DALTON HIGHWAY" "ALASKA, USA" frames_dalton "" 700; wait
job 168.6000 -44.9000 "New Zealand" "SKIPPERS CANYON ROAD" "QUEENSTOWN, NEW ZEALAND" frames_skippers "" 250 &
job 75.4700 34.2800 "India" "ZOJI LA" "LADAKH, INDIA" frames_zoji_la "" 300; wait
job 113.5900 35.7300 "China" "GUOLIANG TUNNEL" "HENAN, CHINA" frames_guoliang "" 300 &
job 147.0000 62.0000 "Russia" "KOLYMA HIGHWAY" "SIBERIA, RUSSIA" frames_kolyma "" 1500; wait
job 74.4700 35.4000 "Pakistan" "FAIRY MEADOWS ROAD" "GILGIT-BALTISTAN, PAKISTAN" frames_fairy_meadows "" 300 &
job -67.7900 -16.2800 "Bolivia" "YUNGAS ROAD" "LA PAZ, BOLIVIA" frames_yungas "" 300; wait
echo MAPS13DONE
