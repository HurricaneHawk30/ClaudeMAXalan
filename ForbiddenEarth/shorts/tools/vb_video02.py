"""Build Forbidden Earth video02 narration with Kokoro (am_michael, speed 0.95).

Usage: python voice_build.py script_original.txt out_dir [--check]
"""
import os, re, subprocess, sys

SR = 24000
VOICE, SPEED = "am_michael", 0.95
PARA_GAP, SECTION_GAP = 0.4, 0.8

# 1) Numbers, years, units, symbols -> words. Every numeric token must be listed here.
NUM = {
    "1850": "eighteen fifty", "5,000": "five thousand", "2,500": "two thousand five hundred",
    "18th": "eighteenth", "1888": "eighteen eighty-eight", "800": "eight hundred", "150": "one hundred and fifty",
    "23": "twenty-three", "100": "one hundred", "1300": "thirteen hundred", "600": "six hundred",
    "1963": "nineteen sixty-three", "85": "eighty-five", "18": "eighteen", "20,000": "twenty thousand",
    "50": "fifty", "8th": "eighth", "19th": "nineteenth", "4,000": "four thousand", "1922": "nineteen twenty-two",
    "1924": "nineteen twenty-four", "4,500": "four thousand five hundred", "1812": "eighteen twelve",
    "22nd": "twenty-second", "79": "seventy-nine", "1590s": "fifteen-nineties", "1748": "seventeen forty-eight",
    "24th": "twenty-fourth", "1911": "nineteen eleven", "1902": "nineteen oh-two", "1400s": "fourteen hundreds",
    "1984": "nineteen eighty-four", "1992": "nineteen ninety-two", "2024": "twenty twenty-four",
    "2013": "twenty thirteen", "6,600": "six thousand six hundred", "2,000": "two thousand",
    "1800s": "eighteen hundreds", "1870": "eighteen seventy", "160": "one hundred and sixty",
    "1873": "eighteen seventy-three", "1,000": "one thousand", "360": "three hundred and sixty",
    "9,000": "nine thousand", "1669": "sixteen sixty-nine", "1882": "eighteen eighty-two", "1600": "sixteen hundred",
}
# abbreviations read letter by letter (applied before numbers)
PRE = [("R. D. Banerji", "R D Banerji"), ("T. E. Lawrence", "T E Lawrence"), ("A. Lizárraga", "A Lizárraga"),
       ("U.S. congressman", "U S congressman"), ("PhD", "P H D"), (" BC", " B C"), ("Mohenjo-daro", "Mohenjo daro")]
TOKEN = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?(?:st|nd|rd|th|s)?\b")

# 2) Pronunciation fixes (misaki/Kokoro phonemes, US).
PHON = {
    "Skara": "skˈɑɹə", "Orkney": "ˈɔɹkni", "Verde": "vˈɜɹdi", "Puebloan": "pwˈɛblOən",
    "Derinkuyu": "dˌɛɹɪnkˈuju", "Mohenjo": "mOhˈɛnʤO", "daro": "dˈɑɹO", "Banerji": "bˈænəɹʤi",
    "Burckhardt": "bˈɜɹkhɑɹt", "Domenico": "dəmˈɛnikO", "Fontana": "fɑntˈɑnə", "Sarno": "sˈɑɹnO",
    "Machu": "mˈɑʧu", "Picchu": "pˈikʧu", "Urubamba": "ˌuɹubˈɑmbə", "Arteaga": "ˌɑɹtAˈɑɡə",
    "Lizárraga": "lisˈɑɹəɡə", "Pachacuti": "pˌɑʧəkˈuti", "Ubar": "ˈubɑɹ", "Iram": "ˈiɹɑm", "Shisr": "ʃˈɪsəɹ",
    "Tulane": "tulˈAn", "Campeche": "kæmpˈɛʧA", "Valeriana": "vəlˌɛɹiˈɑnə", "Hisarlik": "hˌɪsɑɹlˈɪk",
    "Schliemann": "ʃlˈimɑn", "Pushkin": "pˈʊʃkɪn", "Timaeus": "tIˈmiəs", "Critias": "kɹˈɪtiəs",
    "Athanasius": "ˌæθənˈAʃəs", "Kircher": "kˈiɹkəɹ", "Akrotiri": "ˌækɹOtˈɪɹi", "Minoan": "mɪnˈOən",
    "Wetherill": "wˈɛðəɹɪl", "Calvert": "kˈælvəɹt", "Clapp": "klˈæp", "Ibrahim": "ˈɪbɹəhˌim",
    "Johann": "jˈOhɑn", "ballcourt": "bˈɔlkˌɔɹt", "Donnelly": "dˈɑnəli", "Ignatius": "ɪɡnˈAʃəs",
    "Hiram": "hˈIɹəm", "Bingham": "bˈɪŋəm", "Melchor": "mˈɛlkɔɹ",
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
        f.write("Forbidden Earth - video02 - full.mp3 (Kokoro am_michael, speed 0.95)\n")
        f.write("section          start        end          length\n")
        for n, a, b in timings:
            f.write(f"{n:<16} {fmt(a)}  {fmt(b)}  {b-a:7.3f}s\n")
        f.write(f"\nTOTAL            {fmt(t)}  ({t:.3f}s)\n")
    print(open(os.path.join(out, "timings.txt")).read())

if __name__ == "__main__":
    main()
