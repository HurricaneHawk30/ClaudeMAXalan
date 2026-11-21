# video19 — 10 Lost Treasures No One Has Ever Found: план кадров

Текст диктора — `script_original.txt` (12 разделов, ~1600 слов, ≈11,5 мин).

Правила — как в video16: без портретов и крупных лиц, без водяных знаков. **Никакой нацистской символики** (свастики, флаги, форма) — только места: озеро, тоннели, горы, замок. **Без жертв**: ни погибших дайверов, ни узников лагерей; Риз и Топлиц — только пейзажи и входы в тоннели. **Портреты людей (Иоанн Безземельный, Крюгер, Уолц, Альбукерке, Рузвельт)** — не показывать; вместо них старинные карты, гравюры мест, монеты и предметы эпохи (PD). Старые карты и гравюры до 1929 года — PD, указать источник. Сокровища в кадре — только реальные музейные предметы той эпохи (PD/CC) или общие планы, не «фантазийное золото» из стоков.

| Раздел | Папка | Что показать по тексту | Плашка |
| --- | --- | --- | --- |
| 00_hook | все | Быстрая смена: отмели Уоша в отлив, Дублинский замок, Кокос с моря, реплика Янтарной комнаты; в конце FORBIDDEN EARTH | — |
| 01_king_john | `king_john` | Отмели и илистые протоки Уоша, старинная карта Уоша, поля Линкольншира, замок Ньюарк (где умер король) | LOST IN 1216 |
| 02_kruger | `kruger` | Претория (старые снимки до 1929 — PD), паровоз эпохи, бушвельд Лоувельда, старые фото монетного двора и банка Претории (до 1929 — PD), без портретов на монетах | NEVER FOUND |
| 03_toplitz | `toplitz` | Озеро Топлиц среди скал и леса, тёмная вода, Альпы Зальцкаммергута, знак запрета дайвинга (если есть свободный) | DIVING BANNED |
| 04_lost_dutchman | `lost_dutchman` | Горы Суеверия (Superstition Mountains), пик Уивере (Weavers Needle), каньоны, пустыня Аризоны в жару | THOUSANDS HAVE SEARCHED |
| 05_irish_crown_jewels | `irish_jewels` | Дублинский замок, Бедфордская башня, двор замка, газетные полосы 1907 года (PD), рисунок звезды ордена (PD) | STOLEN IN 1907 |
| 06_flor_de_la_mar | `flor_de_la_mar` | Рисунок карраки «Флор де ла Мар» из португальских рукописей XVI века (PD), Малаккский пролив, Малакка с крепостью А-Фамоза, штормовое море | WORTH BILLIONS? |
| 07_gold_train | `gold_train` | Тоннели проекта «Риз» (входы, своды), горы Совье, замок Ксёнж, Валбжих, железная дорога и насыпь у 65-го км | DUG UP IN 2016 |
| 08_treasure_of_lima | `cocos_island` | Остров Кокос с моря, водопады в джунглях, бухта Уэйфер (Wafer Bay), старая карта острова (PD), Лима (собор) | BANNED TO DIG |
| 09_oak_island | `oak_island` | Остров Оук сверху, дубы, «Денежная шахта» и раскопки (свободные снимки), берег Новой Шотландии, старые чертежи шахт (PD) | 6 MEN DIED |
| 10_amber_room | `amber_room` | Екатерининский дворец, реплика Янтарной комнаты (снимки с CC), фото оригинала 1917 года (PD), руины Кёнигсбергского замка (PD), Балтика | VANISHED IN 1945 |
| 11_outro | — | Спокойный фон (Оук-Айленд на закате или Кокос с моря), логотип и Subscribe слева, центр и правая половина свободны | — |

**Обложка** (Claude Code, `tools/thumbnail/make_thumbnail.js`):
- кадр: реплика Янтарной комнаты (золото и янтарь, тёплый свет, без людей); если нет чёткой свободной — остров Оук сверху или Кокос с моря;
- большой текст: `NEVER FOUND`;
- янтарная строка: `10 LOST TREASURES`.

Название на YouTube (ставит Claude при настройке): `10 Lost Treasures No One Has Ever Found (Six Men Died Searching for One)` (проверим по vidIQ).

Карты: глобус → страна → точка. Для Янтарной комнаты — линия Санкт-Петербург → Кёнигсберг; для сокровищ Лимы — линия Лима → остров Кокос.

Произношение: the Wash — the WOSH · Magna Carta — MAG-nuh KAR-tuh · Kruger — KROO-ger · Pretoria — prih-TOR-ee-uh · Lowveld — LOH-felt · Toplitz — TOP-lits · Superstition — soo-per-STISH-un · Jacob Waltz — JAY-kub WALTS · Dublin — DUB-lin · Flor de la Mar — flor deh lah MAR · Afonso de Albuquerque — ah-FON-soo deh AL-buh-ker-kee · Malacca — muh-LAK-uh · Sumatra — soo-MAH-truh · Wałbrzych — VAHW-bzhikh · Riese — REE-zeh · Lima — LEE-muh · Mary Dear · Cocos — KOH-kohs · Daniel McGinnis — mik-GIN-iss · Nova Scotia — NOH-vuh SKOH-shuh · Catherine Palace · Königsberg — KUR-nigz-berg.

Источники фактов: Britannica и English Heritage (Иоанн Безземельный, 1216), South African Mint и Britannica (миллионы Крюгера), Britannica, BBC и Der Standard (Топлиц, запрет дайвинга после 1963), Arizona State Parks и Britannica (Голландец, Уолц, 1891), National Archives of Ireland и Britannica (ирландские регалии, 6 июля 1907), Britannica и Smithsonian (Флор де ла Мар, 1511), BBC, Reuters 2015–2016 и National Geographic (поезд в Валбжихе), Costa Rica SINAC и Britannica (Кокос, сокровище Лимы 1820), Smithsonian и History (Оук-Айленд, 1795, шесть погибших, Рузвельт), Smithsonian, Britannica и музей Царское Село (Янтарная комната, 1716, 55 м², 6 т, копия 2003).
