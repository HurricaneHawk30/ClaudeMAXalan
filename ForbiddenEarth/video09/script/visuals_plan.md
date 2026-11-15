# video09 — Beautiful Places That Can Kill You: план кадров

Текст диктора — `script_original.txt` (12 разделов, ~1630 слов, ≈11,5 мин).

Правила — как в video08: без портретов и крупных лиц (туристы, гиды, дайверы — только общими планами или со спины), без водяных знаков. **Никаких погибших, тел, спасательных операций и мест трагедий крупно**: на фразах о гибели — само место, табличка-предупреждение, пустая тропа, вода. Мемориальные таблички в Голубой дыре — только общим планом, чтобы имена не читались. Снимки Ника Брандта (окаменевшие птицы на Натроне) не брать — они под копирайтом. Понсе де Леон, Николя Стрикленд — без портретов; можно старинную гравюру или карту Карибов (PD).

| Раздел | Папка | Что показать по тексту | Плашка |
| --- | --- | --- | --- |
| 00_hook | все | Быстрая смена: табличка Ханакапиаи, Devil's Pool сверху, манцинелла с плодами, Grand Prismatic сверху, синий круг Голубой дыры; в конце FORBIDDEN EARTH | — |
| 01_manchineel | `manchineel` | Дерево на пляже, листья и зелёные «яблоки» крупно, красная полоса или красный X на стволе, табличка-предупреждение, карибский пляж; старинная карта Карибов (PD) | LITTLE APPLE OF DEATH |
| 02_natron | `natron` | Красное озеро сверху и из космоса (NASA), соляная корка, вулкан Ол-Доиньо-Ленгаи, стаи фламинго, соляные острова | AS CAUSTIC AS AMMONIA |
| 03_hanakapiai | `hanakapiai` | Скалы побережья На-Пали, тропа Калалау, пляж Ханакапиаи, табличка с засечками (крупно — это главный кадр), волны у берега | 80+ TALLY MARKS |
| 04_hua | `hua` | Пики Хуашань в облаках, даосские храмы, сосны, тропа из досок на отвесной скале, цепи и крючья, вид вниз | 30 CM WIDE |
| 05_devils_pool | `devils_pool` | Водопад Виктория (общий план, брызги), водопад в сезон дождей, остров Ливингстона, сам бассейн у края (люди только мелко или со спины), Замбези сверху | 100+ M DROP |
| 06_ice_caves | `ice_caves` | Голубые ледяные пещеры изнутри, пузырьки во льду крупно, ледник Брейдамеркурйокюдль и Ватнайёкюдль снаружи, лагуна Йёкюльсаурлоун, тающий лёд летом | MELTS EVERY SUMMER |
| 07_antelope | `antelope` | Узкий вход в каньон в пустыне, изгибы песчаника, лучи света в пыли, металлические лестницы Нижнего каньона, грозовое небо над пустыней (без людей крупно) | FLASH FLOOD, 1997 |
| 08_jacobs_well | `jacobs_well` | Круглая голубая дыра в ручье сверху, известняк, ручей Сайпресс-Крик, вид вглубь, кипарисы; подводная пещера — если есть свободные снимки | 8+ DIVERS LOST |
| 09_yellowstone | `yellowstone` | Grand Prismatic сверху (NPS, PD — много), цветные кольца крупно, пар, мостки над источниками, бурлящие источники, табличка «stay on boardwalk» | DEADLIER THAN BEARS |
| 10_blue_hole | `blue_hole` | Голубой круг в рифе сверху, побережье Синая у Дахаба, кораллы и рыбы, дайверы под водой (мелко), синяя глубина, мемориальные таблички общим планом | THE DIVERS' CEMETERY |
| 11_outro | — | Спокойный фон (Grand Prismatic или Голубая дыра сверху), логотип и Subscribe слева, центр и правая половина свободны | — |

**Обложка** (делает Claude Code скриптом `tools/thumbnail/make_thumbnail.js`):
- кадр: Grand Prismatic Spring сверху — синий центр и оранжевые кольца (`yellowstone`, NPS, PD); если нет яркого — Devil's Pool у края водопада без лиц;
- большой текст: `LOOKS SAFE`;
- янтарная строка: `10 BEAUTIFUL PLACES THAT CAN KILL YOU`;
- `--pos` подобрать так, чтобы синий центр источника был в верхней половине, текст внизу не закрывал его. Если скрипт пишет, что текст шире кадра, — уменьшить `--size`.

Название на YouTube (ставит Claude при настройке): `10 Beautiful Places That Can Kill You (And People Still Go)`.

Карты: как в video08 (глобус → страна → точка). Для манцинеллы — Карибское море целиком.

Произношение (для Kokoro):
manchineel — MAN-chi-neel · Tobago — toh-BAY-go · Juan Ponce de León — hwahn PON-say day lay-OWN · Natron — NAY-tron · Tanzania — tan-za-NEE-a · Hanakapiai — ha-na-ka-PEE-eye · Kauai — kow-EYE · Na Pali — nah PAH-lee · Hua — HWAH · Taoist — DOW-ist · Zambia — ZAM-bee-a · Zimbabwe — zim-BAHB-way · Zambezi — zam-BEE-zee · Livingstone — LIV-ing-stun · Vatnajökull — VAHT-na-yuh-kutl · Navajo — NAV-a-ho · Wimberley — WIM-ber-lee · Yellowstone — YEL-oh-stone · Prismatic — priz-MAT-ik · Sinai — SY-nye · Dahab — da-HAHB · narcosis — nar-KOH-sis.

Источники фактов: Wikipedia (Manchineel, Hanakāpīʻai Beach, Antelope Canyon, Blue Hole (Red Sea), Grand Prismatic Spring), EarthDate (манцинелла, BMJ 2000), Times of the Turks and Caicos (Понсе де Леон), Live Science и NASA Earth Observatory (Натрон), Star-Advertiser и Civil Beat (Ханакапиаи, ~29–30 утонувших с 1970), Travel China Guide и Easy Tour China (Хуашань), Victoria Falls Guide и Rhino Africa (Devil's Pool), Viristar и AP (ледяные пещеры, август 2024), NCDC/NOAA (Антилоп, 12 августа 1997), Texas Parks & Wildlife через Visit Wimberley (Jacob's Well, решётка 1980), NPS и USGS (Йеллоустон), Spiegel и Wikipedia (Голубая дыра).
