"""Build Forbidden Earth video03 narration with Kokoro (am_michael, speed 0.95).

Usage: python voice_build.py script_original.txt out_dir [--check]
"""
import os, re, subprocess, sys

SR = 24000
VOICE, SPEED = "am_michael", 0.95
PARA_GAP, SECTION_GAP = 0.4, 0.8

# 1) Numbers, years, units, symbols -> words. Every numeric token must be listed here.
NUM = {
    "64": "sixty-four", "200,000": "two hundred thousand", "20": "twenty", "1964": "nineteen sixty-four",
    "2016": "twenty sixteen", "17": "seventeen", "1864": "eighteen sixty-four", "70": "seventy",
    "160": "one hundred and sixty", "1963": "nineteen sixty-three", "40": "forty", "1965": "nineteen sixty-five",
    "90": "ninety", "1940": "nineteen forty", "17,000": "seventeen thousand", "1948": "nineteen forty-eight",
    "1960s": "nineteen-sixties", "1,500": "one thousand five hundred", "125": "one hundred and twenty-five",
    "1,300": "one thousand three hundred", "690": "six hundred and ninety", "2033": "twenty thirty-three",
    "35": "thirty-five", "11,000": "eleven thousand", "43": "forty-three", "2000": "two thousand",
    "300": "three hundred", "11": "eleven", "58": "fifty-eight", "2015": "twenty fifteen",
    "6,638": "six thousand six hundred and thirty-eight", "1974": "nineteen seventy-four", "8,000": "eight thousand",
    "210": "two hundred and ten", "2,000": "two thousand", "700,000": "seven hundred thousand",
}
# abbreviations and symbols (applied before numbers)
PRE = [("$10,000", "ten thousand dollars"), ("US Bureau", "U S Bureau"), (" BC", " B C")]
TOKEN = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?(?:st|nd|rd|th|s)?\b")

# 2) Pronunciation fixes (misaki/Kokoro phonemes, US).
PHON = {
    "Kauai": "kɑwˈɑi", "Kamehameha": "kəmˌAhəmˈAhə", "Sinclair": "sˈɪnklɛɹ", "Surtr": "sˈɜɹtəɹ",
    "Naiku": "nˈIku", "Amaterasu": "ˌɑmɑtɛɹˈɑsu", "Ilha": "ˈiljə", "da": "dɑ", "Queimada": "kAmˈɑdə",
    "Grande": "ɡɹˈɑnʤi", "São": "sˈW", "Paulo": "pˈWlO", "Naica": "nˈIkə", "Kailash": "kIlˈɑʃ",
    "Bön": "bˈɜn", "Meru": "mˈAɹu", "Shi": "ʃˈɜɹ", "Huang": "hwˈɑŋ", "Xi'an": "ʃiˈɑn",
    "Sima": "səmˈɑ", "Qian": "ʧjˈɛn", "Yangtze": "jˈæŋsi", "Robinson": "ɹˈɑbɪnsən",
    "lancehead": "lˈænshˌɛd", "Terracotta": "tˌɛɹəkˈɑtə", "dives": "dˈIvz",
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
        f.write("Forbidden Earth - video03 - full.mp3 (Kokoro am_michael, speed 0.95)\n")
        f.write("section          start        end          length\n")
        for n, a, b in timings:
            f.write(f"{n:<16} {fmt(a)}  {fmt(b)}  {b-a:7.3f}s\n")
        f.write(f"\nTOTAL            {fmt(t)}  ({t:.3f}s)\n")
    print(open(os.path.join(out, "timings.txt")).read())

if __name__ == "__main__":
    main()
