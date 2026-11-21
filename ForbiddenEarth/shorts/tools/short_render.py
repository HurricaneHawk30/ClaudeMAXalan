"""Render a vertical Forbidden Earth Short (1080x1920, 30 fps, H.264 + AAC).

python short_render.py NN [--stills t1,t2,...]
Reads shorts/shortNN/plan.json:
  {"video": "video05", "hook": "COOKING SINCE 1725", "hook_key": ["1725"], "frames": ["botin/botin_13", ...]}
plus voice/voice.mp3, voice/words.json (Whisper) and the text in scripts.md.
Writes render/short.mp4, contact.jpg, credits.txt, work/subs.json.
"""
import difflib, json, os, re, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); FE = os.path.dirname(ROOT)
W, H, FPS = 1080, 1920, 30
FONTS = os.path.join(FE, "video16", "visuals", "fonts")
OSW, INTER = os.path.join(FONTS, "Oswald-Bold.ttf"), os.path.join(FONTS, "Inter-Bold.ttf")
WHITE, AMBER = (245, 240, 230), (242, 169, 59)
XFADE = 0.35
SAFE_L, SAFE_R = 70, 150                      # right 150 px: YouTube buttons
SUB_Y = int(H * 0.62)                         # subtitles at 60-65 % of height
NUMWORDS = set("one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen "
               "eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million zero point "
               "eighty-five forty-three thirty-five twenty-five".split())

sys.path.insert(0, HERE)
from short_voice import text_of

def font(p, s): return ImageFont.truetype(p, s)

# ---------- subtitles: script words with Whisper times ----------
def norm(w): return re.sub(r"[^a-z0-9]", "", w.lower())

def timed_words(nn, words):
    script = text_of(nn).split()
    a = [norm(w) for w in script]; b = [norm(x[2]) for x in words]
    t = [None] * len(script)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size): t[blk.a + k] = (words[blk.b + k][0], words[blk.b + k][1])
    known = [i for i, x in enumerate(t) if x]
    for i in range(len(t)):                      # interpolate unmatched words between neighbours
        if t[i]: continue
        p = max([k for k in known if k < i], default=None); q = min([k for k in known if k > i], default=None)
        t0 = t[p][1] if p is not None else 0.0; t1 = t[q][0] if q is not None else words[-1][1]
        lo = p if p is not None else -1; hi = q if q is not None else len(t)
        f0 = (i - lo) / (hi - lo); f1 = (i + 1 - lo) / (hi - lo)
        t[i] = (t0 + (t1 - t0) * f0, t0 + (t1 - t0) * f1)
    return [(w, s, e) for w, (s, e) in zip(script, t)]

def chunks(tw):
    out, cur = [], []
    for i, (w, s, e) in enumerate(tw):
        cur.append((w, s, e))
        txt = " ".join(x[0] for x in cur)
        nxt = tw[i + 1][0] if i + 1 < len(tw) else None
        if re.search(r"[.?!]$", w): out.append(cur); cur = []; continue
        if re.search(r"[,:;]$", w) and len(cur) >= 2: out.append(cur); cur = []; continue
        if len(cur) >= 4 or len(txt) >= 16:
            # keep a lone sentence-final word with this chunk if it still fits
            if nxt and re.search(r"[.?!]$", nxt) and len(txt + " " + nxt) <= 22 and len(cur) < 4: continue
            out.append(cur); cur = []
    if cur: out.append(cur)
    merged = []
    for c in out:                                # glue single leftover words to the previous chunk when short
        if merged and len(c) == 1 and len(" ".join(x[0] for x in merged[-1] + c)) <= 22 and not re.search(r"[.?!]$", merged[-1][-1][0]):
            merged[-1] = merged[-1] + c
        else: merged.append(c)
    out = merged
    res = []
    for i, c in enumerate(out):
        t1 = out[i + 1][0][1] if i + 1 < len(out) else c[-1][2] + 0.4
        res.append({"words": [x[0] for x in c], "t0": c[0][1], "t1": min(t1, c[-1][2] + 0.6)})
    return res

def is_key(w):
    n = norm(w)
    return bool(re.search(r"\d", w)) or n in NUMWORDS or w.lower().strip(".,?!:;") in NUMWORDS

