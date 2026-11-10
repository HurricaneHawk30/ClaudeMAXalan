"""Build Forbidden Earth video01 narration with Kokoro (am_michael, speed 0.95).

Usage: python voice_build.py script_original.txt out_dir [--check]
"""
import os, re, subprocess, sys

SR = 24000
VOICE, SPEED = "am_michael", 0.95
PARA_GAP, SECTION_GAP = 0.4, 0.8

# 1) Numbers, years, units, symbols -> words. Every numeric token must be listed here.
NUM = {
    "1,746": "one thousand seven hundred and forty-six",
    "1962": "nineteen sixty-two", "48": "forty-eight", "1942": "nineteen forty-two",
    "1980s": "nineteen-eighties", "24th": "twenty-fourth", "1990": "nineteen ninety",
    "£500": "five hundred pounds", "150": "one hundred and fifty",
    "1976": "nineteen seventy-six", "49": "forty-nine",
    "1,200": "one thousand two hundred", "170": "one hundred and seventy",
    "99": "ninety-nine", "300": "three hundred", "700": "seven hundred",
    "1995": "nineteen ninety-five", "1997": "nineteen ninety-seven",
    "1980": "nineteen eighty", "1,000": "one thousand", "2020": "twenty twenty",
    "250": "two hundred and fifty", "1950s": "nineteen-fifties", "1966": "nineteen sixty-six",
    "2,000": "two thousand", "2007": "two thousand and seven", "47,000": "forty-seven thousand",
    "1946": "nineteen forty-six", "1958": "nineteen fifty-eight", "23": "twenty-three",
    "1954": "nineteen fifty-four", "1.5": "one point five", "1960s": "nineteen-sixties",
    "2016": "twenty sixteen", "1951": "nineteen fifty-one", "600": "six hundred",
    "10,000": "ten thousand", "1978": "nineteen seventy-eight", "1986": "nineteen eighty-six",
    "mid-2010s": "mid twenty-tens", "21st": "twenty-first",
    "100,000": "one hundred thousand", "300,000": "three hundred thousand", "50": "fifty",
    "3,500": "three thousand five hundred", "800": "eight hundred", "60": "sixty",
    "2021": "twenty twenty-one", "pH": "p H",
}
TOKEN = re.compile(r"mid-2010s|£\d+|\bpH\b|(?<![\w.])\d[\d,]*(?:\.\d+)?(?:st|th|s)?\b")

# 2) Pronunciation fixes (misaki/Kokoro phonemes, US).
PHON = {
    "Gruinard": "ɡɹˈɪnjəɹd",        # GRIN-yard
    "Kawah": "kˈɑwɑ", "Ijen": "ˈiʤɛn",  # KAH-wah EE-jen
    "Soufrière": "sˌufɹiˈɛɹ",       # soo-free-AIR
    "Montserrat": "mˌɑntsəɹˈæt",     # mont-se-RAT
    "Centralia": "sɛntɹˈAliə",      # sen-TRAY-lee-a
    "Wittenoom": "wˈɪtᵊnˌum",       # WIT-e-noom
    "Pilbara": "pˈɪlbəɹə",          # PIL-ba-ra
    "Karachay": "kˌɑɹəʧˈI",         # ka-ra-CHAI
    "Mayak": "mɑjˈɑk",              # ma-YAHK
    "Nyos": "nˈiOs",                # NEE-ohs
    "Kivu": "kˈivu",                # KEE-voo
    "Nyiragongo": "nˌɪɹəɡˈɑŋɡO",    # neer-a-GONG-go
    "Ural": "jˈʊɹəl", "Guinness": "ɡˈɪnɪs",
}
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
        f.write("Forbidden Earth - video01 - full.mp3 (Kokoro am_michael, speed 0.95)\n")
        f.write("section          start        end          length\n")
        for n, a, b in timings:
            f.write(f"{n:<16} {fmt(a)}  {fmt(b)}  {b-a:7.3f}s\n")
        f.write(f"\nTOTAL            {fmt(t)}  ({t:.3f}s)\n")
    print(open(os.path.join(out, "timings.txt")).read())

if __name__ == "__main__":
    main()
