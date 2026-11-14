# video08 — Hidden Wonders Tourists Never See: план кадров

Текст диктора — `script_original.txt` (12 разделов, ~1560 слов, ≈11 мин).

Правила — как в video07: без портретов и крупных лиц (туристы, гиды, местные — только общими планами или со спины), без водяных знаков. Хо Кхань — только упоминание, без его фото. Мендельсон, Бэнкс и Флиндерс — без портретов; можно старинные гравюры и рисунки мест (PD).

| Раздел | Папка | Что показать по тексту | Плашка |
| --- | --- | --- | --- |
| 00_hook | все | Толпы у известного места (общий план, без лиц), затем быстрая смена: розовое озеро, радужная река, светящаяся вода, луч света в пещеру; в конце FORBIDDEN EARTH | — |
| 01_crooked | `crooked` | Изогнутые сосны крупно и рядами, прямые сосны вокруг, лес зимой (если есть) | 400 BENT TREES |
| 02_fingal | `fingal` | Остров Стаффа с моря, базальтовые колонны, вход в пещеру, внутри пещеры, лодка у острова; гравюра 1772 года (PD) | INSPIRED A SYMPHONY |
| 03_hillier | `hillier` | Розовое озеро сверху рядом с синим океаном, берег, остров Мидл; снимок из космоса (если есть) | PINK FROM ABOVE |
| 04_kelimutu | `kelimutu` | Три озера с края кратера, озёра разного цвета, рассвет и туман, снимки разных лет (смена цвета) | 3 LAKES, CHANGING COLORS |
| 05_marble | `marble` | Мраморные своды и колонны, бирюзовая вода, лодка у входа, озеро Хенераль-Каррера, дорога Патагонии | 6,000 YEARS OF WAVES |
| 06_jellyfish | `jellyfish` | Золотые медузы под водой (крупно), озеро в джунглях сверху, мостки, острова Палау | MILLIONS OF JELLYFISH |
| 07_hidden_beach | `hidden_beach` | Круглая дыра с пляжем сверху, острова Мариетас, тоннель с моря, скалы | ~100 VISITORS A DAY |
| 08_mosquito_bay | `mosquito_bay` | Свечение в воде ночью, каяки, бухта днём, остров Вьекес, архив флота (PD, без людей крупно) | BRIGHTEST GLOWING BAY |
| 09_cano_cristales | `cano_cristales` | Красная река с жёлтым и зелёным, водопады, заповедник Макарена сверху, маленький самолёт | RIVER OF FIVE COLORS |
| 10_son_doong | `son_doong` | Вход в пещеру, огромный зал, луч света через провал, джунгли внутри, туман; карта и вид сверху на национальный парк Фонгня-Кебанг | JUNGLE INSIDE A CAVE |
| 11_outro | — | Спокойный фон (луч света в Шондонге или розовое озеро), логотип и Subscribe слева, центр и правая половина свободны | — |

**Обложка** (делает Claude Code скриптом `tools/thumbnail/make_thumbnail.js`):
- кадр: самый эффектный луч света в Шондонге (`son_doong`); если нет хорошего — Каньо-Кристалес с красной водой;
- большой текст: `SECRET EARTH`;
- янтарная строка: `10 WONDERS TOURISTS NEVER SEE`;
- `--pos` подобрать так, чтобы луч/главная деталь была в верхней половине, текст внизу не закрывал её. Если скрипт пишет, что текст шире кадра, — уменьшить `--size`.

Карты: как в video07 (глобус → страна → точка).

Произношение (для Kokoro):
Gryfino — gri-FEE-no · Staffa — STAF-a · Fingal — FING-gul · basalt — BA-salt · Mendelssohn — MEN-del-son · Hebrides — HEB-ri-deez · Hillier — HIL-ee-er · Flinders — FLIN-derz · Dunaliella salina — doo-na-lee-EL-a sa-LEE-na · Kelimutu — keh-lee-MOO-too · Flores — FLOR-es · Lio — LEE-oh · Patagonia — pat-a-GO-nee-a · General Carrera — heh-neh-RAHL ka-REH-ra · Palau — pa-LOW · El Niño — el NEEN-yo · Marieta — mar-ee-EH-ta · Vieques — vee-EH-kes · bioluminescent — by-oh-loo-mi-NES-ent · Caño Cristales — KAHN-yo kris-TAH-les · Hang Son Doong — hahng son DOONG · Ho Khanh — ho KAHN.

Источники фактов: Wikipedia (Crooked Forest, Fingal's Cave, Lake Hillier, Kelimutu, Islas Marietas National Park), Wordsworth Trust (Banks 1772), Coral Reef Research Foundation (Jellyfish Lake), PuertoRico.com со ссылкой на Guinness и USFWS (Mosquito Bay), Colombia Travel и Impulse Travel (Caño Cristales), Oxalis Adventure и CBS News (Son Doong), Discovery и UPenn (Crooked Forest).
