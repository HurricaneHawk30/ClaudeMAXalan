#!/bin/bash
# lon lat "countries" "LABEL" "SUB" out [country_label] [end_km]
P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" ${7:+--country_label "$7"} ${8:+--end_km $8} 2>&1 | grep -E "frames|Error" | sed "s|^|$6: |"; }
job -5.4743 57.8943 "United Kingdom" "GRUINARD ISLAND" "SCOTLAND" frames_gruinard &
job 114.242 -8.058 "Indonesia" "KAWAH IJEN" "EAST JAVA, INDONESIA" frames_ijen; wait
job 5.40 49.20 "France" "ZONE ROUGE" "VERDUN, FRANCE" frames_zone &
job -62.21 16.71 "Montserrat" "PLYMOUTH" "MONTSERRAT" frames_plymouth "Montserrat" 60; wait
job -76.34 40.80 "United States of America" "CENTRALIA" "PENNSYLVANIA, USA" frames_centralia "United States" &
job 118.33 -22.24 "Australia" "WITTENOOM" "WESTERN AUSTRALIA" frames_wittenoom; wait
job 165.38 11.60 "Marshall Islands" "BIKINI ATOLL" "MARSHALL ISLANDS" frames_bikini "" 200 &
job 60.80 55.68 "Russia" "LAKE KARACHAY" "CHELYABINSK OBLAST, RUSSIA" frames_karachay; wait
job 10.30 6.44 "Cameroon" "LAKE NYOS" "CAMEROON" frames_nyos &
job 29.20 -2.00 "Rwanda,Democratic Republic of the Congo" "LAKE KIVU" "RWANDA / DR CONGO" frames_kivu "Rwanda & DR Congo"; wait
echo MAPSDONE
