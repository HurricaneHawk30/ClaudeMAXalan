#!/bin/bash
# lon lat "countries" "LABEL" "SUB" out [country_label] [end_km] [extra] [center]
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra="$9"} ${10:+--center="${10}"} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"; }
job 91.5826 25.2975 "India" "MAWSYNRAM" "MEGHALAYA, INDIA" frames_mawsynram "" 300 &
job -71.75 9.45 "Venezuela" "CATATUMBO" "LAKE MARACAIBO, VENEZUELA" frames_catatumbo "" 300; wait
job -116.8667 36.4576 "United States of America" "DEATH VALLEY" "CALIFORNIA, USA" frames_deathvalley "United States" 300 &
job -68.5 -23.5 "Chile" "ATACAMA DESERT" "CHILE" frames_atacama "" 450; wait
job -69.4467 -14.6283 "Peru" "LA RINCONADA" "PUNO, PERU" frames_rinconada "" 300 &
job 142.7858 63.4608 "Russia" "OYMYAKON" "YAKUTIA, RUSSIA" frames_oymyakon "" 1200; wait
job -12.2777 -37.1052 "Saint Helena" "TRISTAN DA CUNHA" "SOUTH ATLANTIC" frames_tristan "South Atlantic Ocean" 150 &
job 30.6086 69.3963 "Russia" "KOLA SUPERDEEP BOREHOLE" "MURMANSK OBLAST, RUSSIA" frames_kola "" 300; wait
job 142.5917 11.3733 "" "CHALLENGER DEEP" "MARIANA TRENCH" frames_challenger "Pacific Ocean" 700 &
job -123.3933 -48.8767 "" "POINT NEMO" "SOUTH PACIFIC" frames_nemo "Pacific Ocean" 3500 "-124.79,-24.68,DUCIE ISLAND;-109.45,-27.20,MOTU NUI;-126.4,-73.0,MAHER ISLAND" "-117,-51"; wait
echo MAPS4DONE
