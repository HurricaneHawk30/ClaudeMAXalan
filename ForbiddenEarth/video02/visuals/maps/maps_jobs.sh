#!/bin/bash
# lon lat "countries" "LABEL" "SUB" out [country_label] [end_km] [extra] [center]
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra "$9"} ${10:+--center "${10}"} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"; }
job -3.3416 59.0487 "United Kingdom" "SKARA BRAE" "ORKNEY, SCOTLAND" frames_skara "" 120 &
job -108.4734 37.1677 "United States of America" "CLIFF PALACE" "COLORADO, USA" frames_cliff "United States" 300; wait
job 34.7351 38.3735 "Turkey" "DERINKUYU" "CAPPADOCIA, TURKEY" frames_derinkuyu "" 300 &
job 68.1357 27.3243 "Pakistan" "MOHENJO-DARO" "SINDH, PAKISTAN" frames_mohenjo "" 520 "72.8636,30.6305,HARAPPA" "70.4,29.0"; wait
job 35.4444 30.3285 "Jordan" "PETRA" "JORDAN" frames_petra "" 200 &
job 14.4847 40.7491 "Italy" "POMPEII" "CAMPANIA, ITALY" frames_pompeii "" 150; wait
job -72.5450 -13.1631 "Peru" "MACHU PICCHU" "CUSCO, PERU" frames_machu "" 300 &
job 53.6478 18.2567 "Oman" "UBAR (SHISR)" "DHOFAR, OMAN" frames_ubar "" 300; wait
job -89.45 18.55 "Mexico" "VALERIANA" "CAMPECHE, MEXICO" frames_valeriana "" 300 &
job 26.2389 39.9575 "Turkey" "TROY" "HISARLIK, TURKEY" frames_troy "" 200; wait
job -5.60 36.00 "" "GIBRALTAR" "PILLARS OF HERACLES" frames_atlantis "Mediterranean Sea" 1300 "25.40,36.40,SANTORINI" "10.0,37.5"
echo MAPS2DONE
