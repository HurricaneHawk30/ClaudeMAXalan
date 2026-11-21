# video17 — 10 Places Disappearing Before Our Eyes: план кадров

Текст диктора — `script_original.txt` (12 разделов, ~1430 слов, ≈10,5 мин).

Правила — как в video16: без портретов и крупных лиц, без водяных знаков. **Без пострадавших** от наводнений и обвала; жители Тувалу, Острова Жан-Шарль, Джакарты — только мелко и со спины. **Блаттен:** только сам обвал, долина, снимки со спутника (Copernicus Sentinel — с указанием) и общие планы; без спасателей и поисков. **Мёртвое море:** без пограничных и военных объектов, без политических символов. Сравнения «тогда и сейчас» (USGS, NASA) — очень желательны.

| Раздел | Папка | Что показать по тексту | Плашка |
| --- | --- | --- | --- |
| 00_hook | все | Быстрая смена: провалы у Мёртвого моря, затопленная Джакарта, долина Блаттена после обвала, Фунафути с воздуха; в конце FORBIDDEN EARTH | — |
| 01_glacier_np | `glacier_np` | Ледник Гриннелл и бирюзовое озеро, пары фото USGS «было — стало» (Boulder, Grinnell, Shepard), горы Монтаны | 150 → 26 GLACIERS |
| 02_kilimanjaro | `kilimanjaro` | Вершина с ледниками, ледяные стены Фуртвенглера крупно, саванна под горой, снимки NASA «было — стало» | 85% OF THE ICE GONE |
| 03_aral_sea | `aral_sea` | Снимки NASA 1989 → 2014 (Terra/Landsat), корабли на песке у Муйнака, пустыня Аралкум, плотина Кокарал, Малый Арал с водой | 90% OF THE WATER GONE |
| 04_dead_sea | `dead_sea` | Провалы (sinkholes) сверху и с земли, соляные берега, отметки старого уровня воды, заброшенные пляжи, люди на воде мелко | 6,000+ SINKHOLES |
| 05_venice | `venice` | Высокая вода на площади Сан-Марко (общим планом), каналы, ворота MOSE, толпы туристов издалека, пустые улицы рано утром | 78 FLOOD GATES |
| 06_great_barrier_reef | `great_barrier_reef` | Риф сверху, здоровые кораллы, обесцвеченные кораллы (AIMS/NOAA — с указанием лицензии), рифы из космоса | 8 MASS BLEACHINGS |
| 07_isle_de_jean_charles | `isle_de_jean_charles` | Остров сверху, единственная дорога через воду, дома на сваях, карты/снимки USGS «1963 — сейчас» | 98% OF THE LAND GONE |
| 08_jakarta | `jakarta` | Северная Джакарта, морская стена, затопленные улицы общим планом, Муара-Бару, стройка Нусантары (с разрешённой лицензией) | 4 M LOWER |
| 09_blatten | `blatten` | Деревня Блаттен до обвала (Commons), ледник Бирх и гора Кляйнес-Несторн, долина после обвала, снимки Sentinel-2 до/после | 300 PEOPLE EVACUATED |
| 10_tuvalu | `tuvalu` | Фунафути с воздуха, узкая полоса суши между океаном и лагуной, взлётная полоса, волны у домов, проект намыва земли | 280 VISAS A YEAR |
| 11_outro | — | Спокойный фон (Венеция на закате или риф сверху), логотип и Subscribe слева, центр и правая половина свободны | — |

**Обложка** (Claude Code, `tools/thumbnail/make_thumbnail.js`):
- кадр: затопленная площадь Сан-Марко в Венеции общим планом (узнаваемо сразу); если нет чёткого — Фунафути (Тувалу) с воздуха;
- большой текст: `GONE SOON`;
- янтарная строка: `10 VANISHING PLACES`.

Название на YouTube (ставит Claude при настройке): `10 Places Disappearing Before Our Eyes (Visit While You Can)` (проверим по vidIQ).

Карты: глобус → страна → точка. Для Тувалу — точка в Тихом океане и линия до Австралии.

Произношение: Grinnell — grih-NEL · Kilimanjaro — kil-ih-man-JAR-oh · Aral — AIR-ul · Aralkum — ar-al-KOOM · Jordan — JOR-dun · MOSE — MOH-zeh · Basilica — buh-SIL-ih-kuh · Queensland — KWEENZ-land · Isle de Jean Charles — eel duh zhahn SHARL · Jakarta — juh-KAR-tuh · Nusantara — noo-sahn-TAH-rah · Borneo — BOR-nee-oh · Blatten — BLAH-ten · Tuvalu — too-VAH-loo · Tuvaluans — too-vah-LOO-unz · Funafuti — foo-nah-FOO-tee.

Источники фактов: USGS и Portland State University (ледники Глейшер, 2017), PNAS 2009 (Thompson et al., Килиманджаро), Euronews и Global Voices 2026 (Аральское море, плотина Кокарал), Times of Israel, Globes и Геологическая служба Израиля (Мёртвое море), город Венеция и Lonely Planet (сбор за вход 2026, MOSE), AIMS 2025 и 2026 (Большой Барьерный риф), PBS и Wikipedia (Остров Жан-Шарль, HUD 2016), BRIN / Jakarta Post 2026 (Джакарта), NPR, Reuters и правительство Вале (Блаттен, май 2025), DFAT Australia, SBS и NBC (Тувалу, Falepili 2025).
