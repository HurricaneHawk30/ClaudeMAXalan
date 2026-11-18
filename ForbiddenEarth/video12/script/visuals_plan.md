# video12 — 10 Places No Human Has Ever Set Foot On: план кадров

Текст диктора — `script_original.txt` (12 разделов, ~1500 слов, ≈10,5–11 мин).

Правила — как в video11: без портретов и крупных лиц, без водяных знаков. **Каваг(а)рбо:** никаких снимков экспедиции 1991 года, лагеря, погибших, поисков — только гора, ледник Минъюн, ступы и молитвенные флаги общим планом, деревня Юбэн издалека. **Сакатон:** никаких фото дайверов (Шек Эксли, Джим Боуден) — только сам колодец, вода, ранчо, робот DEPTHX (NASA/Stone Aerospace, PD или CC). **Мачапучаре:** фото экспедиции 1957 года не нужны; гора, Покхара, озеро Фева, треккеры только далеко и со спины. **Глубокое дно:** снимки NOAA Ocean Exploration (PD) — животные, жерла, рельеф дна; без мёртвых животных.

| Раздел | Папка | Что показать по тексту | Плашка |
| --- | --- | --- | --- |
| 00_hook | все | Быстрая смена: Мачапучаре на рассвете, синяя дыра сверху, радарный разрез гор Гамбурцева или лёд Антарктиды, тёмное морское дно с прожектором; в конце FORBIDDEN EARTH | — |
| 01_hranice | `hranice` | Лес и известняк у Границе, обрыв провала, зелёное озеро внизу, пещеры Збрашов рядом, схема/разрез провала (CC), робот (если свободный) | NO BOTTOM FOUND |
| 02_machapuchare | `machapuchare` | Двойная вершина «рыбий хвост» с разных сторон, Покхара и озеро Фева, Аннапурна, хребет на закате, облака у вершины | NEVER SUMMITED |
| 03_taam_ja | `taam_ja` | Залив Четумаль сверху (Sentinel-2/Landsat), тёмный круг в мелкой воде, карибская вода, схема/батиметрия дыры из статьи Frontiers (CC BY 4.0), другие синие дыры для сравнения общим планом | 420 M — STILL NO BOTTOM |
| 04_thwaites | `thwaites` | Ледник Туэйтс сверху (NASA, PD), край ледяного шельфа, трещины, лагерь и скважина (если без людей крупно), робот Icefin (снимки NASA/Cornell с CC/PD), подлёдная вода | ONLY A ROBOT HAS BEEN HERE |
| 05_kawagarbo | `kawagarbo` | Каваг(а)рбо/хребет Мэйли на рассвете («золотая гора»), ледник Минъюн, ступы и флаги общим планом, ущелье Меконга, Юньнань | FORBIDDEN SUMMIT |
| 06_denman | `denman` | Ледник Денмана из космоса (NASA/Landsat), карта BedMachine (если свободная), берег Мёртвого моря для сравнения, антарктический лёд, схема «уровень моря / Мёртвое море / каньон» (можно нарисовать кодом) | 3,500 M BELOW SEA LEVEL |
| 07_zacaton | `zacaton` | Круглый колодец Сакатон сверху и с края, вода, ранчо и травяные острова, соседние колодцы, робот DEPTHX (NASA), сонарная карта (если свободная). Людей нет | ROBOT ONLY |
| 08_gamburtsev | `gamburtsev` | Купол А и плато Восточной Антарктиды, самолёт-радар над льдом (NSF/BAS, если свободно), радарный разрез гор (Creyts et al. 2014, CC BY-SA), карта подлёдного рельефа, Альпы для сравнения | MOUNTAINS NO ONE HAS SEEN |
| 09_gangkhar | `gangkhar` | Гангкхар Пуенсум (снимки на Commons), горы Бутана, монастыри и дзонги общим планом, флаги, высокогорные долины; Эверест для сравнения | HIGHEST UNCLIMBED PEAK |
| 10_deep_seafloor | `deep_seafloor` | Океан сверху, свет гаснет с глубиной, снимки NOAA Okeanos Explorer: подводные горы, жерла, кораллы, глубоководные животные, аппарат с прожекторами; карта мира — где мы видели дно (если свободная) | 0.001% SEEN |
| 11_outro | — | Спокойный фон (Мачапучаре на закате или тёмное дно), логотип и Subscribe слева, центр и правая половина свободны | — |

**Обложка** (делает Claude Code скриптом `tools/thumbnail/make_thumbnail.js`):
- кадр: Мачапучаре — острая двойная вершина на рассвете или в облаках (самая узнаваемая «нетронутая» вершина); если нет яркого — Гангкхар Пуенсум;
- большой текст: `UNTOUCHED`;
- янтарная строка: `10 PLACES NO HUMAN HAS REACHED`;
- `--pos` подобрать так, чтобы вершина была в верхней половине и текст внизу её не закрывал. Если скрипт пишет, что текст шире кадра, — уменьшить `--size`.

Название на YouTube (ставит Claude при настройке): `10 Places No Human Has Ever Set Foot On` + крючок (проверим по vidIQ).

Карты: как в video11 (глобус → страна → точка). Для Туэйтса, Денмана и Гамбурцева — Антарктида с точкой; для глубокого дна — весь мир (океаны).

Произношение (для Kokoro):
Hranice — HRAH-nyi-tseh · Krzysztof Starnawski — KSHISH-tof star-NAHV-skee · Machapuchare — MAH-cha-poo-CHAH-ray · Pokhara — POH-ka-ra · Shiva — SHEE-va · Wilfrid Noyce — WIL-frid NOYCE · Taam Ja' — TAHM HAH · Mayan — MY-an · Belize — be-LEEZ · Thwaites — THWAITS · Icefin — ICE-fin · Kawagarbo — KAH-wah-gar-boh · Yunnan — yoon-NAHN · Tibetan — ti-BET-an · Denman — DEN-man · Zacatón — zah-kah-TONE · Sheck Exley — SHEK EX-lee · Europa — yoo-ROH-pa · Gamburtsev — gam-BOORT-sev · Gangkhar Puensum — GANG-kar POON-sum · Bhutan — boo-TAHN · Rhode Island — rohd EYE-land.

Источники фактов: Wikipedia, Guinness World Records и Visit Czechia (Hranice, 2016 и 2022), Wikipedia, Himalayan Club и Mount Everest Foundation (Мачапучаре, 1957), Frontiers in Marine Science, Live Science и CBS (Taam Ja', 2021 и 2023), AP/NPR и Nature (Thwaites, Icefin, 2020/2023), Wikipedia и ExplorersWeb (Каваг(а)рбо, 1991 и 2001), UC Irvine, BBC и Guinness (Denman, 2019), Carnegie Mellon, SwRI и NASA Astrobiology (Сакатон, 1994 и 2007), British Antarctic Survey, IPY и The Conversation (Гамбурцев), Wikipedia, Explorersweb и History.com (Гангкхар Пуенсум), Science Advances / Ocean Discovery League (глубокое дно, май 2025).