def text_layer(lines_tokens, f, stroke, max_w, line_h, key=None):
    """lines_tokens: list of lines; each line list of (word, colour). Returns RGBA image of width W."""
    hgt = line_h * len(lines_tokens) + stroke * 4
    im = Image.new("RGBA", (W, hgt), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = (SAFE_L + W - SAFE_R) // 2
    for li, toks in enumerate(lines_tokens):
        sp = d.textlength(" ", font=f)
        widths = [d.textlength(w, font=f) for w, _ in toks]
        tot = sum(widths) + sp * (len(toks) - 1)
        x = cx - tot / 2; y = stroke * 2 + li * line_h
        for (w, col), wd in zip(toks, widths):
            d.text((x, y), w, font=f, fill=col, stroke_width=stroke, stroke_fill=(0, 0, 0))
            x += wd + sp
    return im

def wrap(tokens, f, max_w):
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    lines, cur = [], []
    for tok in tokens:
        test = " ".join(w for w, _ in cur + [tok])
        if cur and d.textlength(test, font=f) > max_w: lines.append(cur); cur = [tok]
        else: cur.append(tok)
    if cur: lines.append(cur)
    return lines

# ---------- pictures ----------
def load_shot(path, idx):
    img = Image.open(path).convert("RGB"); w, h = img.size
    scale = H * 1.04 / h; sw = int(w * scale)
    if sw >= W * 1.3:                                   # wide: pan across at full height
        big = np.asarray(img.resize((sw, int(h * scale)), Image.LANCZOS)).astype(np.float32) / 255
        return {"mode": "pan", "img": big, "dir": 1 if idx % 2 == 0 else -1}
    # narrow: blurred background + the whole picture in the middle
    bgs = max(W / w, H / h) * 1.1
    bg = img.resize((int(w * bgs), int(h * bgs)), Image.LANCZOS)
    l, t = (bg.width - W) // 2, (bg.height - H) // 2
    bg = bg.crop((l, t, l + W, t + H)).filter(ImageFilter.GaussianBlur(40))
    bg = np.asarray(bg).astype(np.float32) / 255 * 0.55
    fs = min(W / w, H * 0.8 / h); fg = np.asarray(img.resize((int(w * fs), int(h * fs)), Image.LANCZOS)).astype(np.float32) / 255
    return {"mode": "fit", "bg": bg, "fg": fg}

def shot_frame(sh, u):
    """u in [0,1] progress through the shot."""
    if sh["mode"] == "pan":
        big = sh["img"]; bh, bw = big.shape[:2]
        span = bw - W; x = (0.15 + 0.7 * u) if sh["dir"] > 0 else (0.85 - 0.7 * u)
        x0 = int(span * x); y0 = (bh - H) // 2
        return big[y0:y0 + H, x0:x0 + W]
    out = sh["bg"].copy(); fg = sh["fg"]; k = 1.0 + 0.05 * u
    fh, fw = int(fg.shape[0] * k), int(fg.shape[1] * k)
    f2 = cv2.resize(fg, (fw, fh), interpolation=cv2.INTER_LINEAR)
    if fw > W: c = (fw - W) // 2; f2 = f2[:, c:c + W]; fw = W
    y = (H - fh) // 2 - 60; x = (W - fw) // 2
    out[y:y + fh, x:x + fw] = f2
    return out

def over(base, layer, y):
    a = np.asarray(layer).astype(np.float32) / 255
    h = a.shape[0]; y = max(0, min(H - h, y))
    rgb, al = a[..., :3], a[..., 3:4]
    base[y:y + h] = base[y:y + h] * (1 - al) + rgb * al

# ---------- main ----------
def main():
    nn = sys.argv[1]; d = os.path.join(ROOT, f"short{nn}")
    plan = json.load(open(os.path.join(d, "plan.json")))
    words = json.load(open(os.path.join(d, "voice", "words.json")))
    dur_a = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                           os.path.join(d, "voice", "voice.mp3")]).decode())
    D = round(dur_a + 0.7, 2); END0 = D - 2.6
    tw = timed_words(nn, words); subs = chunks(tw)
    os.makedirs(os.path.join(d, "work"), exist_ok=True); os.makedirs(os.path.join(d, "render"), exist_ok=True)
    json.dump(subs, open(os.path.join(d, "work", "subs.json"), "w"), indent=1)
    # shots: even split, 3-5 s each
    frames = plan["frames"]; n = len(frames); step = D / n
    assert 3.0 <= step <= 5.0 + 1e-6, f"shot length {step:.2f}s outside 3-5 s ({n} shots for {D}s)"
    src = os.path.join(FE, plan["video"], "visuals", "src")
    paths = [os.path.join(src, f + (".jpg" if os.path.exists(os.path.join(src, f + ".jpg")) else ".png")) for f in frames]
    shots = [load_shot(p, i) for i, p in enumerate(paths)]
    # text layers
    fsub = font(OSW, 86); maxw = W - SAFE_L - SAFE_R - 40
    sub_layers = []
    for s in subs:
        toks = [(w, AMBER if is_key(w) else WHITE) for w in s["words"]]
        sub_layers.append(text_layer(wrap(toks, fsub, maxw), fsub, 7, maxw, 104))
    fh = font(OSW, 150)
    hk = [(w, AMBER if any(k.lower() in w.lower() for k in plan["hook_key"]) else WHITE) for w in plan["hook"].split()]
    hook_layer = text_layer(wrap(hk, fh, maxw), fh, 9, maxw, 172)
    fe1, fe2 = font(OSW, 104), font(INTER, 40)
    end1 = text_layer(wrap([(w, WHITE) for w in "FULL VIDEO ON THE CHANNEL".split()], fe1, maxw), fe1, 8, maxw, 124)
    end2 = text_layer([[("FORBIDDEN", AMBER), ("EARTH", AMBER)]], fe2, 4, maxw, 52)

    def frame(t):
        i = min(int(t / step), n - 1); u = (t - i * step) / step
        img = shot_frame(shots[i], u)
        if i + 1 < n and t > (i + 1) * step - XFADE:                # crossfade into the next shot
            a = (t - ((i + 1) * step - XFADE)) / XFADE
            img = img * (1 - a) + shot_frame(shots[i + 1], 0.0) * a
        img = np.ascontiguousarray(img, dtype=np.float32)
        if t < 2.0:
            a = min(1, t / 0.15) * min(1, (2.0 - t) / 0.2)
            img *= 1 - 0.25 * a
            lay = hook_layer if a >= 1 else Image.fromarray((np.asarray(hook_layer) * np.array([1, 1, 1, a])).astype(np.uint8))
            over(img, lay, 560 - hook_layer.height // 2)
        elif t >= END0:
            a = min(1, (t - END0) / 0.4)
            img *= 1 - 0.55 * a
            for lay, y in ((end1, 820 - end1.height // 2), (end2, 820 + end1.height // 2 + 10)):
                l2 = Image.fromarray((np.asarray(lay) * np.array([1, 1, 1, a])).astype(np.uint8))
                over(img, l2, y)
        else:
            for s, lay in zip(subs, sub_layers):
                if s["t0"] <= t < s["t1"]:
                    over(img, lay, SUB_Y - lay.height // 2); break
        return (np.clip(img, 0, 1) * 255).astype(np.uint8)

    if "--stills" in sys.argv:
        for t in sys.argv[sys.argv.index("--stills") + 1].split(","):
            Image.fromarray(frame(float(t))).save(os.path.join(d, "work", f"still_{float(t):05.1f}.jpg"), quality=88)
        return
    # audio: voice at -14 LUFS (two-pass loudnorm), padded to D
    va = os.path.join(d, "work", "voice_norm.m4a"); vm = os.path.join(d, "voice", "voice.mp3")
    af = f"apad,atrim=0:{D}"
    js = subprocess.run(["ffmpeg", "-hide_banner", "-i", vm, "-af", af + ",loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                         "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(js[js.rindex("{"):js.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vm, "-af", f"{af},{ln},aresample=48000", "-ac", "2", "-c:a", "aac", "-b:a", "160k", va], check=True)
    out = os.path.join(d, "render", "short.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", va, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                          "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    nfr = int(D * FPS); picks = {int(nfr * k / 8) for k in range(1, 8)} | {int(0.8 * FPS)}; contact = []
    for fi in range(nfr):
        fr = frame(fi / FPS); p.stdin.write(fr.tobytes())
        if fi in picks: contact.append(Image.fromarray(fr).resize((270, 480)))
    p.stdin.close(); p.wait()
    sheet = Image.new("RGB", (270 * 4 + 50, 480 * 2 + 30), (17, 17, 17))
    for k, im in enumerate(sorted(contact, key=lambda x: 0)[:8]): sheet.paste(im, (10 + (k % 4) * 280, 10 + (k // 4) * 490))
    sheet.save(os.path.join(d, "contact.jpg"), quality=88)
    # credits: one line per picture
    seen, lines = set(), []
    for f, pth in zip(frames, paths):
        if f in seen: continue
        seen.add(f); j = json.load(open(os.path.splitext(pth)[0] + ".json"))
        url = j.get("url") or j.get("source_url") or ""
        lic = j.get("license", ""); lu = j.get("license_url", "")
        lines.append(f"\"{j.get('title', f)}\" by {j.get('author', '')}. {lic}{' (' + lu + ')' if lu else ''}. Source: {url}")
    open(os.path.join(d, "credits.txt"), "w", encoding="utf-8").write(
        f"Image credits - Forbidden Earth Short {nn} (pictures from {plan['video']}):\n" + "\n".join(lines) + "\nImages were cropped and color graded.\n")
    print(out, D)

if __name__ == "__main__":
    main()
