# Kit Editor IA — reels profesionales con Claude Code

Convierte un video vertical grabado con el celular en un reel profesional:

- **Diseño:** panel superior con gráficos animados sincronizados con lo que dices y tú en una tarjeta redondeada, con acercamientos a pantalla completa.
- **Subtítulos:** palabra por palabra, con las palabras clave a color.
- **Imagen y audio:** audio limpio y normalizado, mejora de color y nitidez (superresolución x2).
- **Efectos opcionales:**
  - cambio de fondo (cuarto gamer o tu propia foto);
  - silla gamer;
  - cambio de color de ropa o gorra;
  - logos 3D girando sobre tu mano.

## Requisitos

- **Claude Code** con un plan de pago (Pro o Max). Una edición consume bastante uso; con un plan bajo puede que la sesión se detenga a medias.
- **Computadora** con macOS o Linux. En Windows, usa WSL (Ubuntu).
- **ffmpeg y Python 3.10 o mayor.** `setup.sh` intenta instalar ffmpeg si falta.
- **Internet** la primera vez (≈ 700 MB de modelos) y **≈ 3 GB libres** en disco.
- **Tiempo:** de 20 a 40 minutos de procesamiento por cada minuto de video (sin GPU).

## Cómo usarlo

1. Descomprime el kit y abre la carpeta en Claude Code (`cd kit_editor_ia && claude`).
2. Copia tu video dentro de la carpeta.
3. Pega el prompt de `PROMPT.md` y llena los datos de tu video.
4. Contesta cuando Claude te muestre la transcripción y el plan; después espera el render.

## Para que salga bien

- **Grabación:** vertical, de frente, de la cintura hacia arriba, con buena luz frontal (sin ventana detrás) y voz clara.
- **Pide los efectos en voz alta** y deja de 2 a 3 s de pausa después: "quiero que esta camisa quede azul… (pausa)".
- **Ropa:** lisa y oscura si vas a pedir un cambio de color.
- **Logos en la mano:** muestra la palma abierta hacia arriba, a la altura del pecho, durante 3–4 s.

## Limitaciones (léelas)

- El cuarto gamer y la silla son gráficos generados por código: se ven bien, pero no son fotorrealistas.
- En movimientos muy rápidos de manos puede haber pequeños defectos en el contorno.
- Los logos `claude` y `chatgpt` del kit son aproximaciones dibujadas; para usar un logo exacto, pon tu PNG.
- El resultado depende del video; puede requerir 1 o 2 rondas de ajustes con Claude.

## Archivos

| Archivo | Qué es |
|---|---|
| `setup.sh` | Instala librerías, modelos y tipografías. |
| `scripts/prepare.py` | Normaliza el video y extrae el audio. |
| `scripts/transcribe.py` | Transcripción con tiempos por palabra. |
| `scripts/captions.py` | Arma los subtítulos. |
| `scripts/analyze.py` | Máscaras de la persona, la ropa y la gorra, y seguimiento de la mano. |
| `scripts/render.py` | Render según `plan.json` (con `--preview` para capturas rápidas). |
| `scripts/fx.py` | Efectos: fondo, silla, color, logos 3D y reiluminación. |
| `PLAN.md` | Todas las opciones de `plan.json`. |
| `PROMPT.md` | El prompt para Claude Code. |

Modelos de terceros que descarga `setup.sh`, con su propia licencia:

- Robust Video Matting (GPL-3.0)
- MediaPipe (Apache-2.0)
- Parakeet TDT v3 vía sherpa-onnx (CC-BY-4.0)
- FSRCNN (MIT)
- Tipografías de Google Fonts (OFL)

Si vas a revender el kit, revisa esas licencias.
