# Audios árabes

Los audios de `assets/audio/ar/` están generados con **ElevenLabs** (modelo `eleven_multilingual_v2`, voz de la biblioteca «Hijazi», id `fkqevZRU7Xj52dY1CTkq`, ajustes `stability 0.75`, `similarity_boost 0.75`). Audio generado con ElevenLabs (elevenlabs.io).

Cómo se hicieron:
1. La lista de textos sale del juego: en la consola del navegador, `tdcArTexts()`.
2. Las palabras sin vocales se envían con su forma vocalizada (tabla `DIAC` de `gen.py`), para que la voz no adivine.
3. Cada audio se guarda como `sha1("hijazi|" + texto)[:12] + ".mp3"` y `index.json` relaciona texto → archivo.
4. Con ffmpeg: se quitan los silencios, se ralentiza al 85 % (salvo las sílabas sueltas), se añaden 0,35 s de silencio al principio (para que los móviles no corten el comienzo) y se guarda en mono, 44,1 kHz, 64 kbps.

Si se añaden textos nuevos al juego, hay que generar solo esos con la misma voz y ajustes y añadirlos a `index.json`.

`gen.py` y `syll.py` son los scripts de la versión anterior (voz libre Piper `ar_JO-kareem`, licencia MIT) y sirven de alternativa sin cuenta.
