"""Paso 2 — transcribe con tiempos por palabra (Parakeet TDT v3, 25 idiomas europeos incl. español y portugués).
Uso: python scripts/transcribe.py CARPETA_PROYECTO
Escribe words.json ([inicio_en_segundos, palabra]) y muestra la transcripción."""
import sys, os, json
import numpy as np, soundfile as sf, sherpa_onnx

proj = sys.argv[1]
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = f"{KIT}/models/parakeet/"
rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=d + "encoder.int8.onnx", decoder=d + "decoder.int8.onnx",
        joiner=d + "joiner.int8.onnx", tokens=d + "tokens.txt", model_type="nemo_transducer", num_threads=os.cpu_count() or 4)
a, sr = sf.read(f"{proj}/audio16k.wav", dtype="float32")
words, step = [], 25
for st in range(0, int(len(a) / sr) + 1, step):
    seg = a[int(st * sr): int((st + step) * sr)]
    if len(seg) < sr * 0.5: break
    s = rec.create_stream(); s.accept_waveform(sr, seg); rec.decode_stream(s)
    for t, tok in zip(s.result.timestamps, s.result.tokens):
        if tok.startswith(" ") or not words or (t + st) - words[-1][0] > 1.5: words.append([round(t + st, 2), tok.strip()])
        else: words[-1][1] += tok
words = [w for w in words if w[1]]
json.dump(words, open(f"{proj}/words.json", "w"), ensure_ascii=False, indent=0)
print(" ".join(f"{t:.1f}:{w}" for t, w in words))
print(f"\nOK  {len(words)} palabras -> {proj}/words.json")
