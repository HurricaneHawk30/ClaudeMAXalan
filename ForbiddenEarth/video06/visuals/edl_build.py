"""Edit decision list for video06 "Places That Look Like Another Planet" (11:33.6).
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 12 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 693.6

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

# ---------------- 00_hook (0:00-0:27.9) ----------------
shots += [
    shot("pam_02",   0.00,  5.10, IN(1.0, 1.10), 0.3, xin=0),      # white stone pours down a hillside
    shot("rio_03",   5.10,  8.00, IN(1.0, 1.10), 0.3),             # a river runs red
    shot("dal_02",   8.00, 12.90, IN(1.0, 1.10), 0.3),             # yellow and green pools
    shot("dev_n_2", 12.90, 16.00, IN(1.0, 1.10), 0.3),             # practice for Mars
    shot("ric_n_2", 16.00, 18.50, IN(1.0, 1.10), 0.3),             # ten places on our own planet
    shot("uyu_02",  18.50, 21.00, IN(1.0, 1.08), 0.3),             # ... that look like another one
    shot("dal_01",  21.00, 24.50, IN(1.0, 1.10), 0.3),             # number one: a hostile place
    shot("dvl_05",  24.50, 28.70, IN(1.0, 1.08), 0.3, xout=0.5),   # can anything live there
]
overlays.append({"type": "brand", "t0": 24.80, "t1": 28.40, "fin": 0.9, "fout": 0.5})

# ---------------- 01_pamukkale ----------------
place("#10", "PAMUKKALE", "DENIZLI, TURKEY", "frames_pamukkale", 28.70, 31.825, 35.325, 87.975, [
    shot("pam_01", 35.325, 38.30, IN(1.0, 1.10)),                  # like snow in summer
    shot("pam_11", 38.30, 40.50, TILT(0.6, 0.4, 1.05)),            # up close it's stone
    shot("pam_09", 40.50, 47.60, IN(1.0, 1.10)),                   # hot springs, cliff of 200 m
    shot("pam_03", 47.60, 51.50, PAN(0.4, 0.6, 1.1)),              # carbon dioxide escapes
    shot("pam_05", 51.50, 57.00, IN(1.0, 1.12)),                   # a soft white gel hardens
    shot("pam_04", 57.00, 59.00, IN(1.0, 1.08)),                   # travertine
    shot("pam_08", 59.00, 63.90, PAN(0.4, 0.6, 1.1)),              # a staircase of terraces
    shot("pam_14", 63.90, 67.80, TILT(0.4, 0.6, 1.05)),            # up to six metres tall
    shot("pam_13", 67.80, 72.10, IN(1.0, 1.10)),                   # Cotton Castle
    shot("pam_07", 72.10, 75.80, IN(1.0, 1.10)),                   # bathed here for 2,000 years
    shot("pam_10", 75.80, 80.00, IN(1.0, 1.10)),                   # Hierapolis
    shot("pam_06", 80.00, 84.00, IN(1.0, 1.08)),                   # walk the terraces barefoot
    shot("pam_12", 84.00, 88.775, OUT(1.12, 1.0)),                 # the hotels were torn down
], badge="COTTON CASTLE")

# ---------------- 02_danxia ----------------
place("#9", "ZHANGYE DANXIA", "GANSU, CHINA", "frames_danxia", 88.775, 91.90, 95.40, 146.125, [
    shot("dan_01", 95.40, 98.00, IN(1.0, 1.08)),                   # the hills are striped
    shot("dan_06", 98.00, 103.70, PAN(0.35, 0.65, 1.12)),          # red, orange, yellow, white
    shot("dan_05", 103.70, 108.80, IN(1.0, 1.10)),                 # they're real
    shot("dan_07", 108.80, 112.00, IN(1.0, 1.08)),                 # iron and other elements
    shot("dan_04", 112.00, 118.40, PAN(0.4, 0.6, 1.1)),            # pushed up and tilted
    shot("dan_11", 118.40, 125.30, IN(1.0, 1.10)),                 # frozen waves of colour
    shot("dan_12", 125.30, 128.10, IN(1.0, 1.08)),                 # brightest after rain
    shot("dan_02", 128.10, 132.20, IN(1.0, 1.10)),                 # at sunset the stripes burn
    shot("dan_03", 132.20, 135.20, IN(1.0, 1.08)),                 # Danxia landscape
    shot("dan_09", 135.20, 138.80, PAN(0.4, 0.6, 1.1)),            # one of the most famous
    shot("dan_13", 138.80, 142.80, IN(1.0, 1.08)),                 # a national geopark
    shot("dan_10", 142.80, 146.925, OUT(1.12, 1.0)),               # don't wear the colours away
], badge="RAINBOW MOUNTAINS")

# ---------------- 03_spotted ----------------
place("#8", "SPOTTED LAKE", "BRITISH COLUMBIA, CANADA", "frames_spotted", 146.925, 150.05, 153.55, 204.80, [
    shot("spo_01", 153.55, 157.80, IN(1.0, 1.10)),                 # the skin of a leopard
    shot("spo_02", 157.80, 164.90, IN(1.0, 1.12)),                 # magnesium sulfate
    shot("spo_14", 164.90, 170.80, PAN(0.4, 0.6, 1.1)),            # separate pools
    shot("spo_08", 170.80, 174.80, IN(1.0, 1.10)),                 # each a different colour
    shot("spo_05", 174.80, 179.90, PAN(0.35, 0.65, 1.1)),          # natural walkways
    shot("spo_04", 179.90, 186.90, IN(1.0, 1.08)),                 # Kliluk, a sacred lake
    shot("spo_10", 186.90, 192.60, IN(1.0, 1.08)),                 # First World War
    shot("spo_12", 192.60, 198.10, PAN(0.4, 0.6, 1.1)),            # the Okanagan Nation bought it
    shot("spo_03", 198.10, 202.00, IN(1.0, 1.10)),                 # fenced off
    shot("spo_11", 202.00, 205.60, OUT(1.1, 1.0)),                 # off-limits
], badge="OFF-LIMITS")

# ---------------- 04_deadvlei ----------------
place("#7", "DEADVLEI", "NAMIB DESERT, NAMIBIA", "frames_deadvlei", 205.60, 208.725, 212.225, 264.925, [
    shot("dvl_07", 212.225, 219.20, IN(1.0, 1.12)),                # a white clay pan among dunes
    shot("dvl_15", 219.20, 222.60, IN(1.0, 1.08)),                 # Big Daddy
    shot("dvl_11", 222.60, 229.20, PAN(0.4, 0.6, 1.1)),            # black, twisted trees
    shot("dvl_01", 229.20, 235.90, IN(1.0, 1.10)),                 # camel thorn, dead for centuries
    shot("dvl_n_1", 235.90, 240.40, IN(1.12, 1.2)),                # the Tsauchab River (ISS)
    shot("dvl_17", 240.40, 246.30, PAN(0.4, 0.6, 1.1)),            # the dunes moved in
    shot("dvl_03", 246.30, 252.20, IN(1.0, 1.10)),                 # never fell, never rotted
    shot("dvl_08", 252.20, 255.40, IN(1.0, 1.08)),                 # the air is so dry
    shot("dvl_02", 255.40, 257.60, IN(1.0, 1.08)),                 # burned black
    shot("dvl_04", 257.60, 262.00, IN(1.0, 1.10)),                 # orange, white, black, blue
    shot("dvl_14", 262.00, 265.725, OUT(1.1, 1.0)),                # every photo looks fake
], badge="TREES DEAD ~700 YEARS")

# ---------------- 05_socotra ----------------
place("#6", "SOCOTRA", "YEMEN", "frames_socotra", 265.725, 268.85, 272.35, 332.40, [
    shot("soc_n_1", 272.35, 278.60, IN(1.0, 1.10)),                # an island cut off (ISS)
    shot("soc_03", 278.60, 280.80, IN(1.0, 1.08)),                 # life went its own way
    shot("soc_13", 280.80, 288.10, PAN(0.35, 0.65, 1.1)),          # 37% of plants nowhere else
    shot("soc_11", 288.10, 294.40, IN(1.0, 1.10)),                 # reptiles, land snails
    shot("soc_01", 294.40, 297.90, IN(1.0, 1.10)),                 # the dragon's blood tree
    shot("soc_04", 297.90, 304.40, IN(1.0, 1.10)),                 # an open umbrella
    inset("soc_08", 304.40, 309.50, max_up=1.5),                   # catches moisture from the mist
    shot("soc_18", 309.50, 315.90, IN(1.0, 1.12)),                 # dark red resin
    shot("soc_09", 315.90, 319.50, TILT(0.4, 0.6, 1.05)),          # bottle trees
    shot("soc_10", 319.50, 323.20, TILT(0.4, 0.6, 1.05)),          # swollen trunks
    shot("soc_06", 323.20, 328.20, IN(1.0, 1.10)),                 # UNESCO, 2008
    shot("soc_12", 328.20, 333.20, OUT(1.12, 1.0)),                # hardest places to visit
], badge="37% OF PLANTS FOUND NOWHERE ELSE")

# ---------------- 06_uyuni ----------------
place("#5", "SALAR DE UYUNI", "BOLIVIA", "frames_uyuni", 333.20, 336.325, 339.825, 403.35, [
    shot("uyu_07", 339.825, 345.00, IN(1.0, 1.10)),                # the largest salt flat
    shot("uyu_n_3", 345.00, 348.70, IN(1.0, 1.10)),                # 10,000 km2 (ISS)
    shot("uyu_12", 348.70, 352.80, IN(1.0, 1.10)),                 # ancient lakes dried up
    shot("uyu_08", 352.80, 359.30, PAN(0.4, 0.6, 1.1)),            # flat to within a metre
    shot("uyu_06", 359.30, 365.10, IN(1.0, 1.12)),                 # hexagons
    shot("uyu_04", 365.10, 370.60, IN(1.0, 1.10)),                 # a few centimetres of water
    shot("uyu_02", 370.60, 376.40, IN(1.0, 1.10)),                 # the largest mirror on Earth
    shot("uyu_01", 376.40, 381.00, PAN(0.4, 0.6, 1.1)),            # clouds under your feet
    shot("uyu_09", 381.00, 387.60, IN(1.0, 1.08)),                 # useful beyond photos
    shot("uyu_n_1", 387.60, 394.20, IN(1.0, 1.10)),                # calibrating satellites (ISS)
    shot("uyu_n_2", 394.20, 398.30, IN(1.0, 1.12)),                # lithium (extraction ponds, ISS)
    shot("uyu_10", 398.30, 404.15, OUT(1.12, 1.0)),                # batteries of phones and cars
], badge="WORLD'S LARGEST MIRROR")

# ---------------- 07_richat ----------------
place("#4", "EYE OF THE SAHARA", "MAURITANIA", "frames_richat", 404.15, 407.275, 410.775, 471.175, [
    shot("ric_n_2", 410.775, 414.60, IN(1.0, 1.12)),               # a giant target
    shot("ric_n_8", 414.60, 418.50, IN(1.0, 1.10)),                # 40 km across
    shot("ric_n_7", 418.50, 422.40, IN(1.0, 1.08)),                # hard to see from the ground
    shot("ric_n_9", 422.40, 425.40, IN(1.0, 1.08)),                # impossible to miss from orbit
    shot("ric_02", 425.40, 429.90, IN(1.0, 1.10)),                 # a landmark for shuttle crews
    shot("ric_03", 429.90, 436.90, IN(1.0, 1.12)),                 # Richat: a crater?
    shot("ric_n_5", 436.90, 439.30, IN(1.0, 1.08)),                # no sign of an impact
    shot("ric_n_3", 439.30, 445.60, IN(1.0, 1.08)),                # a dome pushed up
    shot("ric_n_6", 445.60, 451.30, IN(1.0, 1.10)),                # layers exposed in rings
    shot("ric_04", 451.30, 454.80, IN(1.0, 1.10)),                 # like a cut onion
    shot("ric_n_1", 454.80, 462.30, IN(1.0, 1.10)),                # Atlantis? (same view, no "city")
    inset("ric_05", 462.30, 464.20, max_up=1.0),                   # no evidence
    shot("ric_n_4", 464.20, 471.975, IN(1.12, 1.2)),               # a mountain erased by wind
], badge="40 KM ACROSS")

# ---------------- 08_riotinto ----------------
place("#3", "RIO TINTO", "ANDALUSIA, SPAIN", "frames_riotinto", 471.975, 475.10, 478.60, 538.70, [
    shot("rio_03", 478.60, 483.50, IN(1.0, 1.10)),                 # a river runs red
    shot("rio_10", 483.50, 489.80, IN(1.0, 1.12)),                 # acidic as vinegar, iron
    shot("rio_12", 489.80, 495.10, PAN(0.4, 0.6, 1.1)),            # mined for 5,000 years
    shot("rio_11", 495.10, 501.10, IN(1.0, 1.10)),                 # the company took its name
    shot("rio_02", 501.10, 507.20, IN(1.0, 1.10)),                 # acidic before the digging
    shot("rio_05", 507.20, 511.80, IN(1.0, 1.10)),                 # nothing could live here?
    shot("rio_06", 511.80, 517.40, IN(1.0, 1.12)),                 # microbes on iron and sulfur
    shot("rio_14", 517.40, 520.20, IN(1.0, 1.08)),                 # they give it its colour
    shot("rio_n_1", 520.20, 522.80, IN(1.0, 1.10)),                # NASA is interested
    shot("rio_01", 522.80, 526.70, IN(1.0, 1.10)),                 # jarosite
    shot("rio_n_mars2", 526.70, 529.40, IN(1.0, 1.10)),            # also found on Mars
    shot("rio_07", 529.40, 534.00, PAN(0.4, 0.6, 1.1)),            # testing drills
    inset("rio_n_mars3", 534.00, 536.50, max_up=1.0),              # the search for life on Mars
    shot("rio_09", 536.50, 539.50, OUT(1.1, 1.0)),                 # in a river in Spain
], badge="USED TO PRACTICE FOR MARS")

# ---------------- 09_devon ----------------
place("#2", "DEVON ISLAND", "NUNAVUT, CANADA", "frames_devon", 539.50, 542.625, 546.125, 600.625, [
    shot("dev_01", 546.125, 548.50, TILT(0.6, 0.4, 1.05)),         # largest uninhabited island
    shot("dev_08", 548.50, 551.90, IN(1.0, 1.08)),                 # no towns, no roads
    shot("dev_02", 551.90, 555.90, IN(1.0, 1.10)),                 # cold, dry, brown rock
    inset("dev_n_1", 555.90, 561.70, max_up=1.2),                  # a crater 20 km wide (Landsat)
    shot("dev_03", 561.70, 564.90, IN(1.0, 1.08)),                 # Haughton Crater
    shot("dev_05", 564.90, 569.80, IN(1.0, 1.10)),                 # a description of Mars
    shot("dev_n_2", 569.80, 577.00, IN(1.0, 1.10)),                # Haughton-Mars Project
    shot("dev_n_3", 577.00, 580.50, IN(1.0, 1.08)),                # rovers
    shot("dev_n_5", 580.50, 583.90, IN(1.0, 1.08)),                # equipment
    shot("dev_13", 583.90, 588.50, IN(1.0, 1.10)),                 # the Mars Society station
    shot("dev_12", 588.50, 592.90, PAN(0.3, 0.7, 1.0)),            # crews live like Mars explorers
    shot("dev_09", 592.90, 597.90, IN(1.0, 1.10)),                 # if humans ever walk on Mars
    shot("dev_07", 597.90, 601.425, OUT(1.1, 1.0)),                # an island where nobody lives
], badge="MARS ON EARTH")

# ---------------- 10_dallol ----------------
place("#1", "DALLOL", "DANAKIL DEPRESSION, ETHIOPIA", "frames_dallol", 601.425, 604.55, 608.05, 674.10, [
    shot("dal_12", 608.05, 613.00, IN(1.0, 1.10)),                 # 125 m below sea level
    shot("dal_14", 613.00, 615.00, IN(1.0, 1.08)),                 # one of the hottest places
    shot("dal_03", 615.00, 620.60, IN(1.0, 1.10)),                 # water rises through salt
    shot("dal_01", 620.60, 625.70, IN(1.0, 1.10)),                 # doesn't look like Earth
    shot("dal_04", 625.70, 629.00, IN(1.0, 1.10)),                 # yellow crusts, green pools
    shot("dal_10", 629.00, 633.20, IN(1.0, 1.10)),                 # salt chimneys, hissing
    shot("dal_05", 633.20, 635.30, IN(1.0, 1.08)),                 # chemistry
    shot("dal_11", 635.30, 638.50, IN(1.0, 1.08)),                 # close to boiling
    shot("dal_02", 638.50, 642.80, IN(1.0, 1.10)),                 # pH of about 0.25
    shot("dal_06", 642.80, 647.00, IN(1.0, 1.10)),                 # more acidic than battery acid
    shot("dal_16", 647.00, 652.50, IN(1.0, 1.10)),                 # a limit to life?
    shot("dal_08", 652.50, 656.00, IN(1.0, 1.08)),                 # tiny microbes
    shot("dal_09", 656.00, 659.50, IN(1.0, 1.08)),                 # or nothing at all
    shot("dal_15", 659.50, 662.20, IN(1.0, 1.08)),                 # the debate isn't over
    shot("dal_17", 662.20, 667.00, IN(1.0, 1.10)),                 # the salt flats nearby
    shot("dal_07", 667.00, 674.90, OUT(1.1, 1.0)),                 # salt cut by hand (salt plain; no free caravan photo)
], badge="pH 0.25")

# ---------------- 11_outro ----------------
shots.append(shot("uyu_11", 674.90, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 675.5, "t1": DURATION, "fin": 1.2, "fout": 0.6})

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
