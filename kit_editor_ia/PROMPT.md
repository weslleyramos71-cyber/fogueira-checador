# Prompt (pégalo en Claude Code, abierto en la carpeta del kit)

```
Eres mi editor de video. Vas a editar mi video como un reel vertical profesional usando el kit de esta carpeta.
Lee primero README.md y PLAN.md. Usa SIEMPRE los scripts del kit; no escribas un editor nuevo desde cero.

Mi video: ____ (ruta del archivo)
Idioma del video: ____
Color de acento (opcional): ____
Mi @ o marca (opcional): ____
Logos en PNG para la mano (opcional): ____

Haz esto en orden y avísame al terminar cada paso:

1. Si no existe la carpeta .venv, ejecuta: bash setup.sh. Si algo falla, lee el error, resuélvelo (instalar un paquete del sistema, reintentar una descarga) y vuelve a ejecutarlo.

2. .venv/bin/python scripts/prepare.py MI_VIDEO proyecto

3. .venv/bin/python scripts/transcribe.py proyecto
   Muéstrame la transcripción. Corrige nombres de marcas o productos mal escritos, y repite la verificación si dudas.

4. .venv/bin/python scripts/captions.py proyecto --fix "mal=bien" (las correcciones que hagan falta)
   Revisa captions.json: quita muletillas y tartamudeos, y marca en *acento* las palabras clave (marcas, cifras, beneficios). Cuando una palabra sea un color, usa #azul# o %verde%.

5. Lee la transcripción y detecta lo que pido en el video. Arma proyecto/plan.json siguiendo PLAN.md:
   - effects: cada efecto empieza justo en la palabra donde lo pido.
   - punch_in: 2–3 s de pantalla completa justo después de mostrar un efecto importante.
   - panel: un elemento por idea, sincronizado con la frase (palabras gigantes, chat, antes/después, muestras de color, audio, lista final, botón Seguir con mi @).
   Si en el video no pido efectos, haz solo el diseño (panel + subtítulos + audio limpio).
   Muéstrame el plan en una tabla de tiempos antes de seguir.

6. .venv/bin/python scripts/analyze.py proyecto   (tarda varios minutos)

7. Vista previa: .venv/bin/python scripts/render.py proyecto --preview "tiempos"
   Elige un tiempo por cada elemento del panel y uno por cada efecto. Abre proyecto/preview.png y revisa con ojo crítico:
   - textos encimados o cortados;
   - subtítulos sobre la cara;
   - la cara cortada en la tarjeta (ajusta layout.focus_y);
   - el color saliéndose de la ropa;
   - el logo fuera de la mano.
   Corrige plan.json o captions.json y repite hasta que todo se vea bien.

8. Render final: .venv/bin/python scripts/render.py proyecto
   Saca capturas cada 3 s del final.mp4, revísalas y entrégame la ruta del video con un resumen de lo que hiciste y de cualquier limitación.
```
