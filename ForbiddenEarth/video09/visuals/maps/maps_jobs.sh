#!/bin/bash
# lon lat "countries" "LABEL" "SUB" out [country_label] [end_km] [extra] [center]
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra="$9"} ${10:+--center="${10}"} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"; }
job -75.0000 15.5000 "" "MANCHINEEL TREE" "THE CARIBBEAN" frames_manchineel "Caribbean Sea" 1400 &
job 36.0200 -2.4200 "Tanzania" "LAKE NATRON" "TANZANIA" frames_natron "" 300; wait
job -159.5933 22.1795 "United States of America" "HANAKAPIAI BEACH" "KAUAI, HAWAII" frames_hanakapiai "Hawaii" 200 &
job 110.0827 34.4776 "China" "MOUNT HUA" "SHAANXI, CHINA" frames_hua "" 450; wait
job 25.8517 -17.9244 "Zambia" "DEVIL'S POOL" "VICTORIA FALLS, ZAMBIA" frames_devils_pool "" 300 &
job -16.3300 64.1000 "Iceland" "ICE CAVES" "VATNAJÖKULL, ICELAND" frames_ice_caves "" 250; wait
job -111.3740 36.8620 "United States of America" "ANTELOPE CANYON" "PAGE, ARIZONA" frames_antelope "Arizona" 300 &
job -98.1262 30.0344 "United States of America" "JACOB'S WELL" "WIMBERLEY, TEXAS" frames_jacobs_well "Texas" 300; wait
job -110.8381 44.5251 "United States of America" "YELLOWSTONE" "WYOMING, USA" frames_yellowstone "Wyoming" 300 &
job 34.5375 28.5719 "Egypt" "BLUE HOLE" "DAHAB, EGYPT" frames_blue_hole "" 300; wait
echo MAPS9DONE
