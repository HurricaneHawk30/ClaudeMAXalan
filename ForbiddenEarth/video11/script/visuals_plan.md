# video11 — 10 Places Sealed Shut: план кадров

Текст диктора — `script_original.txt` (12 разделов, ~1700 слов, ≈11,5–12 мин).

Правила — как в video10: без портретов и крупных лиц, без водяных знаков. **Рунит (Runit Dome):** никаких снимков ядерных взрывов с людьми, пострадавших, военных крупно — только купол сверху и с земли, атолл Эниветок из космоса, лагуна, бетон с трещинами; грибовидное облако допустимо только общим планом из архива DOE/NNSA (PD) и только один раз. **Онкало:** туннели, капсулы, буровые машины — можно; рабочих крупно — нет. **Склеп цивилизации (Crypt of Civilization):** фото Oglethorpe University могут быть несвободными — бери только с CC/PD; если двери склепа нет — здание Phoebe Hearst Hall снаружи, кампус. **Пирамида:** снимки ScanPyramids с камеры (эндоскоп) — только если лицензия свободная; иначе — пирамида снаружи, Большая галерея (PD/CC), схема. Людей на переднем плане нет.

| Раздел | Папка | Что показать по тексту | Плашка |
| --- | --- | --- | --- |
| 00_hook | все | Быстрая смена: дверь/здание склепа, вход в Семенное хранилище в снегу, купол Рунит сверху, Великая пирамида; в конце FORBIDDEN EARTH | — |
| 01_crypt | `crypt` | Кампус Oglethorpe, здание Phoebe Hearst Hall, дверь склепа (если свободная), старые фото 1930-х (PD), календарь/Египет для фразы про древнюю дату | OPEN IN 8113 |
| 02_hall_of_records | `hall_of_records` | Гора Рашмор общим планом и сбоку, каньон за головами, вход в туннель, Борглум за работой (архив NPS, PD, без крупного лица), гранит | SEALED FOR THOUSANDS OF YEARS |
| 03_seed_vault | `seed_vault` | Бетонный клин входа в снегу (ночью с подсветкой — если есть), Шпицберген, Лонгйир, коробки с семенами на полках, ящики | −18°C |
| 04_movile | `movile` | Побережье у Мангалии, Чёрное море, пещерные пауки/водяные скорпионы/многоножки (макро), бактериальная плёнка на воде, пещерные туннели (если Movile нет — общие пещеры, напиши в отчёте) | 5.5 MILLION YEARS ALONE |
| 05_chauvet | `chauvet` | Ущелье Ардеш, мост Пон-д'Арк, скала со входом, рисунки (львы, лошади, носороги — снимки Министерства культуры, только свободные), копия Chauvet 2 | 36,000 YEARS OLD |
| 06_runit | `runit` | Купол сверху (DOE/NNSA, PD), бетон крупно, атолл Эниветок из космоса (NASA), лагуна, пальмы, волны у купола; один архивный общий план испытания 1958 года (PD) | THE TOMB |
| 07_vostok | `vostok` | Ледяной щит Антарктиды, станция Восток, буровая, керн льда, радарная карта озера (NASA/NSF, PD), снимок из космоса | 4 KM UNDER THE ICE |
| 08_onkalo | `onkalo` | Остров Олкилуото, АЭС, спуск в туннель, туннели в граните, медные капсулы, бентонит; спутниковый снимок | 100,000 YEARS |
| 09_papyri | `papyri` | Геркуланум (раскопки, улицы), Везувий, обугленные свитки, сканы/развёрнутые фрагменты (свободные), бюсты/статуи виллы из музея Неаполя, вилла Гетти (копия) | 1,800 BURNED SCROLLS |
| 10_great_pyramid | `great_pyramid` | Великая пирамида, северная грань с входом и шевронами, Большая галерея внутри, схема пустот (если свободная), Гиза из космоса | NEVER ENTERED |
| 11_outro | — | Спокойный фон (вход в Семенное хранилище или пирамида на закате), логотип и Subscribe слева, центр и правая половина свободны | — |

**Обложка** (делает Claude Code скриптом `tools/thumbnail/make_thumbnail.js`):
- кадр: вход в Семенное хранилище Шпицбергена (бетонный клин в снегу — сразу читается как «запечатанная дверь»); если нет яркого — Великая пирамида с северной гранью;
- большой текст: `DO NOT OPEN`;
- янтарная строка: `10 PLACES SEALED SHUT`;
- `--pos` подобрать так, чтобы вход был в верхней половине и текст внизу его не закрывал. Если скрипт пишет, что текст шире кадра, — уменьшить `--size`.

Название на YouTube (ставит Claude при настройке): `10 Places Sealed Shut — And What's Still Inside` (проверим по vidIQ).

Карты: как в video10 (глобус → страна → точка). Для Востока — Антарктида, для Рунита — Тихий океан и Маршалловы острова.

Произношение (для Kokoro):
Oglethorpe — OH-gul-thorp · Thornwell — THORN-wel · Rushmore — RUSH-mor · Gutzon Borglum — GUT-sun BOR-glum · Svalbard — SVAHL-bar · Aleppo — a-LEP-oh · permafrost — PER-ma-frost · Movile — moh-VEE-leh · hydrogen sulfide — HY-dro-jen SUL-fide · Chauvet — sho-VAY · Ardèche — ar-DESH · Lascaux — las-KOH · Runit — ROO-nit · Enewetak — eh-NEE-weh-tok · Marshall — MAR-shal · Vostok — vos-TOK · Ontario — on-TAIR-ee-oh · kerosene — KER-o-seen · Onkalo — ON-ka-lo · Vesuvius — ve-SOO-vee-us · Herculaneum — her-kyoo-LAY-nee-um · Giza — GEE-za · muons — MYOO-onz.

Источники фактов: Oglethorpe University и Wikipedia (Crypt of Civilization), NPS и Wikipedia (Hall of Records), Crop Trust, Норвежское правительство и Wikipedia (Svalbard Global Seed Vault, ICARDA 2015, вода 2017), Wikipedia, BBC и Smithsonian (Movile Cave), Министерство культуры Франции и Wikipedia (Chauvet), LA Times, ABC Australia и DOE (Runit Dome, Гутерриш 2019), British Antarctic Survey, Nature и Wikipedia (Lake Vostok, 2012), Posiva и Reuters (Onkalo, лицензия октябрь 2026), Vesuvius Challenge, Nature и Wikipedia (Villa of the Papyri, 2023–2026), ScanPyramids, Nature (2017) и Nature Communications (2023) (Великая пирамида).
