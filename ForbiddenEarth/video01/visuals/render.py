"""Forbidden Earth compositor: stills with slow zoom/pan, unified grade, vignette, crossfades,
title cards, brand card, lower third, map frame sequences. Pipes frames to ffmpeg.

python render.py edl.json out.mp4 [--from 0 --to 92.5] [--stills t1,t2,...]
"""
import json, os, subprocess, sys, math, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
HERE = os.path.dirname(os.path.abspath(__file__))
F = lambda n: os.path.join(HERE, "fonts", n)
AMBER = (224, 168, 74)

def smooth(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

# ---------- look ----------
def grade(img):
    x = img.astype(np.float32) / 255.0
    lum = x @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    lo, hi = np.percentile(lum, 0.5), np.percentile(lum, 99.5)
    st = np.clip((x - lo) / max(hi - lo, 1e-3), 0, 1)
    x = 0.65 * st + 0.35 * x
    lum = x @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    x = lum[..., None] + (x - lum[..., None]) * 0.72          # desaturate
    x = np.clip(x * 0.84, 0, 1) ** 1.12                         # exposure + contrast
    lum = (x @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    x = x + ((1 - lum) ** 2) * np.array([-0.025, 0.012, 0.03], np.float32)   # teal shadows
    x = x + (lum ** 2) * np.array([0.03, 0.012, -0.02], np.float32)          # warm highlights
    return np.clip(0.015 + 0.975 * x, 0, 1)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
VIGNETTE = (1 - 0.5 * np.clip(_r, 0, 1) ** 2.0)[..., None].astype(np.float32)

@functools.lru_cache(maxsize=12)
def load_still(path, smax, crop):
    im = cv2.cvtColor(cv2.imread(os.path.join(HERE, path), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    if crop:  # crop = (x0,y0,x1,y1) normalized, e.g. to cut a border or caption strip
        h, w = im.shape[:2]; x0, y0, x1, y1 = crop
        im = im[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
    h, w = im.shape[:2]
    f = max(W / w, H / h) * smax
    nw, nh = int(math.ceil(w * f)), int(math.ceil(h * f))
    im = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_AREA if f < 1 else cv2.INTER_LANCZOS4)
    return grade(im)

def still_frame(s, u):
    m = s.get("move", {})
    s0, s1 = m.get("s0", 1.0), m.get("s1", 1.08)
    c0, c1 = m.get("c0", [0.5, 0.5]), m.get("c1", [0.5, 0.5])
    smax = max(s0, s1)
    img = load_still(s["src"], smax, tuple(s["crop"]) if s.get("crop") else None)
    ih, iw = img.shape[:2]
    p = 0.55 * u + 0.45 * smooth(u)
    k = (s0 + (s1 - s0) * p) / smax
    cx = (c0[0] + (c1[0] - c0[0]) * p) * iw; cy = (c0[1] + (c1[1] - c0[1]) * p) * ih
    hw, hh = W / 2 / k, H / 2 / k
    cx = min(max(cx, hw), iw - hw); cy = min(max(cy, hh), ih - hh)
    M = np.float32([[k, 0, W / 2 - k * cx], [0, k, H / 2 - k * cy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def seq_frame(s, t):
    d = os.path.join(HERE, s["frames"]); files = sorted(os.listdir(d))
    i = min(int((t - s["t0"]) * FPS), len(files) - 1); i = max(i, 0)
    return cv2.cvtColor(cv2.imread(os.path.join(d, files[i])), cv2.COLOR_BGR2RGB).astype(np.float32) / 255

# ---------- text layers ----------
def font(n, size): return ImageFont.truetype(F(n), size)

def draw_tracked(d, xy, text, fnt, fill, tracking=0, anchor_center=False):
    widths = [d.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x, y = xy
    if anchor_center: x -= total / 2
    for ch, w in zip(text, widths):
        d.text((x, y), ch, font=fnt, fill=fill); x += w + tracking
    return total

@functools.lru_cache(maxsize=8)
def card_layer(num, name, sub):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    draw_tracked(d, (W / 2, 250), num, font("Oswald-Bold.ttf", 300), AMBER + (255,), 6, True)
    draw_tracked(d, (W / 2, 615), name, font("Oswald-Bold.ttf", 120), (245, 245, 242, 255), 10, True)
    d.rectangle([W / 2 - 70, 842, W / 2 + 70, 846], fill=AMBER + (255,))
    draw_tracked(d, (W / 2, 866), sub, font("Inter-Bold.ttf", 40), (200, 205, 207, 255), 12, True)
    return np.asarray(L).astype(np.float32) / 255

@functools.lru_cache(maxsize=2)
def brand_layer():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    draw_tracked(d, (W / 2, 430), "FORBIDDEN EARTH", font("Oswald-Bold.ttf", 170), (245, 245, 242, 255), 16, True)
    d.rectangle([W / 2 - 160, 660, W / 2 + 160, 664], fill=AMBER + (255,))
    return np.asarray(L).astype(np.float32) / 255

@functools.lru_cache(maxsize=8)
def lower_layer(num, text):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    x, y = 96, H - 150
    for dd, col in [(ds, (0, 0, 0, 170))]:
        dd.rectangle([x, y, x + 7, y + 58], fill=col)
        w = draw_tracked(dd, (x + 26, y - 4), num, font("Oswald-Bold.ttf", 50), col, 2)
        draw_tracked(dd, (x + 26 + w + 22, y + 10), text, font("Inter-Bold.ttf", 34), col, 3)
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    d = ImageDraw.Draw(L)
    d.rectangle([x, y, x + 7, y + 58], fill=AMBER + (255,))
    w = draw_tracked(d, (x + 26, y - 4), num, font("Oswald-Bold.ttf", 50), AMBER + (255,), 2)
    draw_tracked(d, (x + 26 + w + 22, y + 10), text, font("Inter-Bold.ttf", 34), (242, 242, 240, 255), 3)
    L = Image.alpha_composite(sh, L)
    return np.asarray(L).astype(np.float32) / 255

def over(base, layer, a):
    al = layer[..., 3:4] * a
    return base * (1 - al) + layer[..., :3] * al

# ---------- timeline ----------
def shot_image(s, t):
    u = (t - s["t0"]) / max(s["t1"] - s["t0"], 1e-3)
    u = min(max(u, 0), 1)
    if "frames" in s: return seq_frame(s, t) * VIGNETTE
    if s.get("card"):
        bg = still_frame({**s, "move": s.get("move", {"s0": 1.12, "s1": 1.18})}, u)
        bg = cv2.GaussianBlur(bg, (0, 0), 9) * 0.38
        lay = card_layer(s["num"], s["name"], s["sub"])
        a = smooth((t - s["t0"] - 0.15) / 0.5)
        sh = int(round(18 * (1 - a)))
        if sh: lay = np.roll(lay, sh, axis=0)
        return over(bg * VIGNETTE, lay, a)
    return still_frame(s, u) * VIGNETTE

def weight(s, t):
    xi, xo = s.get("xin", 0.5), s.get("xout", 0.5)
    a = 1.0 if xi <= 0 else smooth((t - (s["t0"] - xi / 2)) / xi)
    b = 1.0 if xo <= 0 else 1 - smooth((t - (s["t1"] - xo / 2)) / xo)
    return min(a, b)

def frame(edl, t):
    shots = [s for s in edl["shots"] if s["t0"] - s.get("xin", .5) / 2 <= t <= s["t1"] + s.get("xout", .5) / 2]
    out = np.zeros((H, W, 3), np.float32)
    for s in sorted(shots, key=lambda s: s["t0"]):
        w = weight(s, t)
        if w <= 0: continue
        out = out * (1 - w) + shot_image(s, t) * w if w < 1 else shot_image(s, t)
    for o in edl.get("overlays", []):
        if not (o["t0"] <= t <= o["t1"]): continue
        a = smooth((t - o["t0"]) / o.get("fin", 0.6)) * (1 - smooth((t - (o["t1"] - o.get("fout", 0.6))) / o.get("fout", 0.6)))
        if o["type"] == "brand":
            out = out * (1 - 0.45 * a)
            out = over(out, brand_layer(), a)
        elif o["type"] == "lower":
            out = over(out, lower_layer(o["num"], o["text"]), a)
    fade_in = smooth(t / 0.4); fade_out = 1 - smooth((t - (edl["duration"] - 0.6)) / 0.6)
    return out * fade_in * fade_out

def main():
    edl = json.load(open(sys.argv[1])); out = sys.argv[2]
    args = sys.argv[3:]
    if "--stills" in args:
        ts = [float(x) for x in args[args.index("--stills") + 1].split(",")]
        for t in ts:
            f = frame(edl, t)
            Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8)).save(f"{out}_{t:06.2f}.jpg", quality=90)
        return
    t_from = float(args[args.index("--from") + 1]) if "--from" in args else 0.0
    t_to = float(args[args.index("--to") + 1]) if "--to" in args else edl["duration"]
    n = int(round((t_to - t_from) * FPS))
    audio = os.path.join(HERE, edl["audio"])
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-ss", str(t_from), "-t", str(t_to - t_from), "-i", audio,
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-af", f"afade=t=out:st={max(t_to - t_from - 0.4, 0)}:d=0.4", "-shortest", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    rng = np.random.default_rng(7)
    for i in range(n):
        t = t_from + i / FPS
        f = frame(edl, t) * 255 + rng.uniform(-0.6, 0.6, (H, W, 1)).astype(np.float32)  # dither vs banding
        p.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
        if i % 300 == 0: print(f"{t:6.1f}s", flush=True)
    p.stdin.close(); p.wait()
    print("done", out)

if __name__ == "__main__":
    main()
