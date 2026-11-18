#!/bin/bash
# lon lat "countries" "LABEL" "SUB" out [country_label] [end_km] [extra] [center]
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra="$9"} ${10:+--center="${10}"} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"; }
job 17.7432 49.5467 "Czechia" "HRANICE ABYSS" "CZECH REPUBLIC" frames_hranice "" 250 &
job 83.9497 28.4950 "Nepal" "MACHAPUCHARE" "ANNAPURNA, NEPAL" frames_machapuchare "" 300; wait
job -88.2000 18.5500 "Mexico" "TAAM JA' BLUE HOLE" "CHETUMAL BAY, MEXICO" frames_taam_ja "" 250 &
job -106.7500 -75.5000 "Antarctica" "THWAITES GLACIER" "WEST ANTARCTICA" frames_thwaites "" 2200; wait
job 98.6833 28.4333 "China" "KAWAGARBO" "YUNNAN, CHINA" frames_kawagarbo "" 400 &
job 99.4000 -66.7500 "Antarctica" "DENMAN CANYON" "EAST ANTARCTICA" frames_denman "" 2200; wait
job -98.1636 22.9944 "Mexico" "EL ZACATÓN" "TAMAULIPAS, MEXICO" frames_zacaton "" 300 &
job 77.0000 -80.5000 "Antarctica" "GAMBURTSEV MOUNTAINS" "EAST ANTARCTICA" frames_gamburtsev "" 2500; wait
job 90.4570 28.0470 "Bhutan" "GANGKHAR PUENSUM" "BHUTAN" frames_gangkhar "" 250 &
job -150.0000 0.0000 "" "THE DEEP SEAFLOOR" "MOST OF OUR PLANET" frames_deep_seafloor "Pacific Ocean" 9000; wait
echo MAPS12DONE
