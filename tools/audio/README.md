# Audios árabes del juego

Los audios de `assets/audio/ar/` se generan con la voz libre **Piper `ar_JO-kareem` (medium)** — [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices), licencia MIT.

1. Instalar Piper: `python3 -m venv venv && ./venv/bin/pip install piper-tts`
2. Descargar `ar_JO-kareem-medium.onnx` y `ar_JO-kareem-medium.onnx.json` de `rhasspy/piper-voices` (`ar/ar_JO/kareem/medium/`).
3. Sacar la lista de textos árabes del juego: abrir `index.html` y ejecutar `JSON.stringify(tdcArTexts())` en la consola; guardarla como `texts.json`.
4. Generar todos los audios (voz lenta, 1,5×): `./venv/bin/python gen.py texts.json ar_JO-kareem-medium.onnx ../../assets/audio/ar`
5. Regrabar las sílabas con vocal corta (بَ بِ بُ…): `./venv/bin/python syll.py ar_JO-kareem-medium.onnx ../../assets/audio/ar`

Al cambiar los audios, sube `VERSION` en `sw.js`.
