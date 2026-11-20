#!/bin/bash
# lon lat "countries" "LABEL" "SUB" out [country_label] [end_km] [extra] [center]
# frames are converted to JPEG (q92) right after rendering to save disk
cd "$(dirname "$0")"; P=/home/user/kvenv12/bin/python
job(){ rm -rf "$6"; $P globe_zoom.py --lon "$1" --lat "$2" --country "$3" --label "$4" --sub "$5" --out "$6" \
  ${7:+--country_label "$7"} ${8:+--end_km $8} ${9:+--extra="$9"} ${10:+--center="${10}"} ${11:+--label_side "${11}"} 2>&1 | grep -E "frames|Error|Trace" | sed "s|^|$6: |"
  $P -c "import glob,os,sys;from PIL import Image
for f in sorted(glob.glob(sys.argv[1]+'/*.png')): Image.open(f).convert('RGB').save(f[:-4]+'.jpg',quality=92); os.remove(f)" "$6"; }
job 138.7274 35.3606 "Japan" "MOUNT FUJI" "HONSHU, JAPAN" frames_fuji "" 200 "139.69,35.69,TOKYO" "139.2,35.5" &
job -121.7603 46.8523 "United States of America" "MOUNT RAINIER" "WASHINGTON, USA" frames_rainier "" 250 "-122.33,47.61,SEATTLE" "-122.05,47.25"; wait
job 120.9980 14.0020 "Philippines" "TAAL VOLCANO" "LUZON, PHILIPPINES" frames_taal "" 200 "120.98,14.60,MANILA" "121.0,14.3" &
job 14.9990 37.7510 "Italy" "MOUNT ETNA" "SICILY, ITALY" frames_etna "" 200 "15.087,37.502,CATANIA" "15.04,37.63"; wait
job 29.2500 -1.5200 "Democratic Republic of the Congo" "NYIRAGONGO" "NORTH KIVU, DR CONGO" frames_nyiragongo "DR CONGO" 120 "29.22,-1.68,GOMA" "29.24,-1.60" &
job 130.6570 31.5850 "Japan" "SAKURAJIMA" "KAGOSHIMA, JAPAN" frames_sakurajima "" 110 "130.557,31.596,KAGOSHIMA" "130.61,31.59"; wait
job -22.3900 63.8800 "Iceland" "REYKJANES PENINSULA" "SOUTHWEST ICELAND" frames_reykjanes "" 200 "-22.43,63.84,GRINDAVÍK" "-22.4,63.86" &
job 110.4460 -7.5420 "Indonesia" "MOUNT MERAPI" "JAVA, INDONESIA" frames_merapi "" 200 "110.365,-7.797,YOGYAKARTA" "110.40,-7.67"; wait
job -98.6220 19.0230 "Mexico" "POPOCATÉPETL" "PUEBLA / MEXICO STATE, MEXICO" frames_popocatepetl "" 250 "-99.13,19.43,MEXICO CITY;-98.20,19.04,PUEBLA" "-98.67,19.15" below &
job 14.1390 40.8270 "Italy" "CAMPI FLEGREI" "NAPLES, ITALY" frames_campi_flegrei "" 80 "14.25,40.85,NAPLES" "14.19,40.84"; wait
echo MAPS15DONE
