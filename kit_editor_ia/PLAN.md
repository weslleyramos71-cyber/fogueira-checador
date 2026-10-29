# plan.json — referencia

`plan.json` vive en la carpeta del proyecto y controla todo el render. Todos los tiempos están en segundos del video original. Los colores son `[R, G, B]`.

```json
{
  "layout": {
    "accent": [255, 106, 26],
    "punch_in": [[26.7, 29.3]],
    "focus_y": 0.42
  },
  "effects": {
    "audio_clean": true,
    "background": {"start": 17.6},
    "chair": {"start": 23.1},
    "recolor": [
      {"part": "clothes", "start": 25.9, "color": [36, 84, 196]},
      {"part": "hair_acc", "start": 52.1, "color": [38, 122, 66]}
    ],
    "hand_logos": [
      {"start": 41.2, "end": 44.5, "logo": "chatgpt", "glow": [90, 255, 200]},
      {"start": 47.5, "end": 50.3, "logo": "mi_logo.png"}
    ]
  },
  "panel": [
    {"type": "label", "start": 0, "end": 70, "text": "● Editado con IA"},
    {"type": "big", "start": 0, "end": 3, "a": "ESTE VIDEO", "b": "FUE EDITADO", "y": 300, "size": 140}
  ],
  "full_overlay": [
    {"type": "big", "start": 26.9, "end": 29.2, "a": "CAMISA", "b": "AZUL", "y": 330, "size": 150, "color_b": [52, 120, 255]}
  ]
}
```

## layout

| Clave | Para qué sirve |
|---|---|
| `accent` | Color de acento de todo el diseño. |
| `punch_in` | Tramos `[inicio, fin]` en los que la persona pasa a pantalla completa. Úsalos justo cuando se muestra un efecto. Duran de 2 a 3 s y no deben ser más de 3 por minuto. |
| `focus_y` | Altura del recorte de la persona en la tarjeta, de 0 a 1. Súbelo (0.5) si se le corta la barbilla y bájalo (0.35) si se le corta la cabeza. |

## effects (todos son opcionales)

| Clave | Qué hace |
|---|---|
| `audio_clean` | Filtro de graves, reducción de ruido y respiración, compresión y normalización a −14 LUFS. |
| `background` | Cambia el fondo a partir de `start`, con un barrido de luz. Sin más datos usa el cuarto gamer con LED. Con `"image": "fondo.jpg"` usa una foto tuya (ruta relativa al proyecto) y `"blur": 3` controla el desenfoque. |
| `chair` | Silla gamer detrás de la persona. Solo funciona junto con `background`. |
| `recolor` | Tiñe `"clothes"` (ropa) o `"hair_acc"` (cabello, gorra o accesorios) al color indicado desde `start`, conservando textura y sombras. Funciona mejor en ropa oscura o lisa. |
| `hand_logos` | Logo girando en 3D sobre la palma. `logo` acepta `"claude"`, `"chatgpt"` o la ruta a un PNG cuadrado con fondo transparente. La palma debe verse abierta y hacia arriba en ese tramo. |

## panel (parte superior) y full_overlay (encima del video en pantalla completa)

Cada elemento es `{"type": ..., "start": s, "end": s, ...}`. Todos los textos van en el idioma del video. Las alturas `y` están en píxeles de un lienzo de 1080×1920. El panel ocupa la franja de y=0 a y=740: no pongas nada más abajo.

| type | Campos | Uso |
|---|---|---|
| `label` | `text`, `x`, `y` | Etiqueta pequeña fija, por ejemplo "● Editado con IA". |
| `big` | `a`, `b`, `y`, `size`, `color_a`, `color_b` | Palabra gigante. `a` va en crema y `b` en el color de acento. Sube desde una máscara. |
| `chips` | `items: [[texto, inicio], ...]`, `y` | De 1 a 3 etiquetas que aparecen en su momento. |
| `check` | `a`, `b` | Palomita grande que aparece de golpe y, debajo, una palabra gigante opcional. |
| `swatch` | `label`, `from`, `to`, `at`, `word` | Cambio de color: círculo de antes → flecha → círculo de después. |
| `audio` | `title`, `tags: [[texto, t], ...]`, `clean_at`, `clean_word`, `toggle`, `toggle_at` | Onda de audio que pasa de ruidosa a limpia, tachando etiquetas, con un interruptor opcional (por ejemplo "Subtítulos"). |
| `checklist` | `title`, `items: [...]` | Hasta 6 elementos palomeados en 2 columnas. |
| `chat` | `assistant`, `user`, `reply`, `reply_at` | Chat de IA: la petición se escribe sola y llega la respuesta. |
| `before_after` | `before`, `after`, `before_label`, `after_label`, `after_at` | Dos tarjetas: antes → después. |
| `follow` | `handle`, `bio`, `button`, `done`, `tap_at` | Tarjeta de perfil con un botón "Seguir" que se presiona. |

**Reglas de diseño:**

- Un solo elemento grande a la vez en el panel; no encimes elementos en el mismo tramo.
- Cada elemento entra en la palabra que lo motiva y dura al menos 1.5 s.
- En las palabras gigantes, `size` va de 110 a 190. Las frases largas usan un tamaño menor; el render reduce el tamaño automáticamente si no caben.
- Elementos `big` en dos líneas: usa dos elementos con `y` distintas, separadas de 150 a 200 px.

## captions.json

Lo genera `scripts/captions.py`; se puede editar a mano. Es una lista de `[inicio, "texto"]`, y cada subtítulo dura hasta que empieza el siguiente (máximo 1.3 s). Marcadores de color:

- `*palabra*` → color de acento
- `#palabra#` → azul
- `%palabra%` → verde
