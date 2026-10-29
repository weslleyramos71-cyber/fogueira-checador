"""Paso 4 — análisis por cuadro: silueta de la persona (Robust Video Matting), ropa / cabello+gorra (MediaPipe
multiclass) y puntos de la mano (MediaPipe hand landmarker). Tarda de 3 a 10 min por minuto de video.
Uso: python scripts/analyze.py CARPETA_PROYECTO
Escribe masks.mkv (R=persona, G=ropa, B=cabello/gorra) y hands.json."""
import sys, os, json, subprocess
import numpy as np, onnxruntime as ort
import mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision

proj = sys.argv[1]
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
info = json.load(open(f"{proj}/info.json")); W, H = info["width"], info["height"]

rvm = ort.InferenceSession(f"{KIT}/models/rvm_mobilenetv3_fp32.onnx", providers=["CPUExecutionProvider"])
rec = [np.zeros([1, 1, 1, 1], np.float32)] * 4
dsr = np.array([0.4], np.float32)
seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
    base_options=mpt.BaseOptions(model_asset_path=f"{KIT}/models/selfie_multiclass_256x256.tflite"),
    running_mode=vision.RunningMode.VIDEO, output_category_mask=False, output_confidence_masks=True))
hands = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
    base_options=mpt.BaseOptions(model_asset_path=f"{KIT}/models/hand_landmarker.task"),
    running_mode=vision.RunningMode.VIDEO, num_hands=2, min_hand_detection_confidence=0.4))

dec = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-i", f"{proj}/norm.mp4", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30",
                        "-i", "-", "-c:v", "libx264rgb", "-crf", "4", "-preset", "fast", f"{proj}/masks.mkv"], stdin=subprocess.PIPE)
log, n = [], 0
total = int(info["duration"] * 30)
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    src = (fr.astype(np.float32) / 255).transpose(2, 0, 1)[None]
    fgr, pha, *rec = rvm.run(None, {"src": src, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3], "downsample_ratio": dsr})
    img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(fr)); ts = int(n * 1000 / 30)
    cm = seg.segment_for_video(img, ts).confidence_masks
    clothes = (cm[4].numpy_view() * 255).astype(np.uint8)
    acc = (np.maximum(cm[1].numpy_view(), cm[5].numpy_view()) * 255).astype(np.uint8)
    hr = hands.detect_for_video(img, ts)
    log.append([{"side": hd[0].category_name, "pts": [[round(p.x, 4), round(p.y, 4)] for p in lm]} for lm, hd in zip(hr.hand_landmarks, hr.handedness)])
    enc.stdin.write(np.dstack([(pha[0, 0] * 255).astype(np.uint8), clothes, acc]).tobytes())
    n += 1
    if n % 150 == 0: print(f"   {n}/{total} cuadros", flush=True)
enc.stdin.close(); enc.wait()
seg.close(); hands.close()
json.dump(log, open(f"{proj}/hands.json", "w"))
print(f"OK  {n} cuadros analizados -> {proj}/masks.mkv, {proj}/hands.json  (manos detectadas en {sum(1 for x in log if x)} cuadros)")
