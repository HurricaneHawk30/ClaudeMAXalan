"""Edit decision list for video02 "10 Lost Cities That Were Found Again (And One That Never Was)" (12:58.2).
Shot times follow the word timestamps of voice/full.mp3 (work/words_full.json, work/sentences.txt);
sections follow voice/timings.txt.
python edl_build.py > edl.json      (fails if a still repeats within MIN_GAP seconds or a file is missing)
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_GAP = 120.0
DURATION = 778.225

IN = lambda s0=1.0, s1=1.10, c0=(0.5, 0.5), c1=None: {"s0": s0, "s1": s1, "c0": list(c0), "c1": list(c1 or c0)}
OUT = lambda s0=1.12, s1=1.0, c0=(0.5, 0.5), c1=None: {"s0": s0, "s1": s1, "c0": list(c0), "c1": list(c1 or c0)}
PAN = lambda a, b, s=1.15, y=0.5: {"s0": s, "s1": s, "c0": [a, y], "c1": [b, y]}
TILT = lambda a, b, s=1.15, x=0.5: {"s0": s, "s1": s, "c0": [x, a], "c1": [x, b]}

def shot(src, t0, t1, move=None, x=0.6, **kw):
    return {"src": f"src/{src}", "t0": t0, "t1": t1, "move": move or IN(), "xin": x, "xout": x, **kw}

def inset(src, t0, t1, **kw):          # small or very wide/tall sources: sharp, centred, on a blurred copy
    return shot(src, t0, t1, None, inset=True, **kw)

shots, overlays = [], []

def place(num, name, sub, frames, t_card, t_map, t_lower, t_end, items, lower=None, lower_num=None):
    shots.append({"card": True, "bg_map": f"maps/{frames}", "num": num, "name": name, "sub": sub,
                  "t0": t_card, "t1": t_map, "xin": 0.5, "xout": 0.5})
    shots.append({"frames": f"maps/{frames}", "t0": t_map, "t1": t_lower, "xin": 0.5, "xout": 0.6})
    shots.extend(items)
    overlays.append({"type": "lower", "num": num if lower_num is None else lower_num,
                     "text": lower or f"{name}, {sub}", "t0": t_lower + 0.1, "t1": t_end})

# ---------------- 00_hook (0:00-0:25.2) ----------------
shots += [
    shot("hk_pomp.jpg",        0.00,  2.70, IN(1.0, 1.12), 0.3, xin=0),            # these cities were gone
    shot("hk_calbio.jpg",      2.70,  4.40, PAN(0.4, 0.55, 1.12), 0.25),           # buried under ash, swallowed by jungle
    shot("hk_dunes.jpg",       4.40,  6.90, IN(1.0, 1.10), 0.25),                  # hidden beneath the sand
    shot("hk_troywalls.jpg",   6.90,  9.20, PAN(0.42, 0.58, 1.12), 0.25),          # written off as legends
    shot("hk_storm.jpg",       9.20, 11.90, IN(1.0, 1.12), 0.25),                  # a storm
    shot("hk_cliff2026.jpg",  11.90, 14.90, PAN(0.4, 0.6, 1.12), 0.25),            # stray cattle
    shot("hk_derin.jpg",      14.90, 18.10, IN(1.0, 1.12), 0.25),                  # a wall in his own house
    shot("hk_machu.jpg",      18.10, 21.20, OUT(1.15, 1.02), 0.25),                # ten lost cities found again
    shot("kircher.jpg",       21.20, 25.975, IN(1.0, 1.10), 0.3, xout=0.5),        # the one nobody has ever found
]
overlays.append({"type": "brand", "t0": 22.60, "t1": 25.90, "fin": 0.9, "fout": 0.5})

# ---------------- 01_skara_brae ----------------
place("#10", "SKARA BRAE", "SCOTLAND", "frames_skara", 25.975, 29.00, 32.50, 84.85, [
    shot("skb_waves.jpg",      32.50, 38.50, PAN(0.4, 0.6, 1.12)),                 # a violent storm battered Orkney
    shot("skb_beach.jpg",      38.50, 43.00, IN(1.0, 1.10)),                       # stripped the sand from a dune
    shot("skb_houses.jpg",     43.00, 50.30, IN(1.0, 1.12, (0.5, 0.55))),          # stone walls, whole houses
    inset("skb_plan.jpg",      50.30, 56.50, max_up=1.0),                          # nearly 5,000 years old
    shot("skb_geo.jpg",        56.50, 62.70, PAN(0.4, 0.6, 1.1)),                  # furniture still there
    inset("skb_sections.jpg",  62.70, 70.20, max_up=1.0),                          # beds, hearth, watertight boxes
    shot("skb_bay3.jpg",       70.20, 77.20, PAN(0.38, 0.6, 1.12)),                # abandoned around 2,500 BC
    shot("skb_bay.jpg",        77.20, 85.65, OUT(1.14, 1.0)),                      # the storm brought it back
])

# ---------------- 02_cliff_palace ----------------
place("#9", "CLIFF PALACE", "COLORADO, USA", "frames_cliff", 85.65, 88.80, 92.30, 146.175, [
    shot("clp_canyon06.jpg",   92.30,  97.40, IN(1.0, 1.10)),                      # two cowboys, December 1888
    shot("clp_canyonpano.jpg", 97.40, 102.50, PAN(0.4, 0.6, 1.12)),                # riding across Mesa Verde
    shot("clp_overlook.jpg",  102.50, 107.00, IN(1.0, 1.12)),                      # from the rim of a canyon
    shot("clp_main.jpg",      107.00, 111.20, IN(1.0, 1.10)),                      # a town under the overhang
    shot("clp_right.jpg",     111.20, 115.60, PAN(0.42, 0.58, 1.1)),               # towers, walls and windows
    shot("clp_1891.jpg",      115.60, 121.60, IN(1.0, 1.10)),                      # they had found Cliff Palace
    shot("clp_2006.jpg",      121.60, 128.60, PAN(0.6, 0.4, 1.12)),                # alcove; 150 rooms, 23 kivas
    shot("clp_kiva.jpg",      128.60, 133.90, IN(1.0, 1.12)),                      # round sunken rooms
    shot("clp_tower.jpg",     133.90, 139.00, OUT(1.12, 1.0)),                     # builders moved away by 1300
    shot("clp_lage.jpg",      139.00, 146.975, IN(1.0, 1.10)),                     # empty for nearly 600 years
])

# ---------------- 03_derinkuyu ----------------
place("#8", "DERINKUYU", "TURKEY", "frames_derinkuyu", 146.975, 150.10, 153.60, 206.325, [
    shot("der_tr.jpg",        153.60, 159.00, IN(1.0, 1.10)),                      # renovating his house
    shot("der_chamber.jpg",   159.00, 165.60, IN(1.0, 1.12)),                      # a room behind the wall
    shot("der_9781.jpg",      165.60, 172.90, PAN(0.4, 0.6, 1.12)),                # carved into volcanic rock
    shot("der_stairs.jpg",    172.90, 178.60, TILT(0.4, 0.6, 1.1)),                # 85 metres, 18 levels
    shot("der_9807.jpg",      178.60, 184.00, IN(1.0, 1.10)),                      # shelter 20,000 people
    shot("hk_derin.jpg",      184.00, 190.00, PAN(0.6, 0.4, 1.12)),                # connected by tunnels (hook use 2:46 ago)
    shot("der_vent.jpg",      190.00, 194.30, IN(1.0, 1.12)),                      # 50 air shafts
    shot("der_door.jpg",      194.30, 200.50, IN(1.0, 1.10, (0.5, 0.45))),         # rolling stone doors
    shot("der_pano.jpg",      200.50, 207.125, OUT(1.12, 1.0)),                    # 8th century BC to 19th century
])

# ---------------- 04_mohenjo_daro ----------------
place("#7", "MOHENJO-DARO", "PAKISTAN", "frames_mohenjo", 207.125, 210.30, 213.80, 273.25, [
    inset("moh_harappa.jpg",  213.80, 219.60),                                     # railway Lahore - Multan
    shot("moh_platform.jpg",  219.60, 226.10, PAN(0.4, 0.6, 1.12)),                # mound full of baked bricks
    shot("moh_brick.jpg",     226.10, 231.00, IN(1.0, 1.12)),                      # laid under 100 miles of railway
    inset("moh_unicorn.jpg",  231.00, 236.90, max_up=1.2),                         # a city 4,000 years old
    shot("moh_stupa.jpg",     236.90, 244.00, IN(1.0, 1.10)),                      # Banerji at a Buddhist stupa
    shot("moh_stupamound.jpg", 244.00, 249.30, PAN(0.4, 0.6, 1.1)),                # beneath it, something older
    shot("moh_ruins.jpg",     249.30, 255.00, IN(1.0, 1.12)),                      # the site was Mohenjo-daro
    shot("moh_stupapano.jpg", 255.00, 260.50, PAN(0.3, 0.7, 1.0)),                 # a lost civilization
    shot("moh_2010.jpg",      260.50, 265.60, IN(1.0, 1.10)),                      # streets in a grid
    shot("moh_bath.jpg",      265.60, 274.05, OUT(1.14, 1.0)),                     # drains; the Mound of the Dead
])

# ---------------- 05_petra ----------------
place("#6", "PETRA", "JORDAN", "frames_petra", 274.05, 277.20, 280.70, 332.125, [
    shot("pet_roberts_east.jpg", 280.70, 285.40, IN(1.0, 1.10)),                   # Burckhardt, 1812
    shot("pet_wellcome.jpg",  285.40, 289.40, PAN(0.42, 0.58, 1.1)),               # dressed as a local
    shot("pet_nearsiq.jpg",   289.40, 296.00, IN(1.0, 1.12)),                      # a ruined city in the mountains
    shot("pet_aaron.jpg",     296.00, 303.60, IN(1.0, 1.12, (0.5, 0.4))),          # the tomb of the prophet Aaron
    shot("pet_siq.jpg",       303.60, 309.00, PAN(0.6, 0.4, 1.12)),                # through a narrow canyon
    shot("pet_khazneh.jpg",   309.00, 314.30, IN(1.0, 1.12)),                      # temples and tombs in rose rock
    shot("pet_royal.jpg",     314.30, 319.00, PAN(0.4, 0.6, 1.1)),                 # didn't dare take notes
    shot("pet_deir.jpg",      319.00, 324.50, IN(1.0, 1.10)),                      # a magician hunting for treasure
    shot("pet_bw.jpg",        324.50, 329.00, PAN(0.35, 0.65, 1.05)),              # left after sunset
    shot("pet_roberts_lower.jpg", 329.00, 332.925, OUT(1.12, 1.0)),                # back on the map
])

# ---------------- 06_pompeii ----------------
place("#5", "POMPEII", "ITALY", "frames_pompeii", 332.925, 336.10, 339.60, 397.875, [
    shot("pom_vesmar.jpg",    339.60, 344.60, IN(1.0, 1.10)),                      # Vesuvius erupted in 79
    shot("pom_duncanson.jpg", 344.60, 351.40, PAN(0.4, 0.6, 1.1)),                 # fields covered it
    shot("pom_hackert1799.jpg", 351.40, 357.00, IN(1.0, 1.10)),                    # the 1590s canal
    inset("pom_timeline.png", 357.00, 362.40, max_up=1.0),                         # straight through the buried city
    shot("pom_fresco.jpg",    362.40, 368.30, PAN(0.4, 0.6, 1.12)),                # walls, paintings, inscriptions
    shot("pom_hackert1794.jpg", 368.30, 374.40, IN(1.0, 1.10)),                    # hidden in plain sight
    shot("pom_sain.jpg",      374.40, 379.00, IN(1.0, 1.12)),                      # excavations began in 1748
    shot("pom_streets.jpg",   379.00, 385.30, TILT(0.6, 0.45, 1.12)),              # streets, cart ruts
    shot("pom_electoral.jpg", 385.30, 389.60, IN(1.0, 1.12, (0.5, 0.45))),         # election slogans
    shot("pom_bakery.jpg",    389.60, 394.00, IN(1.0, 1.10)),                      # everyday Roman life
    shot("pom_aerial.jpg",    394.00, 398.675, OUT(1.12, 1.0)),                    # almost found 150 years earlier
])

# ---------------- 07_machu_picchu ----------------
place("#4", "MACHU PICCHU", "PERU", "frames_machu", 398.675, 401.80, 405.30, 460.675, [
    shot("mac_canyon1912.jpg", 405.30, 411.60, IN(1.0, 1.10)),                     # above the Urubamba River (1912)
    shot("mac_urubamba.jpg",  411.60, 417.00, PAN(0.4, 0.6, 1.12)),                # a local farmer told him
    shot("mac_stairway.jpg",  417.00, 421.60, TILT(0.6, 0.4, 1.1), crop=[0.0, 0.4, 1.0, 1.0]),                # a boy led him the rest of the way
    shot("hk_machu.jpg",      421.60, 426.40, IN(1.0, 1.10)),                      # a city of granite in the clouds
    shot("mac_hb10.jpg",      426.40, 431.00, IN(1.0, 1.10)),                      # "the lost city of the Incas"
    shot("mac_terraces.jpg",  431.00, 437.80, PAN(0.4, 0.6, 1.1)),                 # families growing crops
    inset("mac_lizarraga.jpg", 437.80, 443.60, max_up=1.3, crop=[0.0, 0.0, 0.6, 1.0]),                        # A. Lizárraga, 1902
    shot("mac_yearbefore.jpg", 443.60, 447.50, TILT(0.45, 0.6, 1.08)),             # nine years before Bingham
    shot("mac_stone.jpg",     447.50, 454.00, IN(1.0, 1.10)),                      # royal estate of Pachacuti
    shot("mac_pano.jpg",      454.00, 461.475, PAN(0.35, 0.65, 1.0)),              # found in 1911
])

# ---------------- 08_ubar ----------------
place("#3", "UBAR", "OMAN", "frames_ubar", 461.475, 464.60, 468.10, 523.625, [
    shot("uba_boswellia.jpg", 468.10, 474.60, IN(1.0, 1.10)),                      # frankincense worth a fortune
    inset("uba_frank.jpg",    474.60, 479.00, max_up=1.3),                         # Ubar, Iram of the Pillars
    shot("uba_dunes3.jpg",    479.00, 484.00, PAN(0.4, 0.6, 1.1)),                 # the Atlantis of the Sands
    shot("uba_launch.jpg",    484.00, 488.60, TILT(0.6, 0.4, 1.1)),                # Space Shuttle Challenger, 1984
    inset("uba_radar.jpg",    488.60, 495.80, max_up=1.0),                         # radar sees through dry sand
    inset("uba_optrad.jpg",   495.80, 503.00, max_up=0.9),                         # faint caravan tracks
    shot("uba_shisr.jpg",     503.00, 511.00, IN(1.0, 1.12)),                      # a remote well called Shisr
    shot("uba_dunes1b.jpg",   511.00, 517.40, OUT(1.12, 1.0)),                     # fortress over a collapsed cave
    shot("uba_rub.jpg",       517.40, 524.425, IN(1.0, 1.10)),                     # found from space
])

# ---------------- 09_valeriana ----------------
place("#2", "VALERIANA", "MEXICO", "frames_valeriana", 524.425, 527.60, 531.10, 589.10, [
    shot("val_mar.jpg",       531.10, 535.60, PAN(0.4, 0.6, 1.1)),                 # found on a computer
    shot("val_estr2view.jpg", 535.60, 543.00, TILT(0.55, 0.4, 1.08)),              # old lidar data
    shot("hk_calbio.jpg",     543.00, 548.00, IN(1.0, 1.10)),                      # beneath the trees (hook use 9 min ago)
    shot("val_selva.jpg",     548.00, 555.00, PAN(0.4, 0.6, 1.1)),                 # forests of southern Mexico
    shot("val_str2.jpg",      555.00, 559.90, IN(1.0, 1.10)),                      # a hidden Maya city
    shot("val_xpuhil.jpg",    559.90, 566.40, IN(1.0, 1.12)),                      # pyramids, plazas, ballcourt
    shot("val_pyramid.jpg",   566.40, 572.40, PAN(0.4, 0.6, 1.1)),                 # 6,600 Maya structures
    shot("val_xpujil.jpg",    572.40, 578.60, IN(1.0, 1.10)),                      # he had driven past
    shot("val_laguna.jpg",    578.60, 583.00, PAN(0.42, 0.58, 1.05)),              # named after a lagoon
    shot("val_str1.jpg",      583.00, 589.90, OUT(1.12, 1.0)),                     # many more cities
])

# ---------------- 10_troy ----------------
place("#1", "TROY", "TURKEY", "frames_troy", 589.90, 593.00, 596.50, 657.825, [
    shot("tro_horse.jpg",     596.50, 600.40, IN(1.0, 1.10)),                         # Helen, Achilles, the Trojan Horse
    shot("tro_site1.jpg",     600.40, 605.70, PAN(0.4, 0.6, 1.1)),                         # scholars doubted
    shot("tro_hisarlik.jpg",  605.70, 612.10, IN(1.0, 1.10)),                      # a hill called Hisarlik
    shot("tro_site2.jpg",     612.10, 617.30, PAN(0.4, 0.6, 1.1)),                 # Troy lay underneath
    shot("tro_trench2658.jpg", 617.30, 622.50, IN(1.0, 1.10)),                     # Schliemann, 1870
    shot("tro_trench7757.jpg", 622.50, 629.00, PAN(0.6, 0.4, 1.1)),                # a huge trench
    shot("tro_priam01.jpg",   629.00, 636.00, IN(1.0, 1.12)),                      # Priam's Treasure
    shot("tro_ruins.jpg",     636.00, 641.60, IN(1.0, 1.10)),                      # nine cities stacked
    shot("tro_priam22.jpg",   641.60, 645.60, IN(1.0, 1.10)),                      # 1,000 years older
    shot("tro_trench2650.jpg", 645.60, 650.00, PAN(0.4, 0.6, 1.1)),                # the trench destroyed much
    inset("tro_eastgate.jpg", 650.00, 653.40, max_up=1.0),                         # a real address
    shot("tro_priam19.jpg",   653.40, 658.625, OUT(1.12, 1.0)),                    # Pushkin Museum, Moscow
])

# ---------------- 11_atlantis (card ATLANTIS, Mediterranean map) ----------------
place("ATLANTIS", "THE CITY NEVER FOUND", "PLATO, c. 360 BC", "frames_atlantis", 658.625, 661.80, 665.30, 763.125, [
    inset("atl_platovat.jpg", 665.30, 670.20, max_up=0.75),                        # Plato wrote about Atlantis
    inset("atl_platowell.jpg", 670.20, 678.40, max_up=0.75),                        # Timaeus and Critias
    shot("atl_gib_sts.jpg",   678.40, 684.40, IN(1.0, 1.12)),                      # the Pillars of Heracles
    shot("atl_gib2023.jpg",   684.40, 690.00, PAN(0.4, 0.6, 1.1)),                 # larger than Libya and Asia
    shot("atl_storm1.jpg",    690.00, 696.30, IN(1.0, 1.10)),                      # war against Athens
    shot("atl_storm2.jpg",    696.30, 702.80, PAN(0.4, 0.6, 1.1)),                 # sank into the sea
    shot("kircher.jpg",       702.80, 713.70, {"s0": 0.70, "s1": 0.80, "c0": [0.5, 0.5], "c1": [0.5, 0.5],
                                               "rot0": 0.0, "rot1": -180.0}, x=0.8), # Kircher 1669, south at the top
    inset("atl_insula.jpg",   713.70, 720.50, max_up=1.2),                         # Donnelly, 1882
    inset("atl_hypo.jpg",     720.50, 726.60, max_up=0.9),                         # a century of searching
    shot("atl_san_iss.jpg",   726.60, 731.40, IN(1.0, 1.12)),                      # Santorini
    shot("atl_sanpano.jpg",   731.40, 739.00, PAN(0.3, 0.7, 1.0)),                 # around 1600 BC it exploded
    shot("atl_akro11.jpg",    739.00, 743.60, IN(1.0, 1.10)),                      # Akrotiri under ash
    shot("atl_ships.jpg",     743.60, 748.80, PAN(0.3, 0.7, 1.05)),                # the Minoan civilization
    shot("atl_neakameni.jpg", 748.80, 753.50, IN(1.0, 1.10)),                      # Plato invented it
    shot("atl_spring.jpg",    753.50, 758.60, IN(1.0, 1.10)),                      # never a place at all
    shot("atl_troywalls3.jpg", 758.60, 763.925, IN(1.0, 1.12)),                    # ... the same about Troy
], lower="ATLANTIS", lower_num="")

# ---------------- 12_outro ----------------
shots.append(shot("pet_aaron.jpg", 763.925, DURATION, IN(1.0, 1.06, (0.5, 0.45)), xout=0))
overlays.append({"type": "endcard", "t0": 764.4, "t1": DURATION, "fin": 1.2, "fout": 0.6})

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
