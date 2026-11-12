#!/bin/bash
# lon lat "countries" "LABEL" "SUB" out [country_label] [end_km] [extra] [center]
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra="$9"} ${10:+--center="${10}"} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"; }
job 29.1205 37.9211 "Turkey" "PAMUKKALE" "DENIZLI, TURKEY" frames_pamukkale "" 300 &
job 100.0700 38.9200 "China" "ZHANGYE DANXIA" "GANSU, CHINA" frames_danxia "" 450; wait
job -119.5509 49.0783 "Canada" "SPOTTED LAKE" "BRITISH COLUMBIA, CANADA" frames_spotted "" 300 &
job 15.2955 -24.7593 "Namibia" "DEADVLEI" "NAMIB DESERT, NAMIBIA" frames_deadvlei "" 300; wait
job 53.8237 12.4634 "Yemen" "SOCOTRA" "YEMEN" frames_socotra "" 300 &
job -67.4891 -20.1338 "Bolivia" "SALAR DE UYUNI" "BOLIVIA" frames_uyuni "" 300; wait
job -11.4019 21.1240 "Mauritania" "RICHAT STRUCTURE" "MAURITANIA" frames_richat "" 450 &
job -6.5833 37.6833 "Spain" "RIO TINTO" "ANDALUSIA, SPAIN" frames_riotinto "" 300; wait
job -89.6667 75.3833 "Canada" "DEVON ISLAND" "NUNAVUT, CANADA" frames_devon "" 450 &
job 40.3000 14.2417 "Ethiopia" "DALLOL" "DANAKIL DEPRESSION, ETHIOPIA" frames_dallol "" 300; wait
echo MAPS6DONE
