# Prompt: edición de reel profesional con efectos de IA

Este prompt reproduce la edición de `video_editado_com_claude.mp4`:

- Pantalla dividida: un panel de gráficos animados arriba y la persona en una tarjeta redondeada abajo.
- Subtítulos palabra por palabra y palabras clave gigantes.
- Efectos que se aplican en el momento en que la persona los pide: cambio de escenario, silla gamer, cambio de color de la ropa, logos 3D flotando sobre la mano y audio limpio.

## Requisitos (léelos antes de usarlo)

- **Un agente que pueda ejecutar código**, no un chat normal. Funciona con Claude Code (terminal, app de escritorio o claude.ai/code), que ejecuta comandos, instala librerías y procesa el video. En un chat sin herramientas solo vas a recibir instrucciones, no el video.
- **Acceso a internet** desde el entorno del agente, para descargar los modelos:
  - Robust Video Matting (GitHub): separa a la persona del fondo.
  - MediaPipe (Google Storage): detecta ropa, cabello y mano.
  - Parakeet / Whisper vía sherpa-onnx (GitHub): transcribe con tiempos por palabra.
- **Tiempo:** de 20 a 40 minutos de procesamiento por cada minuto de video, en CPU.
- **Video de entrada:** vertical, con buena luz, la persona de frente y de la cintura hacia arriba, voz clara. Dentro del video la persona debe *decir* lo que quiere ("quiero que esta camisa quede azul"); el agente usa esos momentos para disparar cada efecto.
- **Limitaciones honestas:**
  - El escenario y la silla son gráficos generados por código: se ven bien, pero no son fotorrealistas.
  - Los cambios de color funcionan mejor en ropa oscura o lisa.
  - En los movimientos rápidos de manos puede haber pequeños defectos en el contorno.
  - Los logos de marcas se dibujan aproximados, salvo que entregues los PNG oficiales.

---

## Prompt (copiar desde aquí)

