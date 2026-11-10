# Сборка видео video02 (visuals)

Python 3.12, ffmpeg. Пакеты: `numpy opencv-python-headless pillow matplotlib cartopy shapely pyproj`.

## 1. Однократная подготовка (не хранится в git)
```bash
mkdir -p fonts && cd fonts
for fam in "Oswald:wght@700" "Inter:wght@500;700;800"; do
  curl -s -A "Mozilla/4.0" "https://fonts.googleapis.com/css2?family=$fam" | grep -oE "https://fonts.gstatic.com/[^)]+"
done | xargs -n1 curl -sO
# переименовать: Oswald-Bold.ttf, Inter-Medium.ttf, Inter-Bold.ttf, Inter-ExtraBold.ttf (fc-scan показывает вес)
cd ../maps
for f in ne_10m_admin_0_countries ne_50m_admin_0_countries ne_10m_lakes; do
  curl -sSL -o $f.geojson "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/$f.geojson"
done
```

## 2. Карта места (глобус → страна → точка, 3.5 с)
```bash
python maps/globe_zoom.py --lon -5.4743 --lat 57.8943 --country "United Kingdom" \
  --label "GRUINARD ISLAND" --sub "SCOTLAND" --out maps/frames_gruinard
```
`--country` — поле ADMIN в Natural Earth, несколько через запятую; `--end_km` — конечный масштаб (для мест вглубь суши 300–450, чтобы были видны границы и берега). Все 10 карт видео: `maps/maps_jobs.sh`, затем `maps/maps_jobs2.sh` (обновлённые). Суша и границы светлые, у глобуса янтарный контур — проверено на ширине 480 px.

## 3. Монтажный план → видео
- `edl_build.py` — план: кадр, время (по `work/words_full.json`, пословные тайминги Whisper), движение камеры, переходы, надписи. `python edl_build.py > edl.json`.
- Полное видео: `./render_full.sh` — 4 сегмента параллельно без звука, склейка, звук стерео; затем громкость двухпроходным loudnorm до −16 LUFS (см. отчёт задачи 3). Кадры с малым разрешением — `inset(...)`: чёткий кадр по центру на размытом фоне из того же снимка. Карточка места — на размытом первом кадре карты. Концовка — `endcard`: логотип и Subscribe в левой половине, центр и правая половина свободны под конечную заставку YouTube.
- `edl_build.py` сам проверяет, что кадр не повторяется чаще чем раз в 120 с и что все файлы на месте.
- `render.py edl.json ../render/preview.mp4` — сборка: цветокоррекция, виньетка, наезды/панорамы, переходы, карточки, подпись внизу. `--stills 12,40` — быстрые контрольные кадры.
- Звук после сборки: `ffmpeg -i in.mp4 -c:v copy -af "loudnorm=I=-16:TP=-1.5:LRA=11" -ac 2 -c:a aac -b:a 192k out.mp4`.
- `make_credits.py edl.json credits.txt ../render/contact_sheet_full.jpg credits_compact.txt` — полные кредиты, сетка кадров (с картами), `credits_compact.txt` (строка на кадр) и `credits_youtube.txt` (короткая версия для описания); падает, если у кадра неподходящая лицензия (разрешены PD, CC0, CC BY, CC BY-SA, OGL v3.0).

## Исходники
`src/*.jpg|png` — кадры (копии Wikimedia Commons шириной до 1920 px и NASA Image Library), рядом `*.json` с названием, автором, лицензией и ссылкой. Wikimedia ограничивает скачивание оригиналов: берите превью стандартных размеров (1920/1280/960).

Для новых разделов: добавить кадры в `src/` с метаданными, дописать шоты в `edl_build.py`, нарисовать карту, собрать.

## Отличия video02
- Карты: `maps/maps_jobs.sh`; `globe_zoom.py` умеет дополнительные точки (`--extra "lon,lat,ПОДПИСЬ"`, у правого края подпись слева от точки) и центр финального вида (`--center lon,lat`), страну можно не выделять (`--country ""`) — так сделаны карта Мохенджо-Даро с Хараппой и карта Средиземноморья для Атлантиды.
- `render.py`: поворот кадра (`move` с `rot0`/`rot1`, градусы) на размытом фоне из того же кадра — так повёрнута карта Кирхера; на карточке вместо номера может быть слово (ATLANTIS).
- `make_credits.py` сам сжимает `credits_youtube.txt` до лимита `YT_LIMIT` (по умолчанию 3800 символов).
