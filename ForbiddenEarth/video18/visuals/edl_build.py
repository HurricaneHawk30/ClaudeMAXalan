"""Edit decision list for video18 "15 Most Guarded Places on Earth".
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt. Stills live in src/<place>/<key>.<ext> (task 24 candidates).
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 950.7

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

# ---------------- 00_hook (0:00-0:29.85) ----------------
shots += [
    shot("boe_01",  0.00,  8.30, IN(1.0, 1.08), 0.3, xin=0),     # never allowed to enter
    shot("boe_15",  8.30, 12.20, IN(1.0, 1.10), 0.25),           # billions in gold under a busy street
    shot("cht_09", 12.20, 16.90, IN(1.0, 1.10), 0.25),           # guarded by a single monk
    shot("dmz_07", 16.90, 20.50, IN(1.0, 1.10), 0.25),           # a border where nature took over
    shot("knx_10", 20.50, 29.85, IN(1.0, 1.12), 0.3, xout=0.5),  # number one: a vault
]
overlays.append({"type": "brand", "t0": 25.00, "t1": 29.50, "fin": 0.9, "fout": 0.5})

P("#15", "MOUNT ATHOS", "GREECE", "frames_athos", 29.85, 88.2,
  ["ath_08", "ath_13", "ath_02", "ath_12", "ath_14", "ath_09", "ath_10", "ath_05", "ath_07", "ath_03", "ath_04", "ath_11", "ath_06"],
  "NO WOMEN FOR 1,000 YEARS")
P("#14", "DAISEN KOFUN", "JAPAN", "frames_daisen", 88.2, 147.05,
  ["dai_15", "dai_03", "dai_05", "dai_n1", "dai_01", "dai_08", "dai_12", "dai_02", "dai_07", "MAP"],
  "NO ONE MAY ENTER")
P("#13", "LOP NUR", "CHINA", "frames_lop_nur", 147.05, 209.05,
  ["lop_03", "lop_n1", "lop_07", "lop_12", "lop_06", "lop_09", "lop_14", "lop_01", "lop_04", "lop_11", "lop_05", "lop_13", "lop_10", "lop_08", "lop_15"],
  "45 NUCLEAR TESTS")
P("#12", "PORTON DOWN", "ENGLAND", "frames_porton_down", 209.05, 272.75,
  ["por_01", "por_04", "MAP", "por_11", "por_02", "por_05", "por_12", "por_08", "por_10"],
  "SINCE 1916")
P("#11", "RAF MENWITH HILL", "ENGLAND", "frames_menwith_hill", 272.75, 331.2,
  ["men_05", "men_01", "men_02", "men_09", "men_04", "men_06", "men_07", "men_08", "men_03"],
  "DOZENS OF DOMES")
P("#10", "PINE GAP", "AUSTRALIA", "frames_pine_gap", 331.2, 387.075,
  ["pin_05", "pin_13", "pin_15", "pin_06", "pin_n1", "pin_04", "pin_10", "pin_14", "pin_08"],
  "SINCE 1966")
P("#9", "DIEGO GARCIA", "INDIAN OCEAN", "frames_diego_garcia", 387.075, 451.475,
  ["dgo_02", "dgo_08", "dgo_n2", "dgo_11", "dgo_05", "dgo_14", "dgo_03", "dgo_06", "dgo_12", "dgo_n1"],
  "NO VISITORS")
P("#8", "THE GREAT TABOO", "MONGOLIA", "frames_great_taboo", 451.475, 509.35,
  ["tab_n1", "tab_02", "tab_14", "tab_05", "tab_03", "tab_09", "MAP", "tab_12", "tab_11"],
  "240 KM² FORBIDDEN")
P("#7", "METRO-2", "RUSSIA", "frames_metro2", 509.35, 571.675,
  ["met_09", "met_02", "met_13", "met_04", "met_01", "met_12", "met_07", "met_10", "met_03", "met_06", "met_11", "met_08", "met_14", "met_n1"],
  "NEVER CONFIRMED")
P("#6", "MOUNT YAMANTAU", "RUSSIA", "frames_yamantau", 571.675, 628.55,
  ["yam_01", "yam_10", "yam_04", "yam_03", "yam_05", "yam_06", "yam_02", "yam_12", "yam_09", "yam_11", "yam_13", "yam_15"],
  "CLOSED TOWN")
P("#5", "VATICAN APOSTOLIC ARCHIVE", "VATICAN CITY", "frames_vatican_archive", 628.55, 690.2,
  ["vat_03", "vat_14", "vat_05", "vat_02", "vat_08", "vat_01", "vat_07", "vat_11", "vat_12", "MAP"],
  "85 KM OF SHELVES")
P("#4", "BANK OF ENGLAND", "LONDON", "frames_bank_of_england", 690.2, 746.85,
  ["boe_04", "boe_06", "boe_02", "boe_n1", "boe_07", "boe_03", "boe_11", "boe_10", "boe_05", "boe_13", "boe_08", "boe_09", "boe_14"],
  "400,000 GOLD BARS")
P("#3", "CHAPEL OF THE TABLET", "ETHIOPIA", "frames_chapel_of_tablet", 746.85, 802.9,
  ["cht_03", "cht_01", "cht_05", "cht_06", "cht_13", "cht_04", "cht_07", "cht_08", "cht_02", "cht_11", "cht_12"],
  "ONE GUARDIAN")
P("#2", "KOREAN DMZ", "KOREAN PENINSULA", "frames_korean_dmz", 802.9, 860.45,
  ["dmz_n2", "dmz_11", "MAP", "dmz_13", "dmz_15", "dmz_05", "dmz_09", "dmz_02", "dmz_n1"],
  "2 MILLION MINES")
P("#1", "FORT KNOX", "USA", "frames_fort_knox", 860.45, 936.825,
  ["knx_06", "knx_10", "knx_02", "knx_01", "boe_07", "knx_04", "MAP", "knx_09", "boe_15", "knx_13"],
  "HALF THE NATION'S GOLD")

# ---------------- 16_outro ----------------
shots.append(shot("men_05", 936.825, DURATION, IN(1.0, 1.06), xout=0))
overlays.append({"type": "endcard", "t0": 937.325, "t1": DURATION, "fin": 1.2, "fout": 0.6})
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
