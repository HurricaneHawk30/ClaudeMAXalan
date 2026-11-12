#!/bin/bash
# lon lat "countries" "LABEL" "SUB" out [country_label] [end_km] [extra] [center]
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra="$9"} ${10:+--center="${10}"} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"; }
job -3.7081 40.4142 "Spain" "SOBRINO DE BOTÍN" "MADRID, SPAIN" frames_botin "" 300 &
job -105.5450 36.4392 "United States of America" "TAOS PUEBLO" "NEW MEXICO, USA" frames_taos "United States" 300; wait
job -4.9735 34.0646 "Morocco" "AL-QARAWIYYIN" "FEZ, MOROCCO" frames_qarawiyyin "" 300 &
job 138.3617 35.4767 "Japan" "NISHIYAMA ONSEN KEIUNKAN" "YAMANASHI, JAPAN" frames_keiunkan "" 300; wait
job 33.9760 28.5559 "Egypt" "SAINT CATHERINE'S MONASTERY" "SINAI, EGYPT" frames_catherine "" 300 &
job 12.4769 41.8986 "Italy" "THE PANTHEON" "ROME, ITALY" frames_pantheon "" 300; wait
job 103.6073 31.0026 "China" "DUJIANGYAN" "SICHUAN, CHINA" frames_dujiangyan "" 450 &
job 58.6837 34.3529 "Iran" "QANATS OF GONABAD" "KHORASAN, IRAN" frames_qanat "" 450; wait
job 22.9244 37.5925 "Greece" "ARKADIKO BRIDGE" "PELOPONNESE, GREECE" frames_arkadiko "" 200 &
job 35.6481 34.1208 "Lebanon" "BYBLOS" "LEBANON" frames_byblos "" 150; wait
echo MAPS5DONE
