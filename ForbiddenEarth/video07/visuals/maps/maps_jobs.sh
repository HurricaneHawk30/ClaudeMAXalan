#!/bin/bash
# lon lat "countries" "LABEL" "SUB" out [country_label] [end_km] [extra] [center]
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra="$9"} ${10:+--center="${10}"} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"; }
job -142.8889 61.4864 "United States of America" "KENNECOTT" "ALASKA, USA" frames_kennecott "United States" 450 &
job 16.3233 78.6553 "Norway" "PYRAMIDEN" "SVALBARD, NORWAY" frames_pyramiden "" 300; wait
job 129.7383 32.6278 "Japan" "HASHIMA ISLAND" "NAGASAKI, JAPAN" frames_hashima "" 150 &
job -3.6550 50.2367 "United Kingdom" "HALLSANDS" "DEVON, ENGLAND" frames_hallsands "" 150; wait
job -2.1661 50.6219 "United Kingdom" "TYNEHAM" "DORSET, ENGLAND" frames_tyneham "" 150 &
job -72.7086 -42.9167 "Chile" "CHAITÉN" "LOS LAGOS, CHILE" frames_chaiten "" 300; wait
job -90.6050 38.5072 "United States of America" "TIMES BEACH" "MISSOURI, USA" frames_times_beach "United States" 300 &
job -62.8169 -37.1336 "Argentina" "VILLA EPECUÉN" "BUENOS AIRES, ARGENTINA" frames_epecuen "" 300; wait
job 141.0233 37.4500 "Japan" "FUTABA" "FUKUSHIMA, JAPAN" frames_futaba "" 300 &
job 30.0569 51.4050 "Ukraine" "PRIPYAT" "KYIV OBLAST, UKRAINE" frames_pripyat "" 300; wait
echo MAPS7DONE
