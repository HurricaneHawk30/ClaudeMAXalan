"""Build Forbidden Earth video04 narration with Kokoro (am_michael, speed 0.95).

Usage: python voice_build.py script_original.txt out_dir [--check]
"""
import os, re, subprocess, sys

SR = 24000
VOICE, SPEED = "am_michael", 0.95
PARA_GAP, SECTION_GAP = 0.4, 0.8

# 1) Numbers, years, units, symbols -> words. Every numeric token must be listed here.
NUM = {
    "4,000": "four thousand", "11,873": "eleven thousand eight hundred and seventy-three", "2022": "twenty twenty-two",
    "300": "three hundred", "16": "sixteen", "233": "two hundred and thirty-three", "10th": "tenth",
    "1913": "nineteen thirteen", "134": "one hundred and thirty-four", "57": "fifty-seven", "1972": "nineteen seventy-two",
    "201": "two hundred and one", "86": "eighty-six", "2001": "two thousand and one", "100": "one hundred",
    "38": "thirty-eight", "154": "one hundred and fifty-four", "66": "sixty-six", "5,000": "five thousand",
    "2000s": "two thousands", "6th": "sixth", "1933": "nineteen thirty-three", "68": "sixty-eight", "90": "ninety",
    "52": "fifty-two", "2,400": "two thousand four hundred", "2,800": "two thousand eight hundred",
    "250": "two hundred and fifty", "1961": "nineteen sixty-one", "1970": "nineteen seventy", "1989": "nineteen eighty-nine",
    "12,262": "twelve thousand two hundred and sixty-two", "23": "twenty-three", "180": "one hundred and eighty",
    "24": "twenty-four", "10,935": "ten thousand nine hundred and thirty-five", "1,000": "one thousand",
    "23rd": "twenty-third", "1960": "nineteen sixty", "9,000": "nine thousand", "20": "twenty", "2012": "twenty twelve",
    "1992": "nineteen ninety-two", "2,688": "two thousand six hundred and eighty-eight", "400": "four hundred",
    "2030s": "twenty-thirties",
}
# abbreviations (applied before numbers)
PRE = [("US Navy", "U S Navy")]
TOKEN = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?(?:st|nd|rd|th|s)?\b")

# 2) Pronunciation fixes (misaki/Kokoro phonemes, US).
PHON = {
    "Mawsynram": "mˈɔsɪnɹˌʌm", "Meghalaya": "mAɡˈɑlAə", "knup": "nˈʌp", "Maracaibo": "mˌɑɹɑkˈIbO",
    "Catatumbo": "kˌɑtɑtˈumbO", "Atacama": "ˌɑtɑkˈɑmə", "ALMA": "ˈɑlmə", "Rinconada": "ɹˌinkOnˈɑdə",
    "Bella": "bˈAjə", "Durmiente": "dˌʊɹmiˈɛntA", "cachorreo": "kˌɑʧOɹˈAO", "Oymyakon": "ˌYmjɑkˈɑn",
    "Yakutsk": "jɑkˈutsk", "Cunha": "kˈunjə", "Helena": "həlˈinə", "Kola": "kˈOlə", "Mariana": "mˌɑɹiˈɑnə",
    "Piccard": "pikˈɑɹ", "Hrvoje": "hˈɜɹvOjɛ", "Lukatela": "lˌukɑtˈɛlə", "Nemo": "nˈimO", "nemo": "nˈimO",
    "Jules": "ʤˈulz", "Verne": "vˈɜɹn", "Mir": "mˈiɹ", "Badwater": "bˈædwˌɔtəɹ", "Guinness": "ɡˈɪnɪs",
    "Cameron": "kˈæməɹən", "Walsh": "wˈɔlʃ", "Jacques": "ʒˈɑk",
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
        f.write("Forbidden Earth - video04 - full.mp3 (Kokoro am_michael, speed 0.95)\n")
        f.write("section          start        end          length\n")
        for n, a, b in timings:
            f.write(f"{n:<16} {fmt(a)}  {fmt(b)}  {b-a:7.3f}s\n")
        f.write(f"\nTOTAL            {fmt(t)}  ({t:.3f}s)\n")
    print(open(os.path.join(out, "timings.txt")).read())

if __name__ == "__main__":
    main()
