"""Campi Flegrei caldera sketch for video15 (own drawing, CC0): coastline from Natural Earth 10m, circle ~15 km wide."""
import json, os, math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager, patheffects as pe
from matplotlib.patches import Polygon, Ellipse
H = os.path.dirname(os.path.abspath(__file__)); F = os.path.join(H, "..", "fonts")
osw = font_manager.FontProperties(fname=os.path.join(F, "Oswald-Bold.ttf")); inter = font_manager.FontProperties(fname=os.path.join(F, "Inter-Bold.ttf"))
OCEAN, LAND, SEA, ACC = "#070b0f", "#56676c", "#132632", "#e0a84a"
ST = [pe.withStroke(linewidth=4, foreground="#0b1014")]
lon0, lat0 = 14.14, 40.83; k = math.cos(math.radians(lat0))
x0, x1 = 13.88, 14.42; yh = (x1 - x0) * k * 1080 / 1920 / 2
fig = plt.figure(figsize=(19.2, 10.8), dpi=100); ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(SEA)
ax.set_xlim(x0, x1); ax.set_ylim(lat0 - yh, lat0 + yh); ax.set_aspect(1 / k); ax.axis("off")
g = json.load(open(os.path.join(H, "..", "maps", "ne_10m_admin_0_countries.geojson")))
for f in g["features"]:
    if f["properties"].get("ADMIN") != "Italy": continue
    geo = f["geometry"]; polys = geo["coordinates"] if geo["type"] == "MultiPolygon" else [geo["coordinates"]]
    for p in polys:
        ax.add_patch(Polygon(p[0], closed=True, fc=LAND, ec="#93a3a7", lw=1.5))
r = 7.5 / 111.0
ax.add_patch(Ellipse((lon0, lat0), 2 * r / k, 2 * r, fc=ACC, alpha=0.18, ec=ACC, lw=4, ls=(0, (6, 4))))
pts = [(14.121, 40.823, "POZZUOLI", 0.004, -0.012), (14.087, 40.836, "MONTE NUOVO", -0.06, 0.008),
       (14.139, 40.827, "SOLFATARA", 0.006, 0.006), (14.25, 40.852, "NAPLES", 0.006, 0.006)]
for x, y, t, dx, dy in pts:
    ax.plot(x, y, "o", ms=12, color="white", mec=OCEAN, mew=2)
    ax.text(x + dx, y + dy, t, fontproperties=osw, fontsize=30, color="white", path_effects=ST)
ax.text(lon0 - 0.03, lat0 + r + 0.006, "CALDERA ~15 KM WIDE", fontproperties=osw, fontsize=40, color=ACC, path_effects=ST)
ax.text(14.165, 40.775, "GULF OF POZZUOLI", fontproperties=inter, fontsize=22, color="#9fb1b6", path_effects=ST)
out = os.path.join(H, "..", "src", "campi_flegrei", "cam_dia.jpg")
fig.savefig(out, dpi=100, facecolor=SEA); print(out)
json.dump({"key": "cam_dia", "source": "Forbidden Earth", "title": "Campi Flegrei caldera (diagram)", "author": "Forbidden Earth",
           "credit": "Coastline: Natural Earth (public domain)", "license": "CC0", "license_url": "", "url": "",
           "description": "Diagram drawn for the video: the Campi Flegrei caldera, about 15 km wide, with Pozzuoli, Monte Nuovo, Solfatara and Naples.",
           "restrictions": "", "size": "1920x1080", "license_ok": True}, open(out[:-4] + ".json", "w"), indent=1)
