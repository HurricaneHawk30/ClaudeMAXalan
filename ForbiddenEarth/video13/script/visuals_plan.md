# video13 — 10 Most Dangerous Roads on Earth: план кадров

Текст диктора — `script_original.txt` (12 разделов, ~1460 слов, ≈10,5 мин).

Правила — как в video12: без портретов и крупных лиц, без водяных знаков. **Никаких аварий, разбитых машин, пострадавших.** **Колыма:** никаких исторических фото заключённых и останков — только дорога, зимний пейзаж, руины лагерей и посёлков общим планом. **Юнгас:** кресты у обочины — только издалека; велосипедисты и машины только со спины и далеко. Водители и люди в кадре — мелко, без лиц.

| Раздел | Папка | Что показать по тексту | Плашка |
| --- | --- | --- | --- |
| 00_hook | все | Быстрая смена: серпантин Лос-Каракольес сверху, ледовая дорога с грузовиком, окна тоннеля Гоулян, Дорога смерти в тумане; в конце FORBIDDEN EARTH | — |
| 01_caracoles | `caracoles` | Серпантин сверху («улитка»), Анды, грузовики на поворотах, снег на перевале, граница Лос-Либертадорес | 29 HAIRPIN BENDS |
| 02_ice_road | `ice_road` | Ледовая дорога по озеру, грузовики на льду, тундра, Йеллоунайф, алмазный рудник сверху (Diavik/Ekati, если свободно) | ROAD MADE OF ICE |
| 03_sani_pass | `sani_pass` | Петли Сани-Пасс сверху, внедорожник на гравии, Дракенсберг, пограничный пост Лесото, паб на вершине | 4x4 ONLY |
| 04_dalton | `dalton` | Гравийная дорога вдоль трубопровода, перевал Атиган, хребет Брукс, тундра, знак Coldfoot / «next services 240 miles» (если свободный), зима | NO SERVICES FOR 240 MILES |
| 05_skippers | `skippers` | Дорога на стене каньона, река Шотовер, мост Скипперс, золотые прииски (архив PD) | NO RENTAL CARS |
| 06_zoji_la | `zoji_la` | Перевал Зоджи-Ла, узкая дорога над обрывом, грузовики и снег, Ладакх, портал тоннеля (если свободный) | CLOSED FOR MONTHS |
| 07_guoliang | `guoliang` | Тоннель Гоулян снаружи с «окнами», вид из окна вниз, деревня на скале, горы Тайхан, старая каменная лестница | CARVED BY HAND |
| 08_kolyma | `kolyma` | Колымская трасса зимой и летом, Магадан, Якутск, грузовик в снегу, руины посёлков и лагерей общим планом, мост через Колыму | ROAD OF BONES |
| 09_fairy_meadows | `fairy_meadows` | Гравийная дорога над ущельем, джип на краю (далеко), Райкот-мост, Нанга-Парбат, Фейри-Медоус | NO GUARDRAILS |
| 10_yungas | `yungas` | Дорога смерти: узкий карниз над пропастью, туман, водопады на дорогу, велосипедисты далеко, новая дорога для сравнения, Ла-Пас и Юнгас | DEATH ROAD |
| 11_outro | — | Спокойный фон (серпантин на закате или дорога в тумане), логотип и Subscribe слева, центр и правая половина свободны | — |

**Обложка** (Claude Code, `tools/thumbnail/make_thumbnail.js`):
- кадр: Дорога смерти (Юнгас) — узкий карниз над пропастью, лучше в тумане; если нет яркого — тоннель Гоулян с окнами;
- большой текст: `DEATH ROAD`;
- янтарная строка: `10 MOST DANGEROUS ROADS`;
- `--pos` так, чтобы дорога и обрыв были в верхней половине.

Название на YouTube (ставит Claude при настройке): `10 Most Dangerous Roads on Earth (One Is Called Death Road)` (проверим по vidIQ).

Карты: глобус → страна → точка, для каждой дороги.

Произношение (для Kokoro):
Caracoles — kah-rah-KOH-les · Mendoza — men-DOH-sa · Tibbitt — TIB-it · Contwoyto — kon-TWOY-toh · Yellowknife — YEL-oh-nife · Sani — SAH-nee · Drakensberg — DRAH-kenz-berg · Lesotho — le-SOO-too · Prudhoe — PRUD-oh · Atigun — AT-ih-gun · Brooks · Shotover — SHOT-oh-ver · Zoji La — ZOH-jee LAH · Ladakh — la-DAHK · Kashmir — kash-MEER · Guoliang — gwoh-lee-AHNG · Taihang — tie-HAHNG · Kolyma — koh-lih-MAH · Magadan — mah-gah-DAHN · Yakutsk — yah-KOOTSK · gulag — GOO-lahg · Nanga Parbat — NUN-gah PUR-but · Karakoram — kah-rah-KOR-um · Raikot — RYE-kot · Tato — TAH-toh · Yungas — YOON-gahs · Chaco — CHAH-koh · Paraguayan — pa-ra-GWY-an.

Источники фактов: Wikipedia и dangerousroads.org (Los Caracoles, снег 2013), Wikipedia, JV Winter Road и RCI (Tibbitt to Contwoyto), Wikipedia и SA History (Sani Pass), Alaska DOT&PF, BLM и National Geographic (Dalton), NZ Heritage, newzealand.com и Contractor (Skippers), Dawn/AFP, All India Radio и Outlook Traveller (Zoji La, тоннель — июнь 2026), Wikipedia, China Daily и Shanghai Daily (Guoliang), Wikipedia, NYT и Guinness (Kolyma), Wikipedia и Atlas Obscura (Fairy Meadows), Wikipedia, BBC и Discovery (Yungas).
