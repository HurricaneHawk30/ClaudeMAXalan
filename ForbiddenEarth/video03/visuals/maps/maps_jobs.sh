#!/bin/bash
# lon lat "countries" "LABEL" "SUB" out [country_label] [end_km] [extra] [center]
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra "$9"} ${10:+--center "${10}"} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"; }
job -112.0063 36.9959 "United States of America" "THE WAVE" "ARIZONA, USA" frames_wave "United States" 300 &
job -119.3317 40.8593 "United States of America" "FLY GEYSER" "NEVADA, USA" frames_flygeyser "United States" 300; wait
job -160.15 21.90 "United States of America" "NIIHAU" "HAWAII, USA" frames_niihau "Hawaii" 120 &
job -20.6042 63.3033 "Iceland" "SURTSEY" "ICELAND" frames_surtsey "" 150; wait
job 1.1683 45.0544 "France" "LASCAUX" "DORDOGNE, FRANCE" frames_lascaux "" 300 &
job 136.7258 34.4553 "Japan" "ISE GRAND SHRINE" "MIE, JAPAN" frames_ise "" 300; wait
job -46.6747 -24.4876 "Brazil" "SNAKE ISLAND" "SÃO PAULO, BRAZIL" frames_snake "" 200 &
job -105.4961 27.8506 "Mexico" "NAICA" "CHIHUAHUA, MEXICO" frames_naica "" 400; wait
job 81.3119 31.0675 "China" "MOUNT KAILASH" "TIBET" frames_kailash "" 350 &
job 109.2536 34.3814 "China" "TOMB OF QIN SHI HUANG" "XI'AN, CHINA" frames_qin "" 400; wait
echo MAPS3DONE
