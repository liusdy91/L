"""Regrabar las sílabas con vocal CORTA (بَ بِ بُ…).
La voz lee una sílaba suelta como el nombre de la letra, así que se sintetiza con la vocal larga
(بَا، بِي، بُو) a velocidad normal y se recorta: se conserva la consonante completa y solo los
primeros ~0,13 s de la vocal, con un final suave. Uso: syll.py modelo.onnx carpeta_audios"""
import sys, json, wave, os, subprocess, hashlib, array
from piper import PiperVoice, SynthesisConfig

voice = PiperVoice.load(sys.argv[1]); out = sys.argv[2]
idx_path = os.path.join(out, "index.json"); index = json.load(open(idx_path, encoding="utf-8"))
LONG = {"َ": "ا", "ِ": "ي", "ُ": "و"}
VOWEL_KEEP, FADE = 0.14, 0.05

def rms_frames(samples, sr, win=0.01):
    n = int(sr * win); out = []
    for i in range(0, len(samples) - n, n):
        seg = samples[i:i + n]; out.append((sum(x * x for x in seg) / n) ** .5)
    return out, win

changed = 0
for text in list(index):
    if len(text) != 2 or text[1] not in LONG: continue
    tmp = os.path.join(out, "syl.wav")
    with wave.open(tmp, "wb") as wf:
        voice.synthesize_wav(text + LONG[text[1]], wf, syn_config=SynthesisConfig(length_scale=1.0))
    with wave.open(tmp, "rb") as wf:
        sr = wf.getframerate(); samples = array.array("h", wf.readframes(wf.getnframes()))
    env, win = rms_frames(samples, sr)
    peak = max(env)
    start = next(i for i, e in enumerate(env) if e > peak * 0.06) * win          # comienzo de la consonante
    onset = next(i for i, e in enumerate(env) if e > peak * 0.75) * win          # comienzo de la vocal (75 % del máximo)
    begin = max(0, start - 0.03); end = onset + VOWEL_KEEP
    name = hashlib.sha1(("corta|" + text).encode("utf-8")).hexdigest()[:12] + ".mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af",
                    f"atrim={begin:.3f}:{end:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={end - begin - FADE:.3f}:d={FADE},apad=pad_dur=0.12",
                    "-ac", "1", "-ar", "22050", "-b:a", "48k", os.path.join(out, name)], check=True)
    old = index[text]
    if old != name and os.path.exists(os.path.join(out, old)): os.remove(os.path.join(out, old))
    index[text] = name; changed += 1
    print(text, f"consonante {start:.2f}s · vocal {onset:.2f}s · recorte {end - begin:.2f}s")
os.remove(os.path.join(out, "syl.wav"))
json.dump(index, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(changed, "sílabas regrabadas")
