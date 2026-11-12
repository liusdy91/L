# Islamic Tug of War (Tira de la Cuerda Islámica)

Juego para pizarra digital (o tablet/PC) en el que dos equipos compiten en la misma pantalla.
Cada respuesta correcta tira de la cuerda hacia su lado; gana quien lleve el pañuelo dorado hasta su línea.

- **Preguntas islámicas**: pilares, oraciones, profetas, Corán, fiestas y expresiones (opción múltiple).
- **Sumas con dátiles**: cuentas con pequeñas historias y teclado numérico (3 niveles).
- **Mixto**: alterna preguntas islámicas y sumas.

**Aprende árabe** (sección aparte, sin competir): camino de lecciones con metodología estructurada — 1) el alfabeto en 8 lecciones por familias de letras, 2) las vocales cortas (se abre al terminar el alfabeto), 3) números del 1 al 10, 4) primeras palabras, 5) saludos. Cada lección: Aprende → Practica (reintentos sin castigo) → Escribe (trazar letras) → Comprueba (5 preguntas; 3 aciertos abren la siguiente). Datos en `LEARN` y `EX`; el progreso se guarda en el dispositivo.

**Temas de las preguntas islámicas**: Pilares y fe, Salah, Ramadán y ayuno, Corán, Profetas, Historia del Islam, Hayy y lugares santos, Modales y duas. En la pantalla de inicio se eligen uno, varios o todos.
- **Un jugador**: juegas solo contra la computadora, que tira de la cuerda cada 9, 6 o 4 segundos según la velocidad elegida.
- **🌐 Online**: dos personas, cada una en su dispositivo y en lugares distintos. Una crea la sala (código de 4 letras, enlace o QR) y la otra se une. La conexión es directa entre los dos navegadores (WebRTC con la librería libre [PeerJS](https://peerjs.com/), licencia MIT, en `assets/vendor/`). Solo funciona en el enlace público del juego.

**Idiomas**: español, inglés y árabe (con escritura de derecha a izquierda y números arábigos orientales). El idioma general se elige en la pantalla de inicio o en la cabecera, y cada equipo puede cambiar el suyo durante la partida con los botones ES · EN · ع.

Abre `index.html` en un navegador (la carpeta `assets/` con las ilustraciones de las niñas debe estar al lado). No necesita instalación. Para añadir preguntas, edita las listas `QUIZ_ES`, `QUIZ_EN` y `QUIZ_AR` en el script: la misma posición en cada lista es la misma pregunta, así que añade cada pregunta en las tres y su número en la categoría que toque dentro de `CATS`. El vocabulario de árabe está en `LETTERS`, `NUMBERS`, `WORDS` y `PHRASES`. Las traducciones al inglés y al árabe conviene que las revise una persona hablante.

**Fuentes**: cada pregunta islámica muestra su fuente (Corán o hadiz sahih). La lista completa, con enlaces, está en [FUENTES.md](FUENTES.md).

**Instalar como app**: abre https://liusdy91.github.io/L/ y pulsa «Instalar app» (Android, Chrome o Edge), o en iPhone/iPad Safari → Compartir → «Añadir a pantalla de inicio». Funciona sin internet una vez instalada (`manifest.webmanifest` y `sw.js`). Si cambias imágenes o iconos, sube el número de `VERSION` en `sw.js`.

**Para niños**: niveles por edad (4–6, 7–9, 10–12), botón 🔊 para leer en voz alta, «Taller de letras» para escribir las letras árabes con el dedo, rachas y medallas por tema (guardadas solo en el dispositivo), tutorial de «¿Cómo se juega?» y celebración al ganar. La dificultad de cada pregunta está en `DIFF`. Información para familias y docentes en [padres.html](padres.html).

**Práctica**: modo de una sola persona con 10 preguntas, contador, botón «Siguiente» y resumen final con estrellas y las preguntas falladas (respuesta correcta y fuente). En la tira de la cuerda, al fallar se puede leer la respuesta correcta antes de seguir, y al ganar aparece «Para repasar».

**Deletrea palabras** (dentro de «Aprende árabe»): se ve un dibujo, se escucha la palabra y se forma letra a letra tocando fichas; al terminar se ve la palabra con sus letras unidas. Tres niveles (fácil con pistas, normal, difícil con todo el alfabeto), rondas de 8 palabras y medalla. Palabras en `SPELL`.

**Curso de árabe (método de Medina)** (dentro de «Aprende árabe»): 8 lecciones de gramática con la metodología de los libros de Medina —هٰذَا y مَا، أَ…؟ con نَعَمْ/لَا، مَنْ، الـ، فِي/عَلَى y أَيْنَ، هٰذِهِ y el femenino، la iḍāfa y los pronombres—. Cada lección: vocabulario, regla, frases modelo vocalizadas con audio y ejercicios (completar, significado, ordenar palabras, vocabulario). Contenido original en `GRAMMAR`; conviene que lo revise un profesor de árabe.

**Audios en árabe**: todas las palabras y frases árabes de «Aprende árabe» llevan audio grabado en `assets/audio/ar/` (índice en `index.json`), generado con la voz libre [Piper](https://github.com/rhasspy/piper) `ar_JO-kareem` ([rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices), licencia MIT). Así suenan en cualquier dispositivo aunque no tenga voz árabe instalada; si falta algún audio se usa la voz del dispositivo.
