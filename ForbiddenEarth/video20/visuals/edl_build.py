"""Edit decision list for video20 "10 Abandoned Places Nature Took Back".
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 26 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 651.7

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

# Shots inside each place are spread evenly between the lower third and the next section, in the order of the narration.
# "MAP" repeats the end frame of that place's map zoom.
MOVES = [IN(1.0, 1.10), IN(1.0, 1.08), PAN(0.35, 0.65, 1.12), IN(1.0, 1.10), TILT(0.35, 0.6, 1.1), IN(1.0, 1.08)]

def seq(keys, t0, t1, frames):
    n = len(keys); step = (t1 - t0) / n; out = []
    for i, k in enumerate(keys):
        a, b = t0 + i * step, (t1 if i == n - 1 else t0 + (i + 1) * step)
        if k == "MAP":
            out.append({"frames": f"maps/{frames}", "t0": a, "t1": b, "f0": 104, "xin": 0.6, "xout": 0.6})
        else:
            out.append(shot(k, a, b, OUT(1.12, 1.0) if i == n - 1 else MOVES[i % len(MOVES)]))
    return out

def P(num, name, sub, frames, card, nxt, keys, badge):
    place(num, name, sub, frames, card, card + 3.125, card + 6.625, nxt - 0.8, seq(keys, card + 6.625, nxt, frames), badge=badge)

HK = [0.0, 3.0, 5.95, 9.2, 13.6, 19.65]   # refined from words_full.json

# ---------------- 00_hook ----------------
shots += [
    shot("ros_17", HK[0], HK[1], IN(1.0, 1.08), 0.3, xin=0),   # when people leave, nature doesn't wait
    shot("ayr_05", HK[1], HK[2], IN(1.0, 1.10), 0.25),          # a ship that turned into a floating forest
    shot("cmc_13", HK[2], HK[3], IN(1.0, 1.10), 0.25),          # a church with trees growing out of its roof
    shot("for_01", HK[3], HK[4], IN(1.0, 1.10), 0.25),          # Henry Ford's dream town in the Amazon
    shot("hou_09", HK[4], HK[5], IN(1.0, 1.12), 0.3, xout=0.5), # a village under a blanket of green
]
overlays.append({"type": "brand", "t0": 15.0, "t1": 19.3, "fin": 0.9, "fout": 0.5})

P("#10", "BANNERMAN'S CASTLE", "USA", "frames_bannerman", 19.65, 83.0,
  ["ban_01", "ban_09", "ban_10", "ban_02", "ban_07", "ban_15", "ban_03", "ban_06", "ban_n1", "MAP", "ban_11", "ban_16"],
  "ABANDONED ARSENAL")
P("#9", "SS AYRFIELD", "AUSTRALIA", "frames_ayrfield", 83.0, 139.9,
  ["ayr_01", "ayr_07", "ayr_18", "ayr_08", "ayr_02", "ayr_04", "ayr_10", "ayr_06", "ayr_13", "ayr_09", "ayr_03"],
  "FLOATING FOREST")
P("#8", "KAYAKÖY", "TURKEY", "frames_kayakoy", 139.9, 202.875,
  ["kay_06", "kay_03", "kay_01", "kay_13", "kay_14", "kay_12", "MAP", "kay_07", "kay_04", "kay_10", "kay_16", "kay_17", "kay_09"],
  "EMPTY SINCE 1923")
P("#7", "CITY METHODIST CHURCH", "USA", "frames_city_methodist", 202.875, 260.675,
  ["cmc_01", "cmc_07", "cmc_10", "cmc_15", "cmc_03", "cmc_05", "cmc_02", "cmc_16", "cmc_04", "cmc_13", "cmc_12", "cmc_18"],
  "CLOSED IN 1975")
P("#6", "ROSS ISLAND", "INDIA", "frames_ross_island", 260.675, 327.35,
  ["ros_15", "ros_n2", "ros_04", "ros_01", "ros_n3", "ros_06", "ros_02", "ros_09", "ros_08", "ros_16", "ros_12", "ros_n1", "ros_13", "ros_11"],
  "TAKEN BY TREES")
P("#5", "FORDLÂNDIA", "BRAZIL", "frames_fordlandia", 327.35, 394.95,
  ["for_02", "for_17", "MAP", "for_01", "for_07", "for_n2", "for_04", "for_08", "for_n1"],
  "$20 MILLION LOST")
P("#4", "CRACO", "ITALY", "frames_craco", 394.95, 453.2,
  ["cra_04", "cra_01", "cra_03", "cra_07", "cra_09", "cra_13", "cra_11", "MAP", "cra_06", "cra_14", "cra_16", "cra_12", "cra_08", "cra_17", "cra_18", "cra_02"],
  "EMPTY SINCE 1963")
P("#3", "KOLMANSKOP", "NAMIBIA", "frames_kolmanskop", 453.2, 512.775,
  ["kol_15", "kol_09", "kol_01", "kol_05", "kol_10", "kol_14", "kol_06", "kol_17", "kol_02", "kol_13", "kol_18", "kol_11", "kol_03"],
  "SWALLOWED BY SAND")
P("#2", "TA PROHM", "CAMBODIA", "frames_ta_prohm", 512.775, 573.475,
  ["tap_09", "tap_06", "tap_02", "tap_12", "tap_07", "tap_03", "tap_04", "tap_15", "tap_11", "tap_05", "tap_01", "tap_08", "tap_14", "tap_18"],
  "ROOTS OVER STONE")
P("#1", "HOUTOUWAN", "CHINA", "frames_houtouwan", 573.475, 638.15,
  ["hou_06", "hou_01", "hou_09", "hou_03", "hou_04", "hou_13", "hou_n1", "MAP", "hou_07", "hou_n2", "hou_n6"],
  "GREEN GHOST VILLAGE")

# ---------------- 11_outro ----------------
shots.append(shot("hou_05", 638.15, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 638.65, "t1": DURATION, "fin": 1.2, "fout": 0.6})
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
