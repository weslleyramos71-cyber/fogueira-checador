"""Paso 1 — normaliza el video (rotación del celular, 30 fps, vertical) y extrae el audio.
Uso: python scripts/prepare.py VIDEO.mp4 CARPETA_PROYECTO"""
import sys, os, json, subprocess

src, proj = sys.argv[1], sys.argv[2]
os.makedirs(proj, exist_ok=True)
probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:stream_side_data=rotation",
                                   "-of", "json", src], capture_output=True, text=True, check=True).stdout)["streams"][0]
w, h = probe["width"], probe["height"]
rot = abs(int(next((s.get("rotation", 0) for s in probe.get("side_data_list", [])), 0)))
if rot in (90, 270): w, h = h, w
# keep the working resolution modest (the render upscales with super-resolution); width 576 for 9:16
tw = 576 if w <= h else 1024
th = int(round(h * tw / w / 2)) * 2
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", src, "-vf", f"fps=30,scale={tw}:{th}:flags=lanczos",
                "-c:v", "libx264", "-crf", "14", "-preset", "fast", "-an", f"{proj}/norm.mp4"], check=True)
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", f"{proj}/audio16k.wav"], check=True)
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", src, "-vn", "-c:a", "pcm_s16le", "-ar", "48000", f"{proj}/audio_orig.wav"], check=True)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{proj}/norm.mp4"], capture_output=True, text=True).stdout)
json.dump({"source": os.path.abspath(src), "width": tw, "height": th, "duration": dur}, open(f"{proj}/info.json", "w"), indent=2)
print(f"OK  {proj}/norm.mp4  {tw}x{th}  {dur:.1f}s")
if tw > th:
    print("AVISO: el video es horizontal; el kit está pensado para video vertical 9:16.")
