"""Edit decision list for the preview (00_hook + 01_gruinard, 0:00-1:32.5).
Times are aligned to word timestamps of voice/full.mp3 (see work/words.json).
python edl_build.py > edl.json
"""
import json

IN = lambda s0=1.0, s1=1.10, c0=(0.5, 0.5), c1=None: {"s0": s0, "s1": s1, "c0": list(c0), "c1": list(c1 or c0)}
OUT = lambda s0=1.12, s1=1.0, c0=(0.5, 0.5), c1=None: {"s0": s0, "s1": s1, "c0": list(c0), "c1": list(c1 or c0)}
PAN = lambda a, b, s=1.15, y=0.5: {"s0": s, "s1": s, "c0": [a, y], "c1": [b, y]}

def shot(src, t0, t1, move, x=0.6, **kw):
    return {"src": f"src/{src}", "t0": t0, "t1": t1, "move": move, "xin": x, "xout": x, **kw}

shots = [
    # ---- 00_hook: fast cuts across the countdown ----
    shot("nyos_usgs.jpg",       0.00,  2.95, IN(1.0, 1.12), 0.3, xin=0),       # "a lake that killed 1,746 people"
    shot("nyos_1986.jpg",       2.95,  5.80, PAN(0.38, 0.62, 1.18), 0.3),      # "in a single night"
    shot("centralia_fire.jpg",  5.80, 10.10, IN(1.0, 1.15, (0.4, 0.55), (0.3, 0.6)), 0.3), # "a town ... burning underground since 1962"
    shot("gru_gerrard.jpg",    10.10, 15.50, IN(1.0, 1.16, (0.32, 0.55)), 0.3),# "an island so deadly ..."
    shot("ijen_fire2.jpg",      15.50, 18.10, IN(1.0, 1.10), 0.3),              # "never heard of most of them"
    shot("zone_forest.jpg",    18.10, 19.40, PAN(0.42, 0.55, 1.12), 0.2),      # "we count down ten ..."
    shot("plymouth_buried.jpg",       19.40, 20.70, IN(1.04, 1.12), 0.2),
    shot("witt_sign.jpg",      20.70, 22.00, IN(1.0, 1.10, (0.5, 0.45)), 0.2),
    shot("bravo.jpg",          22.00, 23.30, IN(1.0, 1.10, (0.5, 0.4)), 0.2),
    shot("nyira_lava.jpg",     23.30, 24.40, IN(1.02, 1.12), 0.2),
    shot("kivu_goma.jpg",      24.40, 29.05, OUT(1.18, 1.02, (0.5, 0.55)), 0.3, xout=0.5),  # "two million people"
    # ---- 01_gruinard ----
    {"card": True, "src": "src/gru_walsh.jpg", "num": "#10", "name": "GRUINARD ISLAND", "sub": "SCOTLAND",
     "t0": 29.05, "t1": 32.00, "xin": 0.5, "xout": 0.5},
    {"frames": "maps/frames_gruinard", "t0": 32.00, "t1": 35.50, "xin": 0.5, "xout": 0.6},
    shot("gru_walsh.jpg",      35.50, 41.00, IN(1.0, 1.12, (0.45, 0.52), (0.5, 0.5))),   # peaceful patch of green; 1942
    shot("SHEEP",              41.00, 46.00, PAN(0.42, 0.58, 1.12)),                     # brought sheep here, bombs
    shot("anthrax_cdc.png",    46.00, 51.00, IN(1.0, 1.15), crop=[0.2, 0.18, 0.8, 0.78]),# sheep died; test worked
    shot("gru_eilid.jpg",      51.00, 57.60, OUT(1.15, 1.0, (0.4, 0.45))),               # spores soaked into soil
    shot("porton_fence.jpg",   57.60, 65.40, PAN(0.38, 0.6, 1.12)),                      # package left at a military lab
    shot("anthrax_nist.jpg",   65.40, 70.00, IN(1.0, 1.15, (0.5, 0.5))),                 # tests showed anthrax
    shot("gru_1981.jpg",       70.00, 76.20, PAN(0.4, 0.6, 1.12, 0.48)),                 # cleaned: formaldehyde, seawater
    shot("gru_mcbey.jpg",      76.20, 82.80, IN(1.0, 1.10, (0.62, 0.4))),                # declared safe, bought back
    shot("gru_bay_pano.jpg",   82.80, 88.00, PAN(0.35, 0.62, 1.1)),                      # promised to return
    shot("gru_bay_dawes.jpg",  88.00, 92.50, IN(1.0, 1.14, (0.6, 0.38)), xout=0),        # within 150 years. Just in case.
]
overlays = [
    {"type": "brand", "t0": 25.70, "t1": 28.95, "fin": 0.9, "fout": 0.5},
    {"type": "lower", "num": "#10", "text": "GRUINARD ISLAND, SCOTLAND", "t0": 35.60, "t1": 92.50},
]
import sys
sheep = sys.argv[1] if len(sys.argv) > 1 else "sheep_harris.jpg"
for s in shots:
    if s.get("src") == "src/SHEEP": s["src"] = f"src/{sheep}"
print(json.dumps({"duration": 92.5, "audio": "../voice/full.mp3", "shots": shots, "overlays": overlays}, indent=1))
