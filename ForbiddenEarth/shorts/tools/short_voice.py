"""Narration for Forbidden Earth Shorts (Kokoro am_michael).

python short_voice.py NN [--speed 0.95] [--check]
Text: shorts/scripts.md, block "Текст:" of shortNN. Dictionaries (numbers, phonemes) come from the
source video's voice_build.py (tools/vb_videoNN.py) plus the extra years below.
Output: shorts/shortNN/voice/voice.wav, voice.mp3, text_tts.txt, length.txt
"""
import importlib.util, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SR, VOICE, PARA_GAP = 24000, "am_michael", 0.4
EXTRA_NUM = {"1725": "seventeen twenty-five", "1962": "nineteen sixty-two", "1963": "nineteen sixty-three",
             "1980": "nineteen eighty", "2001": "two thousand one", "2020": "twenty twenty", "2030s": "twenty thirties"}
EXTRA_PRE = [("a pH of", "a P H of")]
EXTRA_PHON = {"Mir": "mˈɪɹ", "Queimada": "kAmˈɑdə", "Ilha": "ˈiljə", "lancehead": "lˈænshˌɛd", "Dallol": "dəlˈOl",
              "Centralia": "sɛntɹˈAliə", "Derinkuyu": "dˌɛɹɪŋkujˈu", "Nemo": "nˈimO", "nemo": "nˈimO"}

def text_of(nn):
    md = open(os.path.join(ROOT, "scripts.md"), encoding="utf-8").read()
    sec = md.split(f"## short{nn}")[1].split("\n## ")[0]
    return sec.split("Текст:")[1].split("```")[1].strip()

def main():
    nn = sys.argv[1]; speed = float(sys.argv[sys.argv.index("--speed") + 1]) if "--speed" in sys.argv else 0.95
    src = {"01": "01", "02": "02", "03": "03", "04": "04", "05": "05", "06": "06"}[nn]
    spec = importlib.util.spec_from_file_location("vb", os.path.join(HERE, f"vb_video{src}.py"))
    vb = importlib.util.module_from_spec(spec); spec.loader.exec_module(vb)
    vb.NUM.update(EXTRA_NUM)
    for k, v in EXTRA_PHON.items(): vb.PHON.setdefault(k, v)
    vb.NAME = re.compile(r"\b(" + "|".join(sorted(vb.PHON, key=len, reverse=True)) + r")\b")
    paras = [p.strip() for p in text_of(nn).split("\n\n") if p.strip()]
    def pre(p):
        for a, b in EXTRA_PRE: p = p.replace(a, b)
        return p
    tts = [vb.normalize(pre(" ".join(p.split()))) for p in paras]
    out = os.path.join(ROOT, f"short{nn}", "voice"); os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "text_tts.txt"), "w", encoding="utf-8").write("\n\n".join(tts) + "\n")
    from kokoro import KPipeline
    import numpy as np, soundfile as sf
    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    if "--check" in sys.argv:
        for p in tts:
            _, toks = pipe.g2p(p)
            bad = [t.text for t in toks if not t.phonemes or "❓" in (t.phonemes or "")]
            if bad: print("UNKNOWN:", bad)
        print("checked"); return
    parts = []
    for j, p in enumerate(tts):
        if j: parts.append(np.zeros(int(PARA_GAP * SR), dtype=np.float32))
        parts += [r.audio.numpy() for r in pipe(p, voice=VOICE, speed=speed, split_pattern=None)]
    a = np.concatenate(parts).astype(np.float32)
    wav = os.path.join(out, "voice.wav"); sf.write(wav, a, SR)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ar", "44100", "-b:a", "192k", os.path.join(out, "voice.mp3")], check=True)
    open(os.path.join(out, "length.txt"), "w").write(f"{len(a)/SR:.3f} speed={speed}\n")
    print(f"short{nn}: {len(a)/SR:.2f}s at speed {speed}")

if __name__ == "__main__":
    main()