```
Eres mi editor de video. Edita el video adjunto como un reel vertical profesional (1080x1920, 30 fps).
Trabaja paso a paso, ejecutando código (Python + ffmpeg). No me entregues instrucciones: entrégame el MP4 terminado.

DATOS DE MI VIDEO
- Idioma: ____
- Marca / página / @: ____
- Color de acento: ____ (si no hay, usa naranja #FF6A1A)
- Logos oficiales en PNG (opcional): ____
- Nombres o cifras que deben salir bien escritos: ____

PASO 1 — PREPARAR
- Normaliza el video a 30 fps, respetando la rotación del celular. Aplica una reducción de ruido suave (hqdn3d) y deja el audio aparte.
- Si la resolución es menor a 1080 de ancho, aplica superresolución x2 (OpenCV dnn_superres con FSRCNN/EDSR, o similar) antes de componer.

PASO 2 — TRANSCRIBIR
- Transcribe con tiempos por palabra (sherpa-onnx con Parakeet TDT v3 multilingüe; usa Whisper para verificar el texto).
- Corrige nombres de productos (por ejemplo "Cloud" → "Claude", "chat GBT" → "ChatGPT"), quita tartamudeos y muletillas.
- Muéstrame la transcripción con sus tiempos antes de seguir.

PASO 3 — DETECTAR QUÉ EFECTOS PIDO
- Busca en la transcripción las frases donde pido un cambio: escenario, silla, color de ropa, objetos o logos en la mano, color de gorra o accesorios, limpiar el audio.
- Arma una línea de tiempo: cada efecto empieza justo en la palabra clave (por ejemplo "azul", "verde", "3D").
- Muéstrame esa línea de tiempo antes de editar.

PASO 4 — ANÁLISIS POR CUADRO
- Máscara de la persona con Robust Video Matting (rvm_mobilenetv3, ONNX), que es estable entre cuadros.
- Máscaras de ropa, cabello y accesorios con MediaPipe selfie_multiclass_256x256 (clase 4 = ropa; clases 1 + 5 = cabello/gorra).
- Puntos de la mano con MediaPipe hand_landmarker.
- Guarda las máscaras en un video aparte para no recalcularlas.

PASO 5 — EFECTOS
- Escenario nuevo: cuarto moderno estilo gamer (paneles acústicos, tiras LED violeta y cian, hexágonos de neón, bokeh), con desenfoque de profundidad. Entra con un barrido de luz en la palabra clave. Reilumina a la persona con luz de borde de los colores del cuarto y "light wrap" para que no se vea recortada; conserva el tono natural de la piel.
- Silla gamer: respaldo con alas y paneles de color detrás de los hombros, con sombreado de cuero; aparece con un fundido corto.
- Cambio de color de ropa o gorra: tiñe solo la máscara correspondiente, conservando la textura, las sombras y los brillos. Método:
  - Suaviza un poco la luminancia de la tela (para no amplificar los bloques de compresión).
  - Estírala entre su percentil 2 y 99.5.
  - Mapéala a una rampa del color nuevo, de oscuro (×0.34) a claro (×1.35).
  - Excluye estampados y logos claros, joyería saturada, cadenas (líneas finas más brillantes que su entorno) y piel.
  - Usa tonos naturales: azul rey (36, 84, 196), verde bosque (38, 122, 66).
  - Transición de barrido de arriba hacia abajo.
- Logos 3D en la mano: logo con grosor, giro tipo moneda, reflejo que se mueve, resplandor y sombra sobre la palma. Sigue la palma con suavizado y mantiene la posición si se pierde la mano. Entra con efecto de rebote y sale achicándose.
- Audio: filtro de graves (80 Hz), reducción de ruido y respiración (afftdn), compresión suave y normalización a −14 LUFS.

PASO 6 — DISEÑO (estilo reel explicativo)
- Fondo oscuro cálido (#100E0D) con manchas de luz suaves.
- Arriba (40%): panel de gráficos animados sincronizados con cada frase:
  - tarjetas tipo app (chat escribiendo la petición y la respuesta "Pronto ✓");
  - antes / después;
  - muestras de color con flecha;
  - onda de audio que pasa de ruidosa a limpia;
  - interruptor de "Legendas" que se enciende;
  - lista de todo lo que se hizo;
  - botón "Seguir" que se presiona.
- Palabras clave gigantes en fuente condensada (Anton), con entrada tipo máscara y una parte en el color de acento.
- Abajo (60%): la persona en una tarjeta con esquinas de 36 px y sombra.
- En el momento de mostrar un efecto (ropa o gorra nueva), acercamiento a pantalla completa de 2–3 s, con la palabra clave encima.
- Subtítulos: de 1 a 3 palabras a la vez, Montserrat ExtraBold blanca con contorno oscuro, con entrada con rebote. Las palabras de colores van en su color ("azul" en azul, "verde" en verde, la marca en el color de acento).
- Animaciones: entradas con easeOut de 0.3–0.6 s, salidas a la mitad de ese tiempo; un solo punto de atención a la vez.

PASO 7 — COLOR Y CALIDAD
- Corrección de color de la persona desde el primer cuadro: quita el tono amarillo de las paredes (balance de blancos), aplica una curva de contraste suave y vibrance que no sature la piel. Al reiluminar en el cuarto nuevo, no apagues la piel: solo agrega luz de borde de colores.
- Nitidez: reducción de ruido temporal ligera (hqdn3d) al decodificar → componer → superresolución x2 con FSRCNN → máscara de enfoque suave. Dibuja los logos 3D después de la superresolución, a resolución completa.
- Exporta con H.264, CRF 16, preset slow, tune film, yuv420p, AAC 192 kbps, +faststart.

PASO 8 — REVISIÓN ANTES DE ENTREGAR
- Saca capturas cada 2 s y en cada efecto. Revisa:
  - textos encimados o que tapen la cara;
  - subtítulos fuera de tiempo;
  - bordes de la máscara;
  - colores que se salgan de la ropa;
  - logos fuera de la mano.
- Corrige y vuelve a revisar. Después entrégame el MP4 y una lista de lo que hiciste y de cualquier limitación.
```

---

## Consejos para quien grabe el video

- **Iluminación:** de frente; evita contraluz de ventanas.
- **Fondo:** que contraste contigo (una pared lisa es ideal).
- **Ropa:** lisa y oscura si vas a pedir cambio de color.
- **Pide cada efecto en voz alta y deja una pausa de 2–3 s** después de pedirlo, para que se luzca el cambio.
- **Logos u objetos en la mano:** abre la palma hacia arriba, a la altura del pecho, durante 3–4 s.
