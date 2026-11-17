#!/bin/bash
# lon lat "countries" "LABEL" "SUB" out [country_label] [end_km] [extra] [center]
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra="$9"} ${10:+--center="${10}"} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"; }
job -84.3352 33.8746 "United States of America" "CRYPT OF CIVILIZATION" "ATLANTA, GEORGIA, USA" frames_crypt "Georgia" 300 &
job -103.4591 43.8791 "United States of America" "HALL OF RECORDS" "MOUNT RUSHMORE, SOUTH DAKOTA" frames_hall_of_records "South Dakota" 300; wait
job 15.4911 78.2357 "Norway" "SEED VAULT" "SVALBARD, NORWAY" frames_seed_vault "Svalbard" 400 &
job 28.5600 43.8250 "Romania" "MOVILE CAVE" "MANGALIA, ROMANIA" frames_movile "" 250; wait
job 4.4161 44.3876 "France" "CHAUVET CAVE" "ARDÈCHE, FRANCE" frames_chauvet "" 250 &
job 162.3500 11.5500 "Marshall Islands" "RUNIT DOME" "ENEWETAK ATOLL, MARSHALL ISLANDS" frames_runit "Pacific Ocean" 600; wait
job 106.0000 -77.5000 "Antarctica" "LAKE VOSTOK" "ANTARCTICA" frames_vostok "" 2500 &
job 21.4400 61.2370 "Finland" "ONKALO" "OLKILUOTO, FINLAND" frames_onkalo "" 300; wait
job 14.3470 40.8090 "Italy" "VILLA OF THE PAPYRI" "HERCULANEUM, ITALY" frames_papyri "" 250 &
job 31.1342 29.9792 "Egypt" "THE GREAT PYRAMID" "GIZA, EGYPT" frames_great_pyramid "" 300; wait
echo MAPS11DONE
