"""Edit decision list for the full video01 (10:37.6).
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json); sections follow voice/timings.txt.
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 637.6

IN = lambda s0=1.0, s1=1.10, c0=(0.5, 0.5), c1=None: {"s0": s0, "s1": s1, "c0": list(c0), "c1": list(c1 or c0)}
OUT = lambda s0=1.12, s1=1.0, c0=(0.5, 0.5), c1=None: {"s0": s0, "s1": s1, "c0": list(c0), "c1": list(c1 or c0)}
PAN = lambda a, b, s=1.15, y=0.5: {"s0": s, "s1": s, "c0": [a, y], "c1": [b, y]}

def shot(src, t0, t1, move=None, x=0.6, **kw):
    return {"src": f"src/{src}", "t0": t0, "t1": t1, "move": move or IN(), "xin": x, "xout": x, **kw}

def inset(src, t0, t1, **kw):          # small sources: sharp, centred, on a blurred copy of themselves
    return shot(src, t0, t1, None, inset=True, **kw)

shots, overlays = [], []
PLATE = [0.05, 0.05, 0.95, 0.95]   # trims archive numbers on the edges of 1916-1924 autochrome plates

def place(num, name, sub, frames, t_card, t_map, t_lower, t_end, items, lower=None):
    """Card (blurred map background) -> map -> shots; lower third from t_lower to t_end."""
    shots.append({"card": True, "bg_map": f"maps/{frames}", "num": num, "name": name, "sub": sub,
                  "t0": t_card, "t1": t_map, "xin": 0.5, "xout": 0.5})
    shots.append({"frames": f"maps/{frames}", "t0": t_map, "t1": t_lower, "xin": 0.5, "xout": 0.6})
    shots.extend(items)
    overlays.append({"type": "lower", "num": num, "text": lower or f"{name}, {sub}", "t0": t_lower + 0.1, "t1": t_end})

# ---------------- 00_hook ----------------
shots += [
    shot("nyos_usgs.jpg",       0.00,  2.95, IN(1.0, 1.12), 0.3, xin=0),            # a lake that killed 1,746 people
    shot("nyos_1986.jpg",       2.95,  5.80, PAN(0.38, 0.62, 1.18), 0.3),           # in a single night
    shot("centralia_fire.jpg",  5.80, 10.10, IN(1.0, 1.15, (0.4, 0.55), (0.3, 0.6)), 0.3),  # burning underground since 1962
    shot("gru_gerrard.jpg",    10.10, 15.50, IN(1.0, 1.16, (0.32, 0.55)), 0.3),     # an island so deadly
    shot("ijen_fire2.jpg",     15.50, 18.10, IN(1.0, 1.10), 0.3),                   # never heard of most of them
    shot("zone_forest.jpg",    18.10, 19.40, PAN(0.42, 0.55, 1.12), 0.2),           # we count down ten ...
    shot("plymouth_buried.jpg", 19.40, 20.70, IN(1.04, 1.12), 0.2),
    shot("witt_sign.jpg",      20.70, 22.00, IN(1.0, 1.10, (0.5, 0.45)), 0.2),
    shot("bravo.jpg",          22.00, 23.30, IN(1.0, 1.10, (0.5, 0.4)), 0.2),
    shot("nyira_lava.jpg",     23.30, 24.40, IN(1.02, 1.12), 0.2),
    shot("kivu_goma.jpg",      24.40, 29.05, OUT(1.18, 1.02, (0.5, 0.55)), 0.3, xout=0.5),  # two million people
]
overlays.append({"type": "brand", "t0": 25.70, "t1": 28.95, "fin": 0.9, "fout": 0.5})

# ---------------- 01_gruinard ----------------
place("#10", "GRUINARD ISLAND", "SCOTLAND", "frames_gruinard", 29.05, 32.00, 35.50, 92.45, [
    shot("gru_walsh.jpg",      35.50, 41.00, IN(1.0, 1.12, (0.45, 0.52), (0.5, 0.5))),   # peaceful patch of green; 1942
    shot("sheep_harris.jpg",   41.00, 46.00, PAN(0.42, 0.58, 1.12)),                     # brought sheep here
    shot("anthrax_cdc.png",    46.00, 51.00, IN(1.0, 1.15), crop=[0.2, 0.18, 0.8, 0.78]),# sheep died; test worked
    shot("gru_eilid.jpg",      51.00, 57.60, OUT(1.15, 1.0, (0.4, 0.45))),               # spores soaked into the soil
    shot("porton_fence.jpg",   57.60, 65.40, PAN(0.38, 0.6, 1.12)),                      # package outside a military lab
    shot("lab_plate.jpg",      65.40, 70.00, IN(1.0, 1.12)),                             # tests showed it contained anthrax
    shot("gru_1981.jpg",       70.00, 76.20, PAN(0.4, 0.6, 1.12, 0.48)),                 # cleaned: formaldehyde and seawater
    shot("gru_torrmor.jpg",    76.20, 82.80, IN(1.0, 1.12, (0.5, 0.5), (0.48, 0.52))),   # declared safe, bought back
    shot("gru_bay_pano.jpg",   82.80, 88.00, PAN(0.35, 0.62, 1.1)),                      # promised to return
    shot("gru_bay_dawes.jpg",  88.00, 93.25, IN(1.0, 1.14, (0.6, 0.38))),                # within 150 years. Just in case.
], lower="GRUINARD ISLAND, SCOTLAND")

# ---------------- 02_kawah_ijen ----------------
place("#9", "KAWAH IJEN", "INDONESIA", "frames_ijen", 93.25, 96.40, 99.90, 146.60, [
    shot("ijen_fire.jpg",      99.90, 106.50, IN(1.0, 1.15, (0.45, 0.45))),              # glows with electric blue fire
    shot("ijn_crater.jpg",    106.50, 112.40, OUT(1.15, 1.0)),                           # turquoise lake a km wide
    shot("ijn_acidlake.jpg",  112.40, 118.30, PAN(0.4, 0.6, 1.12)),                      # most acidic, pH close to zero
    shot("ijn_minelake.jpg",  118.30, 124.60, IN(1.0, 1.12, (0.5, 0.55))),               # photographer lost a camera
    shot("ijn_mine.jpg",      124.60, 130.40, PAN(0.6, 0.4, 1.12)),                      # miners collect sulfur from pipes
    shot("ijn_miner.jpg",     130.40, 135.60, IN(1.0, 1.10, (0.5, 0.4))),                # wet cloth over their mouths
    shot("ijn_slopes.jpg",    135.60, 140.70, PAN(0.35, 0.6, 1.1)),                      # 1976 eruption
    shot("ijn_tourists.jpg",  140.70, 147.40, IN(1.0, 1.12)),                            # hundreds of tourists hike down
])

# ---------------- 03_zone_rouge ----------------
place("#8", "ZONE ROUGE", "FRANCE", "frames_zone", 147.40, 150.60, 154.10, 202.95, [
    shot("zr_eparges.jpg",    154.10, 160.20, IN(1.0, 1.12), crop=PLATE),                            # old battlefields, could not be saved
    shot("zr_esnes.jpg",      160.20, 166.60, PAN(0.4, 0.6, 1.12), crop=PLATE),                      # became the Zone Rouge
    shot("zr_fleury.jpg",     166.60, 171.60, IN(1.0, 1.10)),                            # most land reclaimed
    shot("zr_panneau.jpg",    171.60, 176.60, IN(1.0, 1.12, (0.5, 0.4))),                # 170 km² still off-limits
    shot("zr_obus.jpg",       176.60, 183.00, PAN(0.38, 0.6, 1.12), crop=PLATE),                     # unexploded shells, poison gas
    shot("zr_vaux.jpg",       183.00, 188.50, OUT(1.14, 1.0), crop=[0.12, 0.05, 0.94, 0.95]),                           # arsenic, 99 % of plants die
    inset("zr_harvest.jpg",   188.50, 193.50),                                           # the iron harvest
    shot("zr_curlu.jpg",      193.50, 198.60, IN(1.0, 1.12), crop=PLATE),                            # tons of shells that never went off
    shot("zone_forest.jpg",   198.60, 203.75, IN(1.0, 1.10, (0.5, 0.55))),               # 300 to 700 years
])

# ---------------- 04_plymouth ----------------
place("#7", "PLYMOUTH", "MONTSERRAT", "frames_plymouth", 203.75, 206.90, 210.40, 255.10, [
    shot("ply_aerial.jpg",    210.40, 215.60, IN(1.0, 1.10)),                            # capital; its volcano Soufrière Hills
    shot("souf_pia.jpg",      215.60, 220.30, IN(1.0, 1.12, (0.6, 0.35))),               # July 1995, it woke up
    shot("ply_flows.jpg",     220.30, 227.40, PAN(0.4, 0.6, 1.12)),                      # pyroclastic flows
    shot("ply_2003a.jpg",     227.40, 234.70, IN(1.0, 1.12)),                            # abandoned, buried under ash
    shot("ply_exclusion.jpg", 234.70, 242.20, PAN(0.6, 0.4, 1.12)),                      # exclusion zone, still active
    shot("plymouth.jpg",      242.20, 249.10, IN(1.0, 1.12, (0.5, 0.6))),                # still the official capital
    shot("ply_damaged.jpg",   249.10, 255.90, OUT(1.14, 1.0)),                           # the only ghost town capital
])

# ---------------- 05_centralia ----------------
place("#6", "CENTRALIA", "PENNSYLVANIA", "frames_centralia", 255.90, 259.00, 262.50, 309.825, [
    shot("centralia_sky.jpg", 262.50, 269.00, PAN(0.4, 0.6, 1.12)),                      # the small town of Centralia
    shot("cen_wafting.jpg",   269.00, 275.70, IN(1.0, 1.12)),                            # fire reached a coal seam
    inset("cen_aster.jpg",    275.70, 282.00),                                           # the fire crept through the mines
    shot("cen_smokehole.jpg", 282.00, 287.60, IN(1.0, 1.10)),                            # sinkholes in people's yards
    inset("cen_oldmap.png",   287.60, 293.20, max_up=1.0),                               # about 1,000 people lived here
    shot("cen_rowhouse.jpg",  293.20, 299.40, PAN(0.4, 0.58, 1.12)),                     # paid them to leave; lost ZIP code
    shot("cen_municipal.jpg", 299.40, 304.00, IN(1.0, 1.10)),                            # only five residents
    shot("centralia_fire.jpg", 304.00, 310.625, IN(1.0, 1.12, (0.45, 0.55))),            # 250 more years
])

# ---------------- 06_wittenoom ----------------
place("#5", "WITTENOOM", "AUSTRALIA", "frames_wittenoom", 310.625, 313.80, 317.30, 365.425, [
    shot("pilbara_iss.jpg",   317.30, 323.20, IN(1.0, 1.12)),                            # Australia's Pilbara region
    shot("wit_mine1966.jpg",  323.20, 329.90, PAN(0.4, 0.6, 1.12)),                      # blue asbestos mine
    shot("wit_croc.jpg",      329.90, 335.20, IN(1.0, 1.15), crop=[0.12, 0.12, 0.88, 0.88]),                            # the fibres stayed
    shot("wit_gorge69.jpg",   335.20, 341.30, PAN(0.6, 0.4, 1.12)),                      # in the gorges
    shot("wit_town.jpg",      341.30, 347.30, IN(1.0, 1.10)),                            # 2,000 died
    shot("wit_cafe.jpg",      347.30, 353.80, OUT(1.12, 1.0)),                           # officially erased the town
    shot("witt_road.jpg",     353.80, 358.40, IN(1.0, 1.12, (0.5, 0.35))),               # removed from maps and road signs
    shot("witt_sign.jpg",     358.40, 366.225, IN(1.0, 1.10, (0.5, 0.45))),              # warning signs, 47,000 hectares
])

# ---------------- 07_bikini (archival blasts and the atoll only) ----------------
place("#4", "BIKINI ATOLL", "MARSHALL ISLANDS", "frames_bikini", 366.225, 369.40, 372.90, 432.275, [
    shot("bik_landsat.png",   372.90, 378.10, IN(1.0, 1.12)),                            # looks like paradise
    shot("bik_site.jpg",      378.10, 385.30, PAN(0.4, 0.6, 1.1)),                       # asked to leave for a while
    shot("bik_able.jpg",      385.30, 391.70, IN(1.0, 1.10)),                            # never truly came home
    shot("bik_baker.jpg",     391.70, 398.00, PAN(0.42, 0.58, 1.1)),                     # 23 nuclear devices
    shot("bravo.jpg",         398.00, 402.60, IN(1.0, 1.10, (0.5, 0.4))),                # Castle Bravo
    inset("bik_space.jpg",    402.60, 408.40, crop=[0.46, 0.32, 0.92, 0.68], max_up=1.5),                            # crater 1.5 km wide
    shot("bik_nara_se.jpg",   408.40, 413.40, PAN(0.6, 0.4, 1.1)),                       # families allowed back (archival chart)
    shot("bik_surge.jpg",     413.40, 419.50, IN(1.0, 1.10)),                            # radioactive caesium
    shot("bik_nara_e.jpg",    419.50, 425.70, IN(1.0, 1.10)),                            # six times the safety limit (archival chart)
    shot("bik_coral.jpg",     425.70, 433.075, PAN(0.4, 0.6, 1.12)),                     # coral and fish are thriving
])

# ---------------- 08_karachay ----------------
place("#3", "LAKE KARACHAY", "RUSSIA", "frames_karachay", 433.075, 436.20, 439.70, 490.275, [
    inset("kar_satmap.jpg",   439.70, 445.80),                                           # next to the Mayak plant
    inset("kar_cetac36.jpg",  445.80, 451.80),                                           # Mayak dumped waste
    shot("kar_sign.jpg",      451.80, 458.40, IN(1.0, 1.12)),                            # 600 roentgens per hour
    shot("kar_steppe.jpg",    458.40, 466.60, PAN(0.38, 0.62, 1.12)),                    # a lethal dose
    inset("kar_cetac25.jpg",  466.60, 473.40),                                           # concrete blocks
    shot("kar_techa10.jpg",   473.40, 480.40, IN(1.0, 1.10)),                            # buried under rock and soil
    inset("kar_trace.png",    480.40, 486.00),                                           # the lake is gone
    shot("kar_techa05.jpg",   486.00, 491.075, OUT(1.12, 1.0)),                          # the waste underneath is not
])

# ---------------- 09_nyos (the lake and terrain only; no victims) ----------------
place("#2", "LAKE NYOS", "CAMEROON", "frames_nyos", 491.075, 494.20, 497.70, 555.325, [
    inset("nyos_usgs.jpg",    497.70, 503.00),                                           # released a huge cloud of CO2
    inset("nyos_pano.jpg",    503.00, 510.20, max_up=1.45),                              # heavier than air
    inset("nyo_landsat.jpg",  510.20, 517.60, max_up=1.6),                               # rolled down the valleys
    inset("nyo_2001.jpg",     517.60, 524.20, max_up=1.7),                               # lost consciousness
    inset("nyos_1986.jpg",    524.20, 530.60),                                           # by morning
    inset("nyo_1992.jpg",     530.60, 536.00, max_up=1.2),                               # village of Nyos: six survived
    inset("nyo_strat.jpg",    536.00, 544.60, max_up=1.0),                               # gas trapped like a soda bottle
    inset("nyo_cnx.jpg",      544.60, 548.60, max_up=1.2),                               # the whole lake turned over
    shot("nyos_vent.jpg",     548.60, 556.125, IN(1.0, 1.10, (0.45, 0.5))),              # pipes let the gas out
])

# ---------------- 10_kivu ----------------
place("#1", "LAKE KIVU", "RWANDA & DR CONGO", "frames_kivu", 556.125, 559.30, 562.80, 618.675, [
    shot("kiv_img.jpg",       562.80, 568.00, IN(1.0, 1.10)),                            # 2,000 times bigger
    shot("kivu_goma.jpg",     568.00, 573.20, PAN(0.4, 0.6, 1.12)),                      # the border of Rwanda and DRC
    shot("kiv_monusco.jpg",   573.20, 578.50, IN(1.0, 1.12)),                            # deep below its surface
    shot("kiv_dawn.jpg",      578.50, 582.70, OUT(1.12, 1.0)),                           # CO2 and methane
    shot("kiv_bukavu.jpg",    582.70, 587.00, PAN(0.6, 0.4, 1.12)),                      # two million people
    shot("kiv_goma_nyira.jpg", 587.00, 591.50, IN(1.0, 1.12, (0.5, 0.4))),               # Nyiragongo erupted in 2021
    shot("nyira_lava.jpg",    591.50, 595.30, IN(1.02, 1.12)),                           # lava pushed underground
    shot("kiv_rubona.jpg",    595.30, 602.40, PAN(0.4, 0.6, 1.1)),                       # power plant pumps methane
    shot("kivu_sunset.jpg",   602.40, 607.40, IN(1.0, 1.12)),                            # a ticking time bomb
    shot("kiv_rdc12.jpg",     607.40, 611.50, PAN(0.6, 0.42, 1.1)),                      # risk not growing
    shot("kiv_image1.jpg",    611.50, 619.475, IN(1.0, 1.12)),                           # one of only three such lakes
])

# ---------------- 11_outro: calm background, end card on the left ----------------
shots.append(shot("kiv_sunset2.jpg", 619.475, DURATION, IN(1.0, 1.08), xout=0))
overlays.append({"type": "endcard", "t0": 620.0, "t1": DURATION, "fin": 1.2, "fout": 0.6})

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
