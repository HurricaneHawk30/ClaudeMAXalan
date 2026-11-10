#!/bin/bash
P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" ${7:+--country_label "$7"} ${8:+--end_km $8} 2>&1 | grep -E "frames|Error" | sed "s|^|$6: |"; }
job 29.20 -2.00 "Rwanda,Democratic Republic of the Congo" "LAKE KIVU" "RWANDA / DR CONGO" frames_kivu "Rwanda & DR Congo" 150 &
job -76.34 40.80 "United States of America" "CENTRALIA" "PENNSYLVANIA, USA" frames_centralia "United States" 300; wait
job 5.40 49.20 "France" "ZONE ROUGE" "VERDUN, FRANCE" frames_zone "" 300 &
job 60.80 55.68 "Russia" "LAKE KARACHAY" "CHELYABINSK OBLAST, RUSSIA" frames_karachay "" 350; wait
job 10.30 6.44 "Cameroon" "LAKE NYOS" "CAMEROON" frames_nyos "" 350 &
job 118.33 -22.24 "Australia" "WITTENOOM" "WESTERN AUSTRALIA" frames_wittenoom "" 450; wait
echo MAPSDONE2
