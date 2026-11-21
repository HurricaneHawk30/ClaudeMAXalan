"""Build Forbidden Earth video18 narration with Kokoro (am_michael, speed 0.95).

Usage: python voice_build.py script_original.txt out_dir [--check]
"""
import os, re, subprocess, sys

SR = 24000
VOICE, SPEED = "am_michael", 0.95
PARA_GAP, SECTION_GAP = 0.4, 0.8

# 1) Numbers, years, units, symbols -> words. Every numeric token must be listed here.
NUM = {"1227":"twelve twenty-seven","1916":"nineteen sixteen","1930s":"nineteen thirties","1936":"nineteen thirty-six","1943":"nineteen forty-three",
  "1950s":"nineteen fifties","1953":"nineteen fifty-three","1966":"nineteen sixty-six","1970s":"nineteen seventies","1974":"nineteen seventy-four",
  "1990s":"nineteen nineties","1991":"nineteen ninety-one","1996":"nineteen ninety-six","2017":"twenty seventeen","2018":"twenty eighteen",
  "2019":"twenty nineteen","2025":"twenty twenty-five","2026":"twenty twenty-six"}
PRE = [("October 16, 1964","October sixteenth, nineteen sixty-four"),("Metro-2","Metro two"),("Area 51","Area fifty-one"),("RAF","R A F"),("U.S.","U S"),("UNESCO","Unesco")]
TOKEN = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?(?:st|nd|rd|th|s)?\b")

# 2) Pronunciation fixes (misaki/Kokoro phonemes, US).
PHON = {"tours":"tˈʊɹz","Tours":"tˈʊɹz","Athos":"ˈɑθɔs","Aegean":"əʤˈiən","Daisen":"dIsˈɛn","Kofun":"kˈOfun","Sakai":"sɑkˈI",
  "Nintoku":"nintˈOku","Lop Nur":"lˈɑp nˈʊɹ","Porton":"pˈɔɹtən","Gruinard":"ɡɹˈɪnjəɹd","Menwith":"mˈɛnwɪθ","Diego Garcia":"diˈAɡO ɡɑɹsˈiə",
  "Chagos":"ʧˈɑɡOs","Mauritius":"məɹˈɪʃəs","Genghis":"ʤˈɛŋɡɪs","Burkhan Khaldun":"buɹkˈɑn kɑldˈun","Ikh Khorig":"ˈik kˈɔɹɪɡ",
  "Yamantau":"jˌɑmɑntˈɑu","Mezhgorye":"mɛʒɡˈɔɹjə","Threadneedle":"θɹˈɛdnˌidəl","Aksum":"ˈɑksum","Panmunjom":"pˌɑnmunʤˈɑm","Unesco":"junˈɛskO"}
NAME = re.compile(r"\b(" + "|".join(PHON) + r")\b")

def parse(path):
    secs, cur = [], None
    for line in open(path, encoding="utf-8").read().splitlines():
        m = re.match(r"^===\s*(\S+)\s*===$", line.strip())
        if m:
            cur = (m.group(1), []); secs.append(cur)
        elif line.strip() and cur:
            cur[1].append(line.strip())
    return secs

def normalize(p):
    for a, b in PRE: p = p.replace(a, b)
    def num(m):
        t = m.group(0)
        if t not in NUM: raise SystemExit(f"No spelling for number token {t!r} in: {p}")
        return NUM[t]
    p = TOKEN.sub(num, p)
    return NAME.sub(lambda m: f"[{m.group(1)}](/{PHON[m.group(1)]}/)", p)

def main():
    src, out = sys.argv[1], sys.argv[2]
    secs = [(n, [normalize(p) for p in ps]) for n, ps in parse(src)]
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "script_tts.txt"), "w", encoding="utf-8") as f:
        for n, ps in secs: f.write(f"=== {n} ===\n" + "\n\n".join(ps) + "\n\n")
    from kokoro import KPipeline
    import numpy as np, soundfile as sf
    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    if "--check" in sys.argv:
        for n, ps in secs:
            for p in ps:
                _, toks = pipe.g2p(p)
                bad = [t.text for t in toks if not t.phonemes or "❓" in (t.phonemes or "")]
                if bad: print(n, "UNKNOWN:", bad)
        return
    def enc(audio, mp3):
        wav = mp3[:-4] + ".tmp.wav"
        sf.write(wav, audio, SR)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ar", "44100", "-codec:a", "libmp3lame",
                        "-b:a", "192k", mp3], check=True)
        os.remove(wav)  # temp file created just above
    full, timings, t = [], [], 0.0
    for i, (n, ps) in enumerate(secs):
        parts = []
        for j, p in enumerate(ps):
            if j: parts.append(np.zeros(int(PARA_GAP * SR), dtype=np.float32))
            parts += [r.audio.numpy() for r in pipe(p, voice=VOICE, speed=SPEED, split_pattern=None)]
        sec = np.concatenate(parts).astype(np.float32)
        enc(sec, os.path.join(out, f"{n}.mp3"))
        if i:
            full.append(np.zeros(int(SECTION_GAP * SR), dtype=np.float32)); t += SECTION_GAP
        start = t; t += len(sec) / SR
        timings.append((n, start, t)); full.append(sec)
        print(f"OK {n}.mp3 {len(sec)/SR:.2f}s", flush=True)
    enc(np.concatenate(full), os.path.join(out, "full.mp3"))
    fmt = lambda s: f"{int(s//60):02d}:{s%60:06.3f}"
    with open(os.path.join(out, "timings.txt"), "w", encoding="utf-8") as f:
        f.write("Forbidden Earth - video18 - full.mp3 (Kokoro am_michael, speed 0.95)\n")
        f.write("section          start        end          length\n")
        for n, a, b in timings:
            f.write(f"{n:<16} {fmt(a)}  {fmt(b)}  {b-a:7.3f}s\n")
        f.write(f"\nTOTAL            {fmt(t)}  ({t:.3f}s)\n")
    print(open(os.path.join(out, "timings.txt")).read())

if __name__ == "__main__":
    main()
