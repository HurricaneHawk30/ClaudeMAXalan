"""Globe -> country -> point map animation from Natural Earth data (public domain).

python globe_zoom.py --lon -5.4743 --lat 57.8943 --country "United Kingdom" \
    --label "GRUINARD ISLAND" --sub "SCOTLAND" --out frames_gruinard [--secs 3.5]
Writes PNG frames 1920x1080 @30fps.
"""
import argparse, json, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager, patheffects as pe
STROKE = [pe.withStroke(linewidth=6, foreground='#070b0f')]
import cartopy.crs as ccrs
from shapely.geometry import shape, box

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "fonts")
R = 6371000.0
W, H, DPI = 1920, 1080, 100
OCEAN, LAND, BORDER, HIL, ACCENT = "#070b0f", "#20272a", "#3a4448", "#47301f", "#e0a84a"

def load(path, keep=None, clip=None):
    feats = json.load(open(path))["features"]
    out = []
    for f in feats:
        name = f["properties"].get("ADMIN")
        if keep and name not in keep: continue
        g = shape(f["geometry"])
        if clip is not None:
            if not g.intersects(clip): continue
            g = g.intersection(clip)
        out.append((name, g))
    return out

def smooth(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--lon", type=float, required=True); a.add_argument("--lat", type=float, required=True)
    a.add_argument("--country", required=True); a.add_argument("--label", required=True)
    a.add_argument("--sub", default=""); a.add_argument("--out", required=True)
    a.add_argument("--secs", type=float, default=3.5); a.add_argument("--end_km", type=float, default=120)
    a.add_argument("--start_lon", type=float, default=None)
    o = a.parse_args()
    os.makedirs(o.out, exist_ok=True)
    oswald = font_manager.FontProperties(fname=os.path.join(FONTS, "Oswald-Bold.ttf"))
    inter = font_manager.FontProperties(fname=os.path.join(FONTS, "Inter-Bold.ttf"))
    coarse = load(os.path.join(HERE, "ne_50m_admin_0_countries.geojson"))
    region = box(o.lon - 25, o.lat - 15, o.lon + 25, o.lat + 15)
    fine = load(os.path.join(HERE, "ne_10m_admin_0_countries.geojson"), clip=region)
    pc = ccrs.PlateCarree()
    outside = [(nm, g.difference(region)) for nm, g in coarse]
    outside = [(nm, g) for nm, g in outside if not g.is_empty]
    n = int(round(o.secs * 30))
    start_lon = o.start_lon if o.start_lon is not None else o.lon - 70
    # half-height of view in metres: full globe -> country -> point (log interpolation)
    keys = [(0.0, 1.18 * R), (0.35, 1.05 * R), (0.70, 900e3), (1.0, o.end_km * 1e3)]
    def half_h(t):
        for (t0, h0), (t1, h1) in zip(keys, keys[1:]):
            if t <= t1:
                s = smooth((t - t0) / (t1 - t0))
                return math.exp(math.log(h0) + (math.log(h1) - math.log(h0)) * s)
        return keys[-1][1]
    for i in range(n):
        t = i / (n - 1)
        rot = smooth(t / 0.6)
        clon = start_lon + (o.lon - start_lon) * rot
        clat = 15 + (o.lat - 15) * rot
        hh = half_h(t)
        proj = ccrs.Orthographic(central_longitude=clon, central_latitude=clat)
        fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor=OCEAN)
        ax = fig.add_axes([0, 0, 1, 1], projection=proj)
        ax.set_facecolor(OCEAN)
        ax.spines["geo"].set_visible(False)
        hw = hh * W / H
        ax.set_xlim(-hw, hw); ax.set_ylim(-hh, hh)
        if hh > 0.5 * R:  # globe disc + atmosphere glow
            for k, al in [(1.06, .05), (1.035, .08), (1.015, .12)]:
                ax.add_patch(plt.Circle((0, 0), R * k, transform=proj, color="#3b5566", alpha=al, zorder=0))
            ax.add_patch(plt.Circle((0, 0), R, transform=proj, color="#0d151b", zorder=0.5))
        ax.gridlines(color="#18232b", linewidth=0.6, alpha=0.8 if hh > 2e6 else 0.3)
        geoms = coarse if hh > 2.5e6 else outside + fine
        hl_alpha = smooth((0.75 - (hh / R)) / 0.5) if hh < R else 0.0
        for name, g in geoms:
            is_hl = name == o.country
            col = HIL if is_hl and hl_alpha > 0 else LAND
            ax.add_geometries([g], pc, facecolor=col, edgecolor=BORDER, linewidth=0.5, zorder=1)
            if is_hl and hl_alpha > 0:
                ax.add_geometries([g], pc, facecolor="none", edgecolor=ACCENT, linewidth=1.4,
                                  alpha=hl_alpha, zorder=2)
        # country label while at country scale
        cl = smooth((t - 0.55) / 0.12) * (1 - smooth((t - 0.86) / 0.08))
        if cl > 0.01:
            ax.text(0.5, 0.86, o.country.upper(), transform=ax.transAxes, ha="center",
                    fontproperties=inter, fontsize=26, color="#cfd6d8", alpha=cl, path_effects=STROKE)
        # point marker + label in final phase
        pl = smooth((t - 0.72) / 0.12)
        if pl > 0.01:
            pulse = (t * o.secs * 1.6) % 1.0
            ax.plot(o.lon, o.lat, "o", transform=pc, ms=14, color=ACCENT, alpha=pl, zorder=5)
            ax.plot(o.lon, o.lat, "o", transform=pc, ms=14 + 46 * pulse, mfc="none", mec=ACCENT,
                    mew=2, alpha=pl * (1 - pulse), zorder=5)
            x, y = proj.transform_point(o.lon, o.lat, pc)
            ax.text(x + hw * 0.06, y + hh * 0.03, o.label, fontproperties=oswald, fontsize=46,
                    color="white", alpha=pl, va="bottom", zorder=6, path_effects=STROKE)
            if o.sub:
                ax.text(x + hw * 0.06, y - hh * 0.01, o.sub, fontproperties=inter, fontsize=22,
                        color=ACCENT, alpha=pl, va="top", zorder=6, path_effects=STROKE)
        fig.savefig(os.path.join(o.out, f"{i:04d}.png"), dpi=DPI, facecolor=OCEAN)
        plt.close(fig)
    print("frames:", n)

if __name__ == "__main__":
    main()
