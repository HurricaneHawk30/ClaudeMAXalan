# Сборка видео video01 (visuals)

Python 3.12, ffmpeg. Пакеты: `numpy opencv-python-headless pillow matplotlib cartopy shapely pyproj`.

## 1. Однократная подготовка (не хранится в git)
```bash
mkdir -p fonts && cd fonts
for fam in "Oswald:wght@700" "Inter:wght@500;700;800"; do
  curl -s -A "Mozilla/4.0" "https://fonts.googleapis.com/css2?family=$fam" | grep -oE "https://fonts.gstatic.com/[^)]+"
done | xargs -n1 curl -sO
# переименовать: Oswald-Bold.ttf, Inter-Medium.ttf, Inter-Bold.ttf, Inter-ExtraBold.ttf (fc-scan показывает вес)
cd ../maps
for f in ne_10m_admin_0_countries ne_50m_admin_0_countries; do
  curl -sSL -o $f.geojson "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/$f.geojson"
done
```

## 2. Карта места (глобус → страна → точка, 3.5 с)
```bash
python maps/globe_zoom.py --lon -5.4743 --lat 57.8943 --country "United Kingdom" \
  --label "GRUINARD ISLAND" --sub "SCOTLAND" --out maps/frames_gruinard
```
`--country` — поле ADMIN в Natural Earth.

## 3. Монтажный план → видео
- `edl_build.py` — план: кадр, время (по `work/words.json`, пословные тайминги Whisper), движение камеры, переходы, надписи. `python edl_build.py > edl.json`.
- `render.py edl.json ../render/preview.mp4` — сборка: цветокоррекция, виньетка, наезды/панорамы, переходы, карточки, подпись внизу. `--stills 12,40` — быстрые контрольные кадры.
- Звук после сборки: `ffmpeg -i in.mp4 -c:v copy -af "loudnorm=I=-16:TP=-1.5:LRA=11" -ac 2 -c:a aac -b:a 192k out.mp4`.
- `make_credits.py edl.json credits.txt ../render/contact_sheet.jpg` — кредиты и сетка кадров из использованных файлов; падает, если у кадра неподходящая лицензия.

## Исходники
`src/*.jpg|png` — кадры (копии Wikimedia Commons шириной до 1920 px), рядом `*.json` с названием, автором, лицензией и ссылкой. Wikimedia ограничивает скачивание оригиналов: берите превью стандартных размеров (1920/1280/960).

Для новых разделов: добавить кадры в `src/` с метаданными, дописать шоты в `edl_build.py`, нарисовать карту, собрать.
