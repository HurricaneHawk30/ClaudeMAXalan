"""Build credits.txt (for the video description) and the contact grid from edl.json.
python make_credits.py edl.json credits.txt grid.jpg [credits_compact.txt]
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
lines = ["IMAGE CREDITS - Forbidden Earth, episode 4: The Most Extreme Places on Earth", ""]
compact, attrib, pd_auth, pd_src, attrib_raw = [], [], [], [], []
bad = []
OGL = "Contains public sector information licensed under the Open Government Licence v3.0"
def is_ogl3(lic): return bool(re.match(r"^ogl ?v?3(\.0)?$", lic.strip(), re.I))
TL, AL, SHORT = 24, 21, False      # title / author lengths; SHORT drops the "CC " prefix (YouTube version)
def clean_author(a):
    a = re.sub(r"^File:[^:]+:\s*", "", a)                      # derivative-work prefixes
    a = re.sub(r"\(talk\).*$|\(https?://[^)]*\)|https?://\S+", "", a)
    a = re.sub(r"\s+from\s+.*$", "", a)                        # Flickr "from City, Country"
    a = re.sub(r"(Unknown author)+.*$|^No machine-readable author.*$", "Unknown", a)
    a = re.sub(r"\s*derivative work:.*$|\s*\(color correction.*$|,? and U\.S\./Japan ASTER Science Team", "", a)
    a = a.replace("Photographer: ", "").strip(" .,;")
    a = re.sub(r"^United States Department of (Energy|Defense).*$", "US Dept. of \\1", a)
    a = re.sub(r",? uploaded by.*$|^Original:\s*", "", a)
    return (a[:AL].rstrip() + "…") if len(a) > AL + 1 else (a or "Unknown")

def compact_line(title, author, lic):
    t = re.sub(r"\s*-\s*geograph\.org\.uk\s*-\s*\d+|\s*\(\d{6,}\)|\s*-\s*panoramio|\s*-\s*A\d+X?$", "", title)
    t = re.sub(r"^(France|Meuse), ", "", t).replace("Kawah-Ijen Indonesia ", "Kawah Ijen, ")
    t = re.sub(r"\s+-\s+", ", ", t).replace("-", " ")
    t = re.sub(r",? (Java|East Java), Indonesia|, Pennsylvania|, Montserrat|, Western Australia", "", t).strip(" ,")
    t = (t[:TL].rstrip(" ,") + "…") if len(t) > TL + 1 else t
    sl = "OGL v3.0" if is_ogl3(lic) else ("PD" if lic.lower().startswith(("public domain", "pd")) else lic.replace(" igo", ""))
    if SHORT: sl = sl.replace("CC ", "")
    return f"{t} — {clean_author(author)} ({sl})"

for i, (t, src) in enumerate(used, 1):
    m = json.load(open(os.path.join(HERE, os.path.splitext(src)[0] + ".json")))
    if m.get("generated"): continue          # our own diagrams: no third-party credit
    if not (m["license_ok"] or is_ogl3(m["license"])): bad.append(src)
    title = re.sub(r"\.(jpe?g|png|tiff?)$", "", m["title"], flags=re.I)
    author = m["author"] or m["credit"] or "Unknown"
    lic = m["license"] + (f" ({m['license_url']})" if m["license_url"] else "")
    if is_ogl3(m["license"]): lic = "Open Government Licence v3.0 (" + OGL + ")"
    lines.append(f"{i}. \"{title}\" by {author}. {lic}. Source: {m['url']}")
    compact.append(compact_line(title, author, m["license"]))
    if m["license"].lower().startswith(("public domain", "pd", "cc0")):
        pd_src.append(m.get("source", ""))
        pd_auth.append(author)
    else:
        attrib.append(compact_line(title, author, m["license"])); attrib_raw.append((title, author, m["license"]))
lines += ["", "Changes: images were cropped, color-graded and animated (zoom/pan).",
          "Maps: made with Natural Earth data (public domain), naturalearthdata.com.",
          "Fonts: Oswald and Inter (SIL Open Font License).",
          "Narration: Kokoro TTS (Apache 2.0)."]
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(lines) + "\n")
if len(sys.argv) > 4:
    if any(is_ogl3(json.load(open(os.path.join(HERE, os.path.splitext(src)[0] + ".json")))["license"]) for _, src in used):
        compact.append(OGL + ".")
    compact.append("PD = public domain. Maps: Natural Earth (PD).")
    txt = "\n".join(compact) + "\n"
    open(sys.argv[4], "w", encoding="utf-8").write(txt)
    print(f"\ncompact: {len(compact)} lines, {len(txt)} characters")
    # YouTube version: attribution-required licences one per line; public domain / CC0 grouped
    from collections import Counter
    def org(a):
        keys = [("Geological Survey", "USGS"), ("USGS", "USGS"), ("Bill Evans", "USGS"), ("Lockwood", "USGS"),
                ("NASA", "NASA"), ("Landsat", "NASA"), ("CDC", "CDC"), ("USCDCP", "CDC"), ("NOAA", "NOAA"),
                ("USFWS", "USFWS"), ("Navy", "US Navy"), ("military", "US military"), ("Department of", "US Dept. of Energy/Defense"),
                ("Army", "US Army"), ("NIST", "NIST"), ("Cuville", "French Army photo archive"), ("Passet", "French Army photo archive")]
        for k, v in keys:
            if k.lower() in a.lower(): return v
        return clean_author(a)
    globals().update(AL=21)
    cnt = Counter(org(a) for a in pd_auth)
    parts, used_len = [], 0
    for k, v in cnt.most_common():
        item = f"{k} ({v})" if v > 1 else k
        if used_len + len(item) > 120: parts.append("and others"); break
        parts.append(item); used_len += len(item) + 2
    pd_line = f"Public domain / CC0 ({sum(cnt.values())} images): " + ", ".join(parts) + "."
    LIMIT = int(os.environ.get("YT_LIMIT", "3800"))
    raw_attrib = [(m_t, m_a, m_l) for (m_t, m_a, m_l) in attrib_raw]
    for TL, AL, SHORT in [(24, 21, False), (22, 18, True), (20, 16, True), (18, 15, True), (16, 14, True), (14, 12, True), (12, 11, True)]:
        globals().update(TL=TL, AL=AL, SHORT=SHORT)
        lines_a = [compact_line(*x) for x in raw_attrib]
        head = ["Images (BY = CC BY, BY-SA = CC BY-SA, creativecommons.org/licenses):"] if SHORT else []
        yt = head + lines_a + [pd_line, "Maps: Natural Earth (public domain). Full list with links: credits.txt."]
        ytxt = "\n".join(yt) + "\n"
        if len(ytxt) <= LIMIT: break
    open(os.path.join(os.path.dirname(sys.argv[4]) or ".", "credits_youtube.txt"), "w", encoding="utf-8").write(ytxt)
    print(f"youtube: {len(yt)} lines, {len(ytxt)} characters")
print("\n".join(lines))
if bad: print("\n!! LICENSE CHECK FAILED:", bad); sys.exit(1)
args = [f"{i}. {os.path.basename(os.path.splitext(src)[0])}  @{tc(t)}={os.path.join(HERE, src)}"
        for i, (t, src) in enumerate(used, 1)]
n = len(used)
for s in sorted(edl["shots"], key=lambda s: s["t0"]):
    if "frames" in s:
        d = os.path.join(HERE, s["frames"]); last = sorted(os.listdir(d))[-1]; n += 1
        args.append(f"{n}. map {os.path.basename(s['frames'])[7:]} @{tc(s['t0'])}={os.path.join(d, last)}")
subprocess.run([sys.executable, os.path.join(HERE, "contact.py"), sys.argv[3], "8"] + args, check=True)
