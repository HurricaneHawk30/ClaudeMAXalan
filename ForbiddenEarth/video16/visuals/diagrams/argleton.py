"""Argleton sketch for video16 (own drawing, CC0): Natural Earth 10m coastline, a pin between Aughton and Ormskirk.
Town positions are approximate; the road is schematic."""
import json, os, math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager, patheffects as pe
from matplotlib.patches import Polygon, Ellipse
H = os.path.dirname(os.path.abspath(__file__)); F = os.path.join(H, "..", "fonts")
osw = font_manager.FontProperties(fname=os.path.join(F, "Oswald-Bold.ttf")); inter = font_manager.FontProperties(fname=os.path.join(F, "Inter-Bold.ttf"))
LAND, SEA, ACC = "#3f5a3c", "#132632", "#e0a84a"
ST = [pe.withStroke(linewidth=5, foreground="#0b1014")]
lon0, lat0 = -2.900, 53.5525; k = math.cos(math.radians(lat0))
x0, x1 = lon0 - 0.07, lon0 + 0.07; yh = (x1 - x0) * k * 1080 / 1920 / 2
fig = plt.figure(figsize=(19.2, 10.8), dpi=100); ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(SEA)
ax.set_xlim(x0, x1); ax.set_ylim(lat0 - yh, lat0 + yh); ax.set_aspect(1 / k); ax.axis("off")
g = json.load(open(os.path.join(H, "..", "maps", "ne_10m_admin_0_countries.geojson")))
for f in g["features"]:
    if f["properties"].get("ADMIN") != "United Kingdom": continue
    geo = f["geometry"]; polys = geo["coordinates"] if geo["type"] == "MultiPolygon" else [geo["coordinates"]]
    for p in polys:
        ax.add_patch(Polygon(p[0], closed=True, fc=LAND, ec="#93a3a7", lw=1.5))
# faint field grid
for i in range(-12, 13):
    ax.plot([lon0 + i * 0.008, lon0 + i * 0.008], [lat0 - yh, lat0 + yh], color="#ffffff", alpha=0.05, lw=1)
    ax.plot([x0, x1], [lat0 + i * 0.005, lat0 + i * 0.005], color="#ffffff", alpha=0.05, lw=1)
aug, orm = (-2.917, 53.541), (-2.884, 53.568)
road = [(-2.97, 53.497), aug, (-2.900, 53.555), orm, (-2.86, 53.60)]   # schematic main road
ax.plot([p[0] for p in road], [p[1] for p in road], color="#d9d2c0", lw=7, solid_capstyle="round", alpha=0.85, zorder=2)
for (x, y), t, dx in [(aug, "AUGHTON", -0.021), (orm, "ORMSKIRK", 0.003)]:
    ax.plot(x, y, "o", ms=16, color="white", mec="#0b1014", mew=2, zorder=4)
    ax.text(x + dx, y - 0.0012, t, fontproperties=osw, fontsize=36, color="white", path_effects=ST, zorder=5)
# the town that wasn't there: pin + dashed outline
px, py = -2.906, 53.553
ax.add_patch(Ellipse((px, py), 0.006 / k, 0.006, fc=ACC, alpha=0.15, ec=ACC, lw=3, ls=(0, (5, 4)), zorder=3))
ax.plot([px, px], [py, py + 0.0045], color=ACC, lw=5, zorder=6)
ax.plot(px, py + 0.005, "o", ms=34, color=ACC, mec="#0b1014", mew=3, zorder=7)
ax.plot(px, py + 0.005, "o", ms=11, color="#0b1014", zorder=8)
ax.text(px - 0.005, py + 0.005, "ARGLETON", fontproperties=osw, fontsize=60, color=ACC, va="center", ha="right", path_effects=ST, zorder=8)
ax.text(px - 0.005, py + 0.0005, "ON THE MAP: A TOWN", fontproperties=inter, fontsize=22, color="white", va="center", ha="right", path_effects=ST, zorder=8)
ax.text(px - 0.005, py - 0.0018, "ON THE GROUND: AN EMPTY FIELD", fontproperties=inter, fontsize=22, color="white", va="center", ha="right", path_effects=ST, zorder=8)
ax.text(x0 + 0.004, lat0 + yh - 0.003, "WEST LANCASHIRE, ENGLAND  (SKETCH, NOT TO SCALE)", fontproperties=inter, fontsize=20,
        color="#9fb1b6", va="top", path_effects=ST)
out = os.path.join(H, "..", "src", "argleton", "arg_dia.jpg")
fig.savefig(out, dpi=100, facecolor=SEA); print(out)
json.dump({"key": "arg_dia", "source": "Forbidden Earth", "title": "Argleton (diagram)", "author": "Forbidden Earth",
           "credit": "Coastline: Natural Earth (public domain)", "license": "CC0", "license_url": "", "url": "",
           "description": "Sketch drawn for the video: where the phantom town of Argleton appeared, between Aughton and Ormskirk.",
           "restrictions": "", "size": "1920x1080", "license_ok": True}, open(out[:-4] + ".json", "w"), indent=1)
