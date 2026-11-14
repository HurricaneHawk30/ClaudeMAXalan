#!/bin/bash
# lon lat "countries" "LABEL" "SUB" out [country_label] [end_km] [extra] [center]
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra="$9"} ${10:+--center="${10}"} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"; }
job 14.4775 53.2142 "Poland" "CROOKED FOREST" "GRYFINO, POLAND" frames_crooked "" 300 &
job -6.3417 56.4319 "United Kingdom" "FINGAL'S CAVE" "STAFFA, SCOTLAND" frames_fingal "" 200; wait
job 123.2030 -34.0951 "Australia" "LAKE HILLIER" "WESTERN AUSTRALIA" frames_hillier "" 450 &
job 121.8200 -8.7700 "Indonesia" "KELIMUTU" "FLORES, INDONESIA" frames_kelimutu "" 450; wait
job -72.6200 -46.6450 "Chile" "MARBLE CAVES" "PATAGONIA, CHILE" frames_marble "" 450 &
job 134.3770 7.1610 "Palau" "JELLYFISH LAKE" "PALAU" frames_jellyfish "Pacific Ocean" 300; wait
job -105.5640 20.7020 "Mexico" "HIDDEN BEACH" "MARIETA ISLANDS, MEXICO" frames_hidden_beach "" 300 &
job -65.4440 18.0960 "United States of America" "MOSQUITO BAY" "VIEQUES, PUERTO RICO" frames_mosquito_bay "Puerto Rico" 200; wait
job -73.7860 2.2650 "Colombia" "CAÑO CRISTALES" "META, COLOMBIA" frames_cano_cristales "" 450 &
job 106.2870 17.4560 "Vietnam" "HANG SON DOONG" "QUANG BINH, VIETNAM" frames_son_doong "" 300; wait
echo MAPS8DONE
