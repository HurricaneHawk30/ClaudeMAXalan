#!/bin/bash
# lon lat "countries" "LABEL" "SUB" out [country_label] [end_km] [extra] [center]
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra="$9"} ${10:+--center="${10}"} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"; }
job 119.1700 29.0300 "China" "LONGYOU CAVES" "ZHEJIANG, CHINA" frames_longyou "" 300 &
job -3.0800 47.5900 "France" "CARNAC STONES" "BRITTANY, FRANCE" frames_carnac "" 300; wait
job -71.9820 -13.5090 "Peru" "SACSAYHUAMÁN" "CUSCO, PERU" frames_sacsayhuaman "" 300 &
job 103.1500 19.4300 "Laos" "PLAIN OF JARS" "XIENG KHOUANG, LAOS" frames_plain_of_jars "" 300; wait
job 123.0100 24.4350 "Japan" "YONAGUNI MONUMENT" "OKINAWA, JAPAN" frames_yonaguni "" 400 &
job 158.3350 6.8440 "Micronesia" "NAN MADOL" "POHNPEI, MICRONESIA" frames_nan_madol "" 400; wait
job -75.1300 -14.7350 "Peru" "NAZCA LINES" "ICA, PERU" frames_nazca "" 300 &
job 36.2040 34.0070 "Lebanon" "BAALBEK" "BEKAA VALLEY, LEBANON" frames_baalbek "" 250; wait
job -1.8262 51.1789 "United Kingdom" "STONEHENGE" "WILTSHIRE, ENGLAND" frames_stonehenge "" 600 "-3.70,57.50,ALTAR STONE FROM NE SCOTLAND" "-2.6,54.3" &
job 38.9224 37.2231 "Turkey" "GÖBEKLI TEPE" "ŞANLIURFA, TURKEY" frames_gobekli_tepe "" 300; wait
echo MAPS14DONE
