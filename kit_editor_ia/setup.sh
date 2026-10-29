#!/usr/bin/env bash
# Instala todo lo que necesita el kit: librerías de Python, modelos de IA y tipografías.
# Uso:  bash setup.sh
set -euo pipefail
cd "$(dirname "$0")"
KIT="$(pwd)"
mkdir -p models fonts

say() { printf '\n==> %s\n' "$*"; }

say "Comprobando ffmpeg"
if ! command -v ffmpeg >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then sudo apt-get update -q && sudo apt-get install -y -q ffmpeg || apt-get install -y -q ffmpeg
  elif command -v brew >/dev/null 2>&1; then brew install ffmpeg
  else echo "Instala ffmpeg (https://ffmpeg.org) y vuelve a ejecutar este script."; exit 1; fi
fi

# MediaPipe en Linux necesita las librerías gráficas EGL/GLES aunque no haya pantalla
if [ "$(uname)" = "Linux" ] && command -v apt-get >/dev/null 2>&1; then
  if ! ldconfig -p 2>/dev/null | grep -q libEGL.so.1; then
    say "Instalando librerías EGL para MediaPipe"
    (sudo apt-get install -y -q libegl1 libgles2 libgl1 || apt-get install -y -q libegl1 libgles2 libgl1) >/dev/null
  fi
fi

say "Creando entorno de Python (.venv)"
PY=python3
$PY -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q numpy pillow soundfile onnxruntime sherpa-onnx mediapipe opencv-contrib-python-headless

dl() {  # dl URL destino
  [ -s "$2" ] && return 0
  echo "   descargando $(basename "$2")"
  curl -fsSL --retry 3 -o "$2.part" "$1" && mv "$2.part" "$2"
}

say "Descargando modelos de IA"
dl https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx models/rvm_mobilenetv3_fp32.onnx
dl https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task models/hand_landmarker.task
dl https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite models/selfie_multiclass_256x256.tflite
dl https://raw.githubusercontent.com/Saafke/FSRCNN_Tensorflow/master/models/FSRCNN_x2.pb models/FSRCNN_x2.pb
if [ ! -d models/parakeet ]; then
  echo "   descargando el modelo de transcripción (≈ 650 MB, puede tardar)"
  curl -fsSL --retry 3 https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2 | tar xj -C models
  mv models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8 models/parakeet
fi

say "Descargando tipografías (Google Fonts, licencia OFL)"
G=https://raw.githubusercontent.com/google/fonts/main/ofl
dl "$G/anton/Anton-Regular.ttf" fonts/Anton-Regular.ttf
dl "$G/montserrat/Montserrat%5Bwght%5D.ttf" fonts/Montserrat-VF.ttf
dl "$G/inter/Inter%5Bopsz%2Cwght%5D.ttf" fonts/Inter-VF.ttf

say "Prueba rápida"
.venv/bin/python -c "import numpy, PIL, cv2, onnxruntime, sherpa_onnx, mediapipe; print('   librerías OK')"
for f in models/rvm_mobilenetv3_fp32.onnx models/hand_landmarker.task models/selfie_multiclass_256x256.tflite models/FSRCNN_x2.pb models/parakeet/tokens.txt fonts/Anton-Regular.ttf fonts/Montserrat-VF.ttf fonts/Inter-VF.ttf; do
  [ -s "$f" ] || { echo "FALTA: $f"; exit 1; }
done
echo "   modelos y tipografías OK"
say "Listo. Siguiente paso: .venv/bin/python scripts/prepare.py TU_VIDEO.mp4 proyecto"
