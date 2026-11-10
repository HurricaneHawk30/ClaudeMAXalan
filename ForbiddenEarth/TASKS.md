# Задачи Forbidden Earth

Порядок работы описан в `README.md`. Берётся первая задача со статусом `TODO`.

## 1. Сохранить готовую озвучку video01 — DONE

Всё, что уже сделано для первого видео (озвучка из 12 разделов, `full.mp3`, `timings.txt`, `changes.txt`, `script_original.txt`, `script_tts.txt`, `voice_build.py`), перенеси в эту ветку:
- `ForbiddenEarth/video01/voice/` — mp3, `timings.txt`, `changes.txt`, `script_tts.txt`;
- `ForbiddenEarth/video01/script/` — `script_original.txt`, `voice_build.py`.

Если файлы лежат в другой папке или на другой ветке, просто скопируй их сюда. Закоммить и запушь.

**Отчёт.** Перенесено из облачной папки `~/ForbiddenEarth/video01`:
- `video01/voice/` — 12 разделов `00_hook.mp3`…`11_outro.mp3` и `full.mp3` (Kokoro `am_michael`, 0.95, 192 kbps, 44.1 кГц), `timings.txt` (общая длина 10:37.6), `changes.txt` (числа → слова и фонемы имён), `script_tts.txt`.
- `video01/script/` — `script_original.txt`, `voice_build.py`. Пересборка: `python voice_build.py script_original.txt ../voice` (нужны `kokoro`, `soundfile`, ffmpeg, Python 3.10–3.12).
- Проверить на слух: 08:10 «600 roentgens» — Kokoro читает «RENT-gens», Whisper распознал как «retcons».

## 2. Пробный фрагмент видео: вступление и №10 — DONE

Разделы `00_hook` и `01_gruinard` (00:00–01:32.5 по `timings.txt`) под готовую озвучку. Рабочая папка: `ForbiddenEarth/video01/visuals/`.

Источники кадров (только эти):
1. Wikimedia Commons: Public Domain, CC0, CC BY, CC BY-SA. Без NC и ND.
2. NASA, USGS и другие госсайты США: общественное достояние, включая архивные кадры.
3. Карты рисуются кодом по данным Natural Earth.
Если сайт заблокирован сетью облака, поставь статус `BLOCKED` и напиши, какой адрес нужно разрешить.

Нельзя: тела, жертвы, мёртвые животные, водяные знаки, картинки с непонятной лицензией, чужие видео с YouTube.

Стиль:
- Тёмный документальный тон, единая цветокоррекция, лёгкая виньетка.
- Каждый кадр 5–8 секунд с медленным наездом или панорамой, мягкие переходы.
- Вступление: быстрая смена кадров из разных мест подборки под текст хука, в конце надпись FORBIDDEN EARTH.
- Начало каждого места: крупный номер «#10» и название места, затем карта: глобус → страна → точка места (3–4 секунды).
- Внизу экрана подпись с названием места, пока идёт раздел.
- Шрифт жирный без засечек под свободной лицензией (Google Fonts, OFL).
- Картинка совпадает со смыслом фразы: говорим про овец — показываем остров и овец, говорим про очистку — следы работ.
- Музыку пока не добавляй.

Результат:
- `ForbiddenEarth/video01/render/preview.mp4` (до 90 МБ);
- `ForbiddenEarth/video01/render/contact_sheet.jpg` — сетка со всеми использованными кадрами;
- `ForbiddenEarth/video01/visuals/credits.txt` — название, автор, лицензия и ссылка для каждого кадра;
- скрипт сборки, чтобы потом собрать остальные разделы так же.

**Отчёт.**
- `video01/render/preview.mp4` — 1:32.5, 1920×1080, 30 fps, H.264 High + AAC стерео, громкость −16 LUFS, 67 МБ.
- `video01/render/contact_sheet.jpg` — 21 кадр + карта, номера совпадают с `credits.txt`.
- `video01/visuals/credits.txt` — 21 изображение с Wikimedia Commons: 6 общественное достояние (USGS, CDC, NIST, Минэнерго США), остальные CC BY / CC BY-SA. Плюс Natural Earth, шрифты Oswald и Inter (OFL), Kokoro.
- Скрипты сборки: `visuals/BUILD.md`, `render.py`, `edl_build.py`, `maps/globe_zoom.py`, `make_credits.py`, `contact.py`. Кадры с метаданными лицензий — `visuals/src/`.
- Исключено: фото с погибшей коровой (Ниос), фото Портон-Дауна от Минобороны (лицензия OGL), граффити-шоссе Сентрейлии.
- Сеть облака: разрешены `commons.wikimedia.org`, `upload.wikimedia.org`, `thumb.wikimedia.org` (с подтверждения Алана).
- Проверить: кадры вступления короче 5–8 с (быстрая смена по заданию); снимок острова с людьми на пляже (1:16) — автор называет его Груинардом, но остров выглядит скалистее, чем на остальных кадрах; два снимка Ниоса маленькие (640–770 px), чуть мягче.
