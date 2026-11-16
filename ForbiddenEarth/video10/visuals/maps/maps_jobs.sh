#!/bin/bash
# lon lat "countries" "LABEL" "SUB" out [country_label] [end_km] [extra] [center]
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra="$9"} ${10:+--center="${10}"} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"; }
job -10.5389 51.7711 "Ireland" "SKELLIG MICHAEL" "COUNTY KERRY, IRELAND" frames_skellig "" 200 &
job -128.3300 -24.3700 "Pitcairn Islands" "HENDERSON ISLAND" "PITCAIRN ISLANDS" frames_henderson "South Pacific" 600; wait
job 159.2525 -31.7536 "Australia" "BALL'S PYRAMID" "LORD HOWE ISLAND, AUSTRALIA" frames_balls_pyramid "Tasman Sea" 300 &
job 12.3307 45.3818 "Italy" "POVEGLIA" "VENETIAN LAGOON, ITALY" frames_poveglia "" 150; wait
job -123.0017 37.6989 "United States of America" "FARALLON ISLANDS" "SAN FRANCISCO, USA" frames_farallon "California" 200 &
job 73.5167 -53.1000 "Heard Island and McDonald Islands" "HEARD ISLAND" "AUSTRALIA" frames_heard "Southern Ocean" 800; wait
job 3.4000 -54.4200 "" "BOUVET ISLAND" "NORWAY" frames_bouvet "South Atlantic" 1500 &
job -109.2167 10.3000 "Clipperton Island" "CLIPPERTON ISLAND" "FRANCE" frames_clipperton "Pacific Ocean" 1000; wait
job 59.3000 45.1500 "Kazakhstan,Uzbekistan" "VOZROZHDENIYA" "ARAL SEA" frames_vozrozhdeniya "Aral Sea" 400 &
job 92.2350 11.5550 "India" "NORTH SENTINEL" "ANDAMAN ISLANDS, INDIA" frames_north_sentinel "Andaman Islands" 300; wait
echo MAPS10DONE
