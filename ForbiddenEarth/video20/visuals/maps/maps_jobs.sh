#!/bin/bash
# map zooms for video20 (10 places nature took back); frames converted to JPEG q92 right after rendering
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra="$9"} ${10:+--center="${10}"} ${11:+--label_side "${11}"} ${12:+--dashed} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"
  $P -c "import glob,os,sys;from PIL import Image
for f in sorted(glob.glob(sys.argv[1]+'/*.png')): Image.open(f).convert('RGB').save(f[:-4]+'.jpg',quality=92); os.remove(f)" "$6"; }
job -73.9886 41.4553 "United States of America" "BANNERMAN'S CASTLE" "HUDSON RIVER, NEW YORK" frames_bannerman "USA" 120 &
job 151.0790 -33.8360 "Australia" "SS AYRFIELD" "HOMEBUSH BAY, SYDNEY" frames_ayrfield "" 60; wait
job 29.0960 36.5770 "Turkey" "KAYAKÖY" "NEAR FETHIYE, TURKEY" frames_kayakoy "" 150 &
job -87.3365 41.6019 "United States of America" "CITY METHODIST CHURCH" "GARY, INDIANA, USA" frames_city_methodist "USA" 120; wait
job 92.7600 11.6750 "India" "ROSS ISLAND" "ANDAMAN ISLANDS, INDIA" frames_ross_island "BAY OF BENGAL" 300 &
job -55.5000 -3.8300 "Brazil" "FORDLÂNDIA" "PARÁ, BRAZIL" frames_fordlandia "" 7000 "-83.05,42.33,DETROIT" "-69.0,19.0"; wait
job 16.4390 40.3790 "Italy" "CRACO" "BASILICATA, ITALY" frames_craco "" 150 &
job 15.2300 -26.7040 "Namibia" "KOLMANSKOP" "NAMIB DESERT, NAMIBIA" frames_kolmanskop "" 150; wait
job 103.8890 13.4350 "Cambodia" "TA PROHM" "ANGKOR, CAMBODIA" frames_ta_prohm "" 150 &
job 122.8200 30.7300 "China" "HOUTOUWAN" "SHENGSHAN ISLAND, CHINA" frames_houtouwan "" 150; wait
echo MAPS20DONE
