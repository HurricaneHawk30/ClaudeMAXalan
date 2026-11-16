# video10 — Islands No One Is Allowed to Live On: план кадров

Текст диктора — `script_original.txt` (12 разделов, ~1550 слов, ≈10,5–11 мин).

Правила — как в video09: без портретов и крупных лиц, без водяных знаков. **Северный Сентинел: никаких фотографий сентинельцев** (их съёмка запрещена законом Индии, и это вопрос уважения) — только остров сверху и из космоса (NASA), рифы, море, карта. Клиппертон: никаких снимков выживших 1917 года и людей того времени — только атолл, лагуна, маяк/руины, старые карты (PD). Возрождение: только спутниковые снимки Аральского моря (NASA, PD) и брошенный городок Кантубек общими планами; никаких лабораторий крупно, схем, контейнеров. Повелья — без «паранормальных» постановочных кадров. Хёрд — без политиков; на фразе о пошлинах — пингвины на пляже.

| Раздел | Папка | Что показать по тексту | Плашка |
| --- | --- | --- | --- |
| 00_hook | все | Быстрая смена: Болс-Пирамид из моря, пластик на пляже Хендерсона, пингвины на Хёрде, остров Северный Сентинел из космоса; в конце FORBIDDEN EARTH | — |
| 01_skellig | `skellig` | Скеллиг-Майкл с моря, каменные ступени, каменные «ульи» монахов, тупики на скалах, лодка у причала | 618 STONE STEPS |
| 02_henderson | `henderson` | Остров сверху и с моря, джунгли, пляж с пластиком (крупно мусор, без людей), обломки сетей | 38 MILLION PIECES OF PLASTIC |
| 03_balls_pyramid | `balls_pyramid` | Болс-Пирамид с моря и сверху, остров Лорд-Хау, гигантский палочник (снимки из зоопарка, крупно), скалы | 24 INSECTS ON A ROCK |
| 04_poveglia | `poveglia` | Остров с колокольней из лагуны, заброшенные здания общим планом, заросли, Венеция и Лидо вдали, старые карты лагуны (PD) | QUARANTINE ISLAND |
| 05_farallon | `farallon` | Гранитные острова в тумане, птичьи колонии, морские львы, маяк на Юго-Восточном острове, белая акула (снимки NOAA, если есть); карта свалки бочек (USGS/NOAA, PD) | ~48,000 BARRELS |
| 06_heard | `heard` | Вулкан Биг-Бен в облаках, ледники, чёрный пляж, пингвины, морские слоны; снимок со спутника (ESA Sentinel/NASA) | PENGUINS ONLY |
| 07_bouvet | `bouvet` | Остров с ледником из моря и со спутника (NASA), скалы, ледяной купол; гравюра/карта XVIII века (PD); снимок шлюпки 1964 года, только если он свободный | 1,700 KM TO ANYWHERE |
| 08_clipperton | `clipperton` | Атолл сверху (NASA), кольцо кораллов, лагуна, скала Клиппертон, птицы-олуши, руины и маяк общим планом; старые карты (PD) | ABANDONED SINCE 1917 |
| 09_vozrozhdeniya | `vozrozhdeniya` | Аральское море из космоса в разные годы (NASA, PD) — главный приём: остров становится полуостровом; Кантубек издалека, пустыня, ржавые корабли Арала | THE ISLAND THAT VANISHED |
| 10_north_sentinel | `north_sentinel` | Остров из космоса (снимки МКС/NASA), рифы и лес сверху, Андаманские острова, море; карта зоны запрета. Людей нет | DO NOT APPROACH |
| 11_outro | — | Спокойный фон (Скеллиг-Майкл или Болс-Пирамид), логотип и Subscribe слева, центр и правая половина свободны | — |

**Обложка** (делает Claude Code скриптом `tools/thumbnail/make_thumbnail.js`):
- кадр: Болс-Пирамид из моря (самая острая и драматичная форма); если нет яркого — Северный Сентинел из космоса;
- большой текст: `DO NOT LAND`;
- янтарная строка: `10 ISLANDS NO ONE CAN LIVE ON`;
- `--pos` подобрать так, чтобы пик скалы был в верхней половине, текст внизу его не закрывал. Если скрипт пишет, что текст шире кадра, — уменьшить `--size`.

Название на YouTube (ставит Claude при настройке): `10 Islands No One Is Allowed to Live On` + крючок (решим по vidIQ).

Карты: как в video09 (глобус → страна → точка). Для Возрождения — Аральское море.

Произношение (для Kokoro):
Skellig — SKEL-ig · Pitcairn — PIT-kairn · Henderson — HEN-der-sun · Lord Howe — lord HOW · Tasman — TAZ-man · Poveglia — po-VEL-ya · Farallon — FAIR-a-lon · Heard — HURD · Perth — PURTH · Bouvet — boo-VAY · Clipperton — KLIP-er-tun · scurvy — SKUR-vee · Vozrozhdeniya — voz-rozh-DEN-ee-ya · Aral — AR-al · Kazakhstan — ka-zakh-STAHN · Uzbekistan — ooz-BEK-i-stahn · anthrax — AN-thrax · Sentinel — SEN-ti-nel · Sentinelese — sen-ti-nel-EEZ · Andaman — AN-da-man · Bengal — ben-GAWL.

Источники фактов: Skellig Islands, Heritage Ireland (Скеллиг-Майкл), National Geographic, University of Tasmania и Time (Хендерсон, 2017), Wikipedia и Gripped (Болс-Пирамид), Wikipedia, CNN и Far Out (Повелья), USGS, Atlas Obscura и KQED (Фараллоны), Guardian, Forbes и NPR (Хёрд, апрель 2025), Wikipedia, Atlas Obscura и Oceanwide (Буве), Wikipedia и Damn Interesting (Клиппертон), Arms Control Association, NTI и Britannica (Возрождение), Wikipedia, National Geographic и Business Insider (Северный Сентинел).
