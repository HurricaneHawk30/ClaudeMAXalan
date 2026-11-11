"""Depth comparison diagrams for video04 (sections 08_kola and 09_challenger_deep).
python depth_diagram.py <out_dir>   -> depth_kola.png, depth_challenger.png (+ .json, generated: true)
Everest 8,849 m (drawn hanging below sea level for comparison), Challenger Deep ~10,935 m, Kola Superdeep Borehole 12,262 m.
"""
import json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager, patheffects as pe
from matplotlib.patches import Polygon, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "fonts")
OSW = font_manager.FontProperties(fname=os.path.join(FONTS, "Oswald-Bold.ttf"))
INT = font_manager.FontProperties(fname=os.path.join(FONTS, "Inter-Bold.ttf"))
BG, SEA, DEEP, GROUND, LINE, TEXT, DIM, AMBER = "#070b0f", "#132632", "#0b1820", "#3b3127", "#93a3a7", "#f2f2f0", "#8d9ba0", "#e0a84a"
ITEMS = [("everest", "MOUNT EVEREST", "8,849 m", 8849), ("challenger", "CHALLENGER DEEP", "≈10,935 m", 10935),
         ("kola", "KOLA SUPERDEEP BOREHOLE", "12,262 m", 12262)]

def draw(highlight, out):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1920); ax.set_ylim(-14200, 2200); ax.axis("off")
    ax.add_patch(Rectangle((0, -14200), 1920, 14200, color=DEEP, zorder=0))
    ax.add_patch(Rectangle((0, -11500), 1920, 11500, color=SEA, zorder=0.5))
    ax.plot([0, 1920], [0, 0], color=LINE, lw=2, zorder=3)
    ax.text(60, 300, "SEA LEVEL", fontproperties=INT, fontsize=20, color=DIM, zorder=4)
    for d in range(2000, 14001, 2000):
        ax.plot([0, 1920], [-d, -d], color=LINE, lw=0.6, alpha=0.18, zorder=1)
        ax.text(60, -d + 120, f"{d:,} m", fontproperties=INT, fontsize=16, color=DIM, alpha=0.8, zorder=4)
    xs = {"everest": 470, "challenger": 1000, "kola": 1540}
    for key, name, val, depth in ITEMS:
        x = xs[key]; hl = key == highlight
        col = AMBER if hl else "#56676c"; alpha = 1.0 if hl else 0.85
        if key == "everest":       # mountain turned upside down, as if dropped into the trench
            ax.add_patch(Polygon([[x - 190, 0], [x + 190, 0], [x, -depth]], closed=True, color=col, alpha=alpha, zorder=2))
        elif key == "challenger":  # trench profile
            ax.add_patch(Polygon([[x - 210, 0], [x + 210, 0], [x + 60, -depth], [x - 60, -depth]], closed=True,
                                 color=col, alpha=alpha, zorder=2))
        else:                      # a narrow borehole through rock
            ax.add_patch(Rectangle((x - 200, -depth - 600), 400, depth + 600, color=GROUND, zorder=1.5))
            ax.add_patch(Rectangle((x - 14, -depth), 28, depth, color=col, alpha=alpha, zorder=2))
        ax.plot([x - 230, x + 230], [-depth, -depth], color=col, lw=3 if hl else 1.5, zorder=3)
        st = [pe.withStroke(linewidth=6, foreground=BG)]
        ax.text(x, -depth - 380, val, fontproperties=OSW, fontsize=40 if hl else 30, color=TEXT if hl else DIM,
                ha="center", va="top", zorder=5, path_effects=st)
        ax.text(x, 1250, name, fontproperties=OSW if hl else INT, fontsize=30 if hl else 20, color=AMBER if hl else DIM,
                ha="center", va="center", zorder=5, path_effects=st)
    fig.savefig(out, dpi=100, facecolor=BG); plt.close(fig)

def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    for key in ("kola", "challenger"):
        p = os.path.join(out, f"depth_{key}.png"); draw(key, p)
        json.dump({"key": f"depth_{key}", "source": "Forbidden Earth", "title": f"Depth diagram ({key})",
                   "author": "Forbidden Earth (generated with code)", "license": "CC0", "license_url": "",
                   "url": "", "license_ok": True, "generated": True},
                  open(os.path.join(out, f"depth_{key}.json"), "w"), indent=1)
        print("OK", p)

if __name__ == "__main__":
    main()
