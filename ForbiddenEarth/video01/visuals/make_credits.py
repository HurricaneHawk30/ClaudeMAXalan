"""Build credits.txt (for the video description) and the contact grid from edl.json.
python make_credits.py edl.json credits.txt grid.jpg
"""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
edl = json.load(open(sys.argv[1]))
used, seen = [], set()
for s in sorted(edl["shots"], key=lambda s: s["t0"]):
    src = s.get("src")
    if src and src not in seen:
        seen.add(src); used.append((s["t0"], src))

def tc(t): return f"{int(t // 60)}:{t % 60:04.1f}"
lines = ["IMAGE CREDITS - Forbidden Earth, episode 1 (preview: #10 Gruinard Island)", ""]
bad = []
for i, (t, src) in enumerate(used, 1):
    m = json.load(open(os.path.join(HERE, os.path.splitext(src)[0] + ".json")))
    if not m["license_ok"]: bad.append(src)
    title = re.sub(r"\.(jpe?g|png|tiff?)$", "", m["title"], flags=re.I)
    author = m["author"] or m["credit"] or "Unknown"
    lic = m["license"] + (f" ({m['license_url']})" if m["license_url"] else "")
    lines.append(f"{i}. \"{title}\" by {author}. {lic}. Source: {m['url']}")
lines += ["", "Changes: images were cropped, color-graded and animated (zoom/pan).",
          "Maps: made with Natural Earth data (public domain), naturalearthdata.com.",
          "Fonts: Oswald and Inter (SIL Open Font License).",
          "Narration: Kokoro TTS (Apache 2.0)."]
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
if bad: print("\n!! LICENSE CHECK FAILED:", bad); sys.exit(1)
args = [f"{i}. {os.path.basename(os.path.splitext(src)[0])}  @{tc(t)}={os.path.join(HERE, src)}"
        for i, (t, src) in enumerate(used, 1)]
maps = sorted(os.listdir(os.path.join(HERE, "maps", "frames_gruinard")))
args.append(f"{len(used) + 1}. map (Natural Earth)={os.path.join(HERE, 'maps', 'frames_gruinard', maps[-1])}")
subprocess.run([sys.executable, os.path.join(HERE, "contact.py"), sys.argv[3], "5"] + args, check=True)
