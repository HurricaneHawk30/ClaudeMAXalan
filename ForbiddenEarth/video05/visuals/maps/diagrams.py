"""Schemes for video05, drawn in code (brand colours, like the maps).
python diagrams.py <out_dir>
  duj_dry.png, duj_flood.png  - Dujiangyan seen from above: the Fish Mouth splits the Min River (section 07)
  qanat_section.png           - qanat cross-section with an Eiffel Tower silhouette of the same height (section 08)
Each gets a .json with "generated": true (not listed in image credits).
"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager, patheffects as pe
from matplotlib.patches import Polygon, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "fonts")
OSW = font_manager.FontProperties(fname=os.path.join(FONTS, "Oswald-Bold.ttf"))
INT = font_manager.FontProperties(fname=os.path.join(FONTS, "Inter-Bold.ttf"))
BG, LAND, LAND2, WATER, WATER_HL, TEXT, DIM, AMBER = ("#070b0f", "#26302a", "#313b33", "#2f6f8f", "#4fa6cf",
                                                     "#f2f2f0", "#9aa6aa", "#e0a84a")
ST = [pe.withStroke(linewidth=6, foreground=BG)]

def fig_ax(xlim, ylim):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.axis("off")
    return fig, ax

def river(ax, xs, ys, w0, w1, col, z=2):
    """Band along the polyline (xs, ys) whose width goes from w0 to w1."""
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    n = len(xs); w = np.linspace(w0, w1, n)
    dx, dy = np.gradient(xs), np.gradient(ys); L = np.hypot(dx, dy) + 1e-9
    nx, ny = -dy / L, dx / L
    left = np.c_[xs + nx * w / 2, ys + ny * w / 2]; right = np.c_[xs - nx * w / 2, ys - ny * w / 2]
    ax.add_patch(Polygon(np.r_[left, right[::-1]], closed=True, color=col, zorder=z, lw=0))

def curve(p0, p1, p2, n=60):
    t = np.linspace(0, 1, n)[:, None]
    p = (1 - t) ** 2 * np.array(p0) + 2 * (1 - t) * t * np.array(p1) + t ** 2 * np.array(p2)
    return p[:, 0], p[:, 1]

def dujiangyan(mode, out):
    inner, outer = (60, 40) if mode == "dry" else (40, 60)
    fig, ax = fig_ax((0, 1920), (0, 1080))
    ax.add_patch(Polygon([[0, 0], [1920, 0], [1920, 1080], [0, 1080]], color=LAND, zorder=0))
    # mountain to the east (Lidui hill) cut by the Bottle-Neck channel
    ax.add_patch(Polygon([[1180, 1080], [1920, 1080], [1920, 300], [1500, 360], [1330, 560], [1240, 820]], color=LAND2, zorder=1))
    W_main = 230
    xs, ys = curve((720, 1080), (760, 900), (820, 760)); river(ax, xs, ys, W_main, W_main, WATER)
    # split at the Fish Mouth (820, 760)
    wi, wo = W_main * inner / 100, W_main * outer / 100
    xi, yi = curve((870, 760), (1180, 620), (1390, 470)); river(ax, xi, yi, wi, wi * 0.9, WATER_HL if mode == "dry" else WATER)
    xo, yo = curve((770, 760), (720, 420), (760, 0)); river(ax, xo, yo, wo, wo * 1.05, WATER_HL if mode == "flood" else WATER)
    # Bottle-Neck through the hill and the canals onto the plain
    xb, yb = curve((1390, 470), (1460, 400), (1560, 330)); river(ax, xb, yb, wi * 0.8, wi * 0.6, WATER_HL if mode == "dry" else WATER)
    for end in [(1900, 120), (1700, 0), (1500, 0)]:
        xc, yc = curve((1560, 330), ((1560 + end[0]) / 2 + 60, (330 + end[1]) / 2 + 40), end)
        river(ax, xc, yc, 26, 18, WATER, 2)
    # the Fish Mouth levee: a fish-head shaped island splitting the flow
    fish = [[820, 790], [868, 740], [900, 640], [930, 520], [960, 430], [900, 470], [850, 560], [800, 680]]
    ax.add_patch(Polygon(fish, closed=True, color="#b8a27a", zorder=4, lw=0))
    ax.text(660, 720, "FISH MOUTH", fontproperties=OSW, fontsize=34, color=AMBER, zorder=6, path_effects=ST, ha="right")
    ax.text(660, 680, "levee splits the river", fontproperties=INT, fontsize=18, color=DIM, zorder=6, path_effects=ST, ha="right")
    ax.text(900, 990, "MIN RIVER", fontproperties=OSW, fontsize=36, color=TEXT, zorder=6, path_effects=ST)
    ax.text(600, 300, "OUTER RIVER", fontproperties=OSW, fontsize=32, color=TEXT, zorder=6, path_effects=ST, ha="right")
    ax.text(600, 262, "flood water away", fontproperties=INT, fontsize=18, color=DIM, zorder=6, path_effects=ST, ha="right")
    ax.text(1250, 700, "INNER CHANNEL", fontproperties=OSW, fontsize=32, color=TEXT, zorder=6, path_effects=ST, rotation=-28)
    ax.text(1600, 420, "BOTTLE-NECK", fontproperties=OSW, fontsize=26, color=TEXT, zorder=6, path_effects=ST)
    ax.text(1600, 388, "cut through the hill", fontproperties=INT, fontsize=16, color=DIM, zorder=6, path_effects=ST)
    ax.text(1690, 150, "FIELDS OF THE\nCHENGDU PLAIN", fontproperties=OSW, fontsize=26, color=TEXT, zorder=6,
            path_effects=ST, ha="center", linespacing=1.1)
    # percentages
    kw = dict(fontproperties=OSW, zorder=7, path_effects=ST)
    ax.text(1120, 520, f"{inner}%", fontsize=64 if mode == "dry" else 46, color=AMBER if mode == "dry" else TEXT, **kw)
    ax.text(820, 440, f"{outer}%", fontsize=64 if mode == "flood" else 46, color=AMBER if mode == "flood" else TEXT, ha="right", **kw)
    # title plate
    ax.text(96, 940, "DRY SEASON" if mode == "dry" else "FLOOD", fontproperties=OSW, fontsize=58, color=AMBER, zorder=7, path_effects=ST)
    ax.text(96, 900, ("most water goes to the fields" if mode == "dry" else "most water is sent away"),
            fontproperties=INT, fontsize=24, color=TEXT, zorder=7, path_effects=ST)
    ax.annotate("", xy=(745, 860), xytext=(722, 1050), zorder=8,
                arrowprops=dict(arrowstyle="-|>", color=TEXT, lw=3, mutation_scale=28))
    fig.savefig(out, dpi=100, facecolor=BG); plt.close(fig)

def qanat(out):
    # x: km-ish horizontal (not to scale), y: metres (to scale vertically)
    fig, ax = fig_ax((0, 1920), (-430, 600))
    surf_x = np.array([0, 520, 900, 1250, 1500, 1920]); surf_y = np.array([0, 0, 25, 70, 120, 190])
    sx = np.linspace(0, 1920, 400); sy = np.interp(sx, surf_x, surf_y)
    ax.add_patch(Polygon(np.r_[np.c_[sx, sy], [[1920, -430], [0, -430]]], color=LAND, zorder=1))
        # aquifer under the hill
    ax.add_patch(Polygon([[1150, -100], [1920, -130], [1920, -260], [1150, -200]], color=WATER, alpha=0.75, zorder=2))
    ax.text(1880, -300, "WATER-BEARING LAYER", fontproperties=OSW, fontsize=24, color=TEXT, ha="right", zorder=6, path_effects=ST)
    # tunnel from the mother well down in the aquifer, gently up to the fields at the surface
    mw_x = 1660; mw_top = float(np.interp(mw_x, sx, sy)); mw_bot = mw_top - 300
    tx = np.array([400, mw_x]); ty = np.array([0, mw_bot])
    ax.plot(tx, ty, color=WATER_HL, lw=7, zorder=4, solid_capstyle="round")
    # vertical shafts
    for x in np.linspace(560, mw_x - 120, 9):
        top = float(np.interp(x, sx, sy)); bot = float(np.interp(x, tx, ty))
        ax.plot([x, x], [bot, top], color=DIM, lw=3, zorder=3)
        ax.add_patch(Polygon([[x - 16, top], [x + 16, top], [x + 9, top + 9], [x - 9, top + 9]], color="#5b5a4e", zorder=3))
    ax.plot([mw_x, mw_x], [mw_bot, mw_top], color=AMBER, lw=7, zorder=5)
    ax.text(mw_x - 24, mw_bot + 40, "MOTHER WELL\n≈300 m deep", fontproperties=OSW, fontsize=28, color=AMBER, ha="right",
            zorder=6, path_effects=ST, linespacing=1.05)
    # Eiffel Tower silhouette (330 m incl. antennas, 300 m original) on the hill top, same vertical scale
    ex, eb = 1820, float(np.interp(1820, sx, sy)); h = 300
    tw = [[ex - 55, eb], [ex - 34, eb + 0.18 * h], [ex - 22, eb + 0.42 * h], [ex - 8, eb + 0.85 * h], [ex - 2, eb + h],
          [ex + 2, eb + h], [ex + 8, eb + 0.85 * h], [ex + 22, eb + 0.42 * h], [ex + 34, eb + 0.18 * h], [ex + 55, eb],
          [ex + 28, eb], [ex, eb + 0.12 * h], [ex - 28, eb]]
    ax.add_patch(Polygon(tw, closed=True, color="#8d9ba0", zorder=5))
    for f in (0.18, 0.42):
        ax.plot([ex - 34 + (f - 0.18) * 50, ex + 34 - (f - 0.18) * 50], [eb + f * h] * 2, color=BG, lw=2, zorder=6)
    ax.annotate("", xy=(ex + 80, eb + h), xytext=(ex + 80, eb), zorder=6,
                arrowprops=dict(arrowstyle="<->", color=DIM, lw=2))
    ax.annotate("", xy=(mw_x + 40, mw_top), xytext=(mw_x + 40, mw_bot), zorder=6,
                arrowprops=dict(arrowstyle="<->", color=AMBER, lw=2))
    ax.text(ex, eb + h + 14, "EIFFEL TOWER", fontproperties=OSW, fontsize=22, color=TEXT, ha="center", zorder=6, path_effects=ST)
    # fields and outlet
    for x in range(40, 420, 46):
        ax.add_patch(Polygon([[x, 0], [x + 38, 0], [x + 38, 10], [x, 10]], color="#4f7a3a", zorder=4))
    ax.text(210, 40, "FIELDS OF GONABAD", fontproperties=OSW, fontsize=28, color=TEXT, ha="center", zorder=6, path_effects=ST)
    ax.text(400, -40, "water flows out", fontproperties=INT, fontsize=18, color=DIM, ha="center", zorder=6, path_effects=ST)
    ax.text(1000, -190, "TUNNEL  ≈33 km, gentle slope, no pumps", fontproperties=OSW, fontsize=26, color=WATER_HL,
            rotation=np.degrees(np.arctan2(ty[1] - ty[0], (tx[1] - tx[0]) * 0.735)) * 0.9, ha="center", zorder=6, path_effects=ST)
    ax.text(870, 250, "427 SHAFTS: air, earth out, access for repairs", fontproperties=INT, fontsize=20, color=DIM,
            ha="center", zorder=6, path_effects=ST)
    ax.text(70, 520, "A QANAT IN CROSS-SECTION", fontproperties=OSW, fontsize=44, color=AMBER, zorder=7, path_effects=ST)
    ax.text(70, 480, "length not to scale", fontproperties=INT, fontsize=18, color=DIM, zorder=7, path_effects=ST)
    fig.savefig(out, dpi=100, facecolor=BG); plt.close(fig)

def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    jobs = [("duj_dry", lambda p: dujiangyan("dry", p)), ("duj_flood", lambda p: dujiangyan("flood", p)), ("qanat_section", qanat)]
    for key, fn in jobs:
        p = os.path.join(out, key + ".png"); fn(p)
        json.dump({"key": key, "source": "Forbidden Earth", "title": f"Scheme ({key})", "author": "Forbidden Earth (generated with code)",
                   "license": "CC0", "license_url": "", "url": "", "license_ok": True, "generated": True},
                  open(os.path.join(out, key + ".json"), "w"), indent=1)
        print("OK", p)

if __name__ == "__main__":
    main()
