"""Edit decision list for video05 "The Oldest Places Still in Use Today" (12:22.4).
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 10 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 742.4

FILES = {os.path.splitext(os.path.basename(p))[0]: os.path.relpath(p, HERE)
         for p in glob.glob(os.path.join(HERE, "src", "*", "*")) if not p.endswith(".json")}

IN = lambda s0=1.0, s1=1.10, c0=(0.5, 0.5), c1=None: {"s0": s0, "s1": s1, "c0": list(c0), "c1": list(c1 or c0)}
OUT = lambda s0=1.12, s1=1.0, c0=(0.5, 0.5), c1=None: {"s0": s0, "s1": s1, "c0": list(c0), "c1": list(c1 or c0)}
PAN = lambda a, b, s=1.15, y=0.5: {"s0": s, "s1": s, "c0": [a, y], "c1": [b, y]}
TILT = lambda a, b, s=1.15, x=0.5: {"s0": s, "s1": s, "c0": [x, a], "c1": [x, b]}

def shot(key, t0, t1, move=None, x=0.6, **kw):
    return {"src": FILES.get(key, f"src/MISSING/{key}"), "t0": t0, "t1": t1, "move": move or IN(), "xin": x, "xout": x, **kw}

def inset(key, t0, t1, **kw):
    return shot(key, t0, t1, None, inset=True, **kw)

shots, overlays = [], []

def place(num, name, sub, frames, t_card, t_map, t_lower, t_end, items, lower=None, badge=None):
    if badge:   # age plate, bottom-left: appears with "Number ...", holds ~6 s (ends before the lower third)
        overlays.append({"type": "badge", "text": badge, "t0": t_card + 0.4, "t1": t_lower - 0.1, "fin": 0.5, "fout": 0.5})
    shots.append({"card": True, "bg_map": f"maps/{frames}", "num": num, "name": name, "sub": sub,
                  "t0": t_card, "t1": t_map, "xin": 0.5, "xout": 0.5})
    shots.append({"frames": f"maps/{frames}", "t0": t_map, "t1": t_lower, "xin": 0.5, "xout": 0.6})
    shots.extend(items)
    overlays.append({"type": "lower", "num": num, "text": lower or f"{name}, {sub}", "t0": t_lower + 0.1, "t1": t_end})

# ---------------- 00_hook (0:00-0:34.1) ----------------
shots += [
    shot("ark_10",   0.00,  2.90, IN(1.0, 1.10), 0.3, xin=0),     # most ancient places are ruins
    shot("byb_06",   2.90,  5.60, PAN(0.4, 0.6, 1.12), 0.3),       # visit, take a photo, leave
    shot("botin_03", 5.60,  7.70, IN(1.0, 1.10), 0.3),             # a few never closed
    shot("botin_13", 7.70,  9.20, IN(1.0, 1.08), 0.25),            # eat
    shot("kei_02",   9.20, 10.40, IN(1.0, 1.08), 0.25),            # sleep
    shot("pan_04",  10.40, 11.60, IN(1.0, 1.08), 0.25),            # pray
    shot("qar_14",  11.60, 12.80, IN(1.0, 1.08), 0.25),            # study
    shot("duj_02",  12.80, 15.10, IN(1.0, 1.10), 0.25),            # drink water
    shot("qan_14",  15.10, 18.80, TILT(0.35, 0.65, 1.1), 0.3),     # each older than the one before
    shot("botin_16", 18.80, 22.50, IN(1.0, 1.10), 0.3),            # a restaurant since 1725
    shot("byb_01",  22.50, 26.50, PAN(0.4, 0.6, 1.12), 0.3),       # a town 7,000 years old
    inset("cat_09",  26.50, 29.70, max_up=1.3, xin=0.3, xout=0.3), # the word Bible
    shot("ark_01",  29.70, 34.85, IN(1.0, 1.08), 0.3, xout=0.5),   # the oldest places still in use
]
overlays.append({"type": "brand", "t0": 30.40, "t1": 34.50, "fin": 0.9, "fout": 0.5})

# ---------------- 01_botin ----------------
place("#10", "SOBRINO DE BOTÍN", "MADRID, SPAIN", "frames_botin", 34.85, 37.975, 41.475, 91.275, [
    shot("botin_08", 41.475, 44.30, IN(1.0, 1.10)),                # Calle de Cuchilleros
    shot("botin_07", 44.30, 46.20, TILT(0.6, 0.4, 1.1)),           # street of the knife makers
    shot("botin_11", 46.20, 51.60, IN(1.0, 1.10)),                 # 1725, Jean Botín opens an inn
    shot("botin_04", 51.60, 56.90, PAN(0.6, 0.45, 1.12)),          # Guinness: oldest restaurant
    shot("botin_10", 56.90, 61.30, IN(1.0, 1.10)),                 # no meat or wine at first
    shot("botin_12", 61.30, 65.10, IN(1.0, 1.10)),                 # travellers brought their food
    shot("botin_09", 65.10, 69.90, TILT(0.6, 0.4, 1.05)),          # the business passed to a nephew
    shot("botin_14", 69.90, 75.30, PAN(0.35, 0.6, 1.12)),          # Sobrino de Botín: Botín's nephew
    shot("botin_02", 75.30, 80.20, IN(1.0, 1.12)),                 # the wood-fired oven (HORNO DE ASAR)
    shot("botin_17", 80.20, 84.00, IN(1.0, 1.10)),                 # suckling pig
    shot("botin_05", 84.00, 92.075, OUT(1.12, 1.0)),               # Hemingway, The Sun Also Rises
], badge="SINCE 1725 · ~300 YEARS")

# ---------------- 02_taos ----------------
place("#9", "TAOS PUEBLO", "NEW MEXICO, USA", "frames_taos", 92.075, 95.20, 98.70, 163.075, [
    shot("taos_01", 98.70, 104.00, PAN(0.4, 0.6, 1.12)),           # two great buildings of earth
    shot("taos_02", 104.00, 109.30, IN(1.0, 1.10)),                # built 1000-1450
    shot("taos_10", 109.30, 117.50, PAN(0.35, 0.65, 1.12)),        # oldest continuously inhabited
    shot("taos_07", 117.50, 121.60, IN(1.0, 1.10)),                # adobe: earth, water, straw
    shot("taos_03", 121.60, 127.30, IN(1.0, 1.10)),                # replastered with mud by hand
    shot("taos_08", 127.30, 134.60, TILT(0.55, 0.35, 1.12)),       # ladders, entered through the roof
    shot("taos_06", 134.60, 139.60, IN(1.0, 1.10)),                # about 150 people live inside
    inset("taos_13", 139.60, 144.80, max_up=1.4),                  # no electricity, no running water
    shot("taos_04", 144.80, 151.50, IN(1.0, 1.10)),                # a stream through the village
    shot("taos_12", 151.50, 156.00, IN(1.0, 1.10)),                # 1906: Blue Lake taken
    shot("taos_11", 156.00, 160.60, IN(1.0, 1.08)),                # fought for sixty years
    shot("taos_14", 160.60, 163.875, OUT(1.1, 1.0)),               # in 1970 they won
], badge="1000–1450 AD · ~1,000 YEARS")

# ---------------- 03_qarawiyyin ----------------
place("#8", "AL-QARAWIYYIN", "FEZ, MOROCCO", "frames_qarawiyyin", 163.875, 167.00, 170.50, 226.425, [
    shot("qar_09", 170.50, 177.20, PAN(0.3, 0.7, 1.05)),           # 859, Fez, Fatima al-Fihri
    shot("qar_10", 177.20, 184.10, IN(1.0, 1.10)),                 # from Kairouan; a merchant's daughter
    shot("qar_01", 184.10, 189.10, IN(1.0, 1.10)),                 # a mosque with a school
    shot("qar_03", 189.10, 194.10, IN(1.0, 1.10)),                 # a great centre of learning
    shot("qar_04", 194.10, 201.30, PAN(0.35, 0.65, 1.1)),          # Guinness: never stopped operating
    shot("qar_07", 201.30, 206.80, IN(1.35, 1.45, (0.5, 0.36))),   # 1963 state university (crop: no crowd)
    shot("qar_08", 206.80, 212.40, IN(1.0, 1.10)),                 # students still study here
    shot("qar_05", 212.40, 215.90, TILT(0.4, 0.6, 1.08)),          # one of the oldest libraries
    shot("qar_02", 215.90, 219.70, PAN(0.4, 0.6, 1.1)),            # reopened in 2016
    shot("qar_15", 219.70, 222.80, IN(1.0, 1.10)),                 # a hidden room
    shot("qar_12", 222.80, 227.225, OUT(1.12, 1.0)),               # carved wooden ceiling
], badge="SINCE 859 · ~1,170 YEARS")

# ---------------- 04_keiunkan ----------------
place("#7", "NISHIYAMA ONSEN KEIUNKAN", "YAMANASHI, JAPAN", "frames_keiunkan", 227.225, 230.35, 233.85, 293.875, [
    shot("kei_n_fuji", 233.85, 237.20, IN(1.0, 1.10)),             # Yamanashi, near Mount Fuji (ISS)
    shot("kei_03", 237.20, 240.70, IN(1.0, 1.10)),                 # hot water in a narrow valley
    shot("kei_01", 240.70, 248.70, IN(1.0, 1.10)),                 # 705: Fujiwara Mahito's inn
    shot("kei_04", 248.70, 252.90, IN(1.0, 1.10)),                 # thirteen centuries later
    shot("kei_02", 252.90, 257.60, PAN(0.4, 0.6, 1.1)),            # Guinness: oldest hotel
    shot("kei_10", 257.60, 261.70, IN(1.0, 1.08)),                 # same family, 52 generations
    shot("kei_11", 261.70, 268.60, IN(1.0, 1.10)),                 # adopted heirs
    shot("kei_n_fuji2", 268.60, 275.90, IN(1.0, 1.10)),            # Tokugawa Ieyasu stayed twice (Fuji from ISS)
    shot("kei_05", 275.90, 282.40, IN(1.0, 1.10)),                 # rebuilt; about 35 rooms
    shot("kei_08", 282.40, 288.50, IN(1.0, 1.10)),                 # natural hot spring water
    shot("kei_09", 288.50, 294.675, OUT(1.12, 1.0)),               # a thousand litres a minute
], badge="SINCE 705 · ~1,320 YEARS")

# ---------------- 05_catherine ----------------
place("#6", "SAINT CATHERINE'S MONASTERY", "SINAI, EGYPT", "frames_catherine", 294.675, 297.80, 301.30, 362.225, [
    shot("cat_01", 301.30, 304.20, IN(1.0, 1.08)),                 # a fortress in the desert
    shot("cat_03", 304.20, 312.30, PAN(0.4, 0.6, 1.1)),            # Justinian, 548-565
    shot("cat_02", 312.30, 316.60, IN(1.0, 1.10)),                 # oldest working monasteries
    shot("cat_05", 316.60, 320.90, IN(1.0, 1.10)),                 # monks for fifteen centuries
    shot("cat_04", 320.90, 325.40, IN(1.0, 1.10)),                 # never destroyed
    shot("cat_07", 325.40, 330.10, IN(1.0, 1.10)),                 # sacred to three faiths
    shot("cat_10", 330.10, 336.10, IN(1.0, 1.12)),                 # the burning bush
    shot("cat_11", 336.10, 341.40, TILT(0.6, 0.35, 1.05)),         # a small mosque within the walls
    shot("cat_13", 341.40, 349.30, IN(1.0, 1.10)),                 # the library
    inset("cat_08", 349.30, 356.40, max_up=1.2),                   # Codex Sinaiticus
    shot("cat_12", 356.40, 363.025, OUT(1.1, 1.0)),                # written by hand, 4th century
], badge="SINCE 565 · ~1,460 YEARS")

# ---------------- 06_pantheon ----------------
place("#5", "THE PANTHEON", "ROME, ITALY", "frames_pantheon", 363.025, 366.15, 369.65, 427.675, [
    shot("pan_01", 369.65, 374.00, IN(1.0, 1.10)),                 # Hadrian, around 125
    shot("pan_11", 374.00, 377.90, IN(1.0, 1.10)),                 # the inscription doesn't mention him
    shot("pan_02", 377.90, 385.50, PAN(0.35, 0.7, 1.12)),          # M·AGRIPPA
    shot("pan_07", 385.50, 388.00, PAN(0.3, 0.7, 1.0)),            # under the dome
    shot("pan_03", 388.00, 392.60, IN(1.0, 1.10)),                 # 43 metres across
    shot("pan_09", 392.60, 398.80, TILT(0.6, 0.4, 1.05)),          # largest unreinforced concrete dome
    shot("pan_05", 398.80, 403.70, IN(1.0, 1.12)),                 # the oculus
    shot("pan_06", 403.70, 408.90, TILT(0.35, 0.6, 1.05)),         # never had glass; rain
    shot("pan_14", 408.90, 412.70, IN(1.0, 1.10)),                 # small drains
    shot("pan_13", 412.70, 416.70, TILT(0.4, 0.6, 1.05)),          # never stopped being used
    shot("pan_15", 416.70, 422.40, IN(1.0, 1.10)),                 # 609: a church; Mass
    shot("pan_10", 422.40, 428.475, OUT(1.12, 1.0)),               # Raphael's tomb
], badge="~125 AD · ~1,900 YEARS")

# ---------------- 07_dujiangyan ----------------
place("#4", "DUJIANGYAN", "SICHUAN, CHINA", "frames_dujiangyan", 428.475, 431.60, 435.10, 494.075, [
    shot("duj_07", 435.10, 436.80, IN(1.0, 1.08)),                 # the Min River was a problem
    shot("duj_13", 436.80, 441.80, IN(1.0, 1.10)),                 # it flooded the plain
    shot("duj_10", 441.80, 444.60, IN(1.0, 1.08)),                 # dry the rest of the year
    shot("duj_11", 444.60, 449.60, IN(1.45, 1.55, (0.5, 0.3))),                 # governor Li Bing
    shot("duj_02", 449.60, 455.40, IN(1.0, 1.12)),                 # a levee shaped like a fish's head
    shot("duj_01", 455.40, 458.00, PAN(0.3, 0.7, 1.0)),            # the Fish Mouth splits the river
    shot("duj_dry", 458.00, 462.60, IN(1.0, 1.04), 0.4),           # scheme: dry season
    shot("duj_flood", 462.60, 467.00, IN(1.0, 1.04), 0.4),         # scheme: flood
    shot("duj_12", 467.00, 471.00, IN(1.0, 1.10)),                 # a channel through the mountain
    shot("duj_06", 471.00, 476.90, IN(1.0, 1.10)),                 # fire, then water
    shot("duj_15", 476.90, 479.80, IN(1.55, 1.62, (0.72, 0.5))),                 # about eight years
    shot("duj_08", 479.80, 483.40, IN(1.0, 1.10)),                 # it still works
    shot("duj_09", 483.40, 488.90, IN(1.0, 1.10)),                 # 668,000 hectares
    shot("duj_04", 488.90, 494.875, OUT(1.12, 1.0)),           # the Land of Abundance
], badge="SINCE 256 BC · ~2,280 YEARS")

# ---------------- 08_qanat ----------------
place("#3", "THE QANATS OF GONABAD", "KHORASAN, IRAN", "frames_qanat", 494.875, 498.00, 501.50, 563.825, [
    shot("qan_13", 501.50, 504.90, IN(1.0, 1.10)),                 # dry north-east of Iran
    shot("qan_08", 504.90, 508.90, IN(1.0, 1.10)),                 # green fields around Gonabad
    shot("qan_06", 508.90, 516.50, IN(1.0, 1.10)),                 # tunnels dug by hand
    shot("qan_15", 516.50, 518.40, IN(1.0, 1.08)),                 # this is a qanat
    shot("qan_10", 518.40, 525.90, IN(1.0, 1.10)),                 # a gently sloping tunnel
    shot("qan_11", 525.90, 528.40, PAN(0.3, 0.7, 1.0)),            # no pumps, no power
    shot("qanat_section", 528.40, 535.40, IN(1.0, 1.04), 0.4),     # scheme: shafts, tunnel, mother well
    shot("qan_09", 535.40, 540.80, IN(1.0, 1.10)),                 # a line of craters
    shot("qan_01", 540.80, 546.60, PAN(0.35, 0.65, 1.1)),          # Qasabeh: 33 km, 427 wells
    shot("qan_12", 546.60, 554.50, IN(1.0, 1.10)),         # mother well, ~300 m
    shot("qan_02", 554.50, 558.60, PAN(0.3, 0.7, 1.05)),           # still delivers water
    shot("qan_04", 558.60, 564.625, OUT(1.12, 1.0)),               # UNESCO, 2016
], badge="~500 BC · ~2,500 YEARS")

# ---------------- 09_arkadiko ----------------
place("#2", "ARKADIKO BRIDGE", "PELOPONNESE, GREECE", "frames_arkadiko", 564.625, 567.75, 571.25, 630.975, [
    shot("ark_04", 571.25, 575.20, IN(1.0, 1.10)),                 # beside a modern road
    shot("ark_02", 575.20, 579.60, IN(1.0, 1.10)),                 # 22 m long, 4 m high
    shot("ark_06", 579.60, 586.30, IN(1.0, 1.12)),                 # no mortar; limestone blocks
    shot("ark_11", 586.30, 593.10, IN(1.0, 1.10)),                 # the Cyclopes (Tiryns gallery)
    shot("ark_12", 593.10, 597.70, IN(1.0, 1.10)),                 # the Mycenaeans (Lion Gate)
    shot("ark_07", 597.70, 602.20, IN(1.0, 1.10)),                 # 1300-1190 BC
    shot("ark_10", 602.20, 606.30, PAN(0.4, 0.6, 1.1)),            # road between Tiryns and Epidaurus
    shot("ark_03", 606.30, 609.60, IN(1.0, 1.10)),                 # made for chariots
    shot("ark_08", 609.60, 615.20, IN(1.0, 1.12)),                 # a corbel arch
    shot("ark_09", 615.20, 618.50, IN(1.0, 1.10)),                 # the two sides meet at the top
    shot("ark_15", 618.50, 622.90, IN(1.0, 1.10)),                 # the Mycenaean world collapsed
    shot("ark_14", 622.90, 626.50, IN(1.0, 1.10)),                 # palaces burned
    shot("ark_05", 626.50, 631.775, OUT(1.12, 1.0)),               # still standing, still used
], badge="~1300 BC · ~3,300 YEARS")

# ---------------- 10_byblos ----------------
place("#1", "BYBLOS", "LEBANON", "frames_byblos", 631.775, 634.90, 638.40, 719.375, [
    shot("byb_02", 638.40, 642.30, IN(1.0, 1.10)),                 # a small harbour town
    shot("byb_03", 642.30, 644.40, IN(1.0, 1.08)),                 # you've used its name
    shot("byb_06", 644.40, 649.50, PAN(0.4, 0.6, 1.1)),            # about 7,000 years
    shot("byb_07", 649.50, 654.40, IN(1.0, 1.10)),                 # oldest continuously inhabited
    shot("byb_15", 654.40, 658.40, IN(1.0, 1.10)),                 # by 3000 BC a rich port
    shot("byb_12", 658.40, 662.30, IN(1.0, 1.10)),                 # cedar to Egypt
    shot("byb_16", 662.30, 666.70, IN(1.0, 1.10)),                 # papyrus
    shot("byb_05", 666.70, 673.90, PAN(0.4, 0.6, 1.1)),            # the Greeks called it Byblos
    inset("cat_08", 673.90, 681.10, max_up=1.2),                   # biblion, ta biblia, Bible
    shot("byb_11", 681.10, 688.60, IN(1.0, 1.10)),                 # 1923: the tomb of Ahiram
    shot("byb_09", 688.60, 694.40, PAN(0.35, 0.65, 1.1)),          # earliest Phoenician alphabet
    inset("byb_13", 694.40, 700.20, max_up=1.0),                   # ancestor of our letters
    shot("byb_10", 700.20, 709.30, IN(1.0, 1.12)),                 # the warning
    shot("byb_08", 709.30, 715.00, IN(1.0, 1.10)),                 # still a living town
    shot("byb_01", 715.00, 720.175, OUT(1.12, 1.0)),               # boats; 7,000 years of history
], badge="~5000 BC · ~7,000 YEARS")

# ---------------- 11_outro ----------------
shots.append(shot("pan_04", 720.175, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 720.8, "t1": DURATION, "fin": 1.2, "fout": 0.6})

# ---------------- checks ----------------
errors, last = [], {}
for s in sorted(shots, key=lambda s: s["t0"]):
    src = s.get("src") if not s.get("card") else None
    if not src: continue
    if not os.path.exists(os.path.join(HERE, src)): errors.append(f"missing {src}")
    if src in last and s["t0"] - last[src] < MIN_GAP:
        errors.append(f"repeat {src}: {last[src]:.1f}s -> {s['t0']:.1f}s")
    last[src] = s["t1"]
for s in shots:
    if "frames" in s and not os.path.isdir(os.path.join(HERE, s["frames"])): errors.append(f"missing {s['frames']}")
if errors and "--force" not in sys.argv:
    print("\n".join(errors), file=sys.stderr); sys.exit(1)
print(json.dumps({"duration": DURATION, "audio": "../voice/full.mp3", "shots": shots, "overlays": overlays}, indent=1))
