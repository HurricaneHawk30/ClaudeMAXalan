"""Edit decision list for video19 "10 Lost Treasures No One Has Ever Found".
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 25 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 679.8

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

HK1, HK2, HK3 = 5.95, 9.5, 15.3
DUT = ["dut_04", "dut_01", "dut_10", "dut_02", "dut_05", "dut_13", "dut_12", "dut_09", "dut_06", "dut_14", "dut_16", "dut_17", "dut_11", "dut_18"]
AMB = ["amb_r5", "amb_02", "amb_04", "amb_01", "amb_r4", "amb_11", "MAP", "amb_16", "amb_03", "amb_08", "amb_12", "amb_r3", "amb_r2", "amb_r6", "amb_r1"]

# ---------------- 00_hook (0:00-0:23.2) ----------------
shots += [
    shot("kjo_01",  0.00, HK1, IN(1.0, 1.08), 0.3, xin=0),       # some treasures were never found / swallowed by the tide
    shot("flo_07",  HK1, HK2, IN(1.0, 1.10), 0.25),               # a ship carrying the riches of a kingdom
    shot("iri_10",  HK2, HK3, IN(1.0, 1.10), 0.25),               # royal jewels stolen from a castle
    shot("amb_04",  HK3, 23.225, IN(1.0, 1.12), 0.3, xout=0.5),  # a whole room of amber and gold
]
overlays.append({"type": "brand", "t0": 18.6, "t1": 22.9, "fin": 0.9, "fout": 0.5})

P("#10", "KING JOHN'S CROWN JEWELS", "ENGLAND", "frames_king_john", 23.225, 81.775,
  ["kjo_02", "kjo_04", "kjo_18", "kjo_09", "kjo_11", "kjo_15", "kjo_05", "MAP", "kjo_08", "kjo_13", "kjo_14"],
  "LOST IN 1216")
P("#9", "THE KRUGER MILLIONS", "SOUTH AFRICA", "frames_kruger", 81.775, 144.0,
  ["kru_04", "kru_09", "kru_05", "kru_10", "kru_07", "kru_02", "kru_12", "kru_13", "kru_14", "kru_18", "kru_03", "kru_17"],
  "NEVER FOUND")
P("#8", "LAKE TOPLITZ", "AUSTRIA", "frames_toplitz", 144.0, 210.625,
  ["top_01", "top_16", "top_08", "top_13", "top_04", "top_15", "top_07", "top_10", "top_12", "top_02", "top_17", "top_14"],
  "DIVING BANNED")
P("#7", "LOST DUTCHMAN'S MINE", "USA", "frames_lost_dutchman", 210.625, 277.075,
  DUT, "THOUSANDS HAVE SEARCHED")
P("#6", "IRISH CROWN JEWELS", "IRELAND", "frames_irish_jewels", 277.075, 339.775,
  ["iri_17", "iri_02", "iri_07", "iri_14", "iri_04", "iri_06", "iri_13", "iri_11", "iri_01", "iri_09", "iri_15", "iri_18"],
  "STOLEN IN 1907")
P("#5", "FLOR DE LA MAR", "STRAIT OF MALACCA", "frames_flor_de_la_mar", 339.775, 404.35,
  ["flo_03", "flo_13", "flo_06", "flo_11", "flo_01", "flo_17", "flo_02", "MAP", "flo_14", "flo_16", "flo_12", "flo_18"],
  "WORTH BILLIONS?")
P("#4", "NAZI GOLD TRAIN", "POLAND", "frames_gold_train", 404.35, 467.15,
  ["gol_08", "gol_09", "gol_10", "gol_11", "gol_06", "gol_15", "gol_13", "gol_02", "gol_16", "MAP", "gol_03", "gol_14", "gol_18"],
  "DUG UP IN 2016")
P("#3", "TREASURE OF LIMA", "COCOS ISLAND", "frames_cocos_island", 467.15, 531.525,
  ["coc_04", "coc_12", "coc_08", "coc_16", "MAP", "coc_06", "coc_02", "coc_14", "coc_17", "coc_18", "coc_01"],
  "BANNED TO DIG")
P("#2", "OAK ISLAND", "CANADA", "frames_oak_island", 531.525, 595.725,
  ["oak_09", "oak_14", "oak_01", "oak_04", "oak_07", "oak_15", "oak_12", "oak_18", "oak_13", "oak_06", "oak_17", "oak_02"],
  "6 MEN DIED")
P("#1", "THE AMBER ROOM", "RUSSIA", "frames_amber_room", 595.725, 665.825,
  AMB, "VANISHED IN 1945")

# ---------------- 11_outro ----------------
shots.append(shot("coc_10", 665.825, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 666.325, "t1": DURATION, "fin": 1.2, "fout": 0.6})
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
