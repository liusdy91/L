# Islamic Tug of War (Tira de la Cuerda Islámica)

Juego para pizarra digital (o tablet/PC) en el que dos equipos compiten en la misma pantalla.
Cada respuesta correcta tira de la cuerda hacia su lado; gana quien lleve el pañuelo dorado hasta su línea.

- **Preguntas islámicas**: pilares, oraciones, profetas, Corán, fiestas y expresiones (opción múltiple).
- **Sumas con dátiles**: cuentas con pequeñas historias y teclado numérico (3 niveles).
- **Aprende árabe**: letras, números, animales, comida, colores, familia, cosas y saludos, con dibujos y pronunciación. Si el navegador tiene voz en árabe, aparece el botón 🔊 Escuchar.
- **Mixto**: alterna preguntas islámicas, árabe y sumas.

**Temas de las preguntas islámicas**: Pilares y fe, Salah, Ramadán y ayuno, Corán, Profetas, Historia del Islam, Hayy y lugares santos, Modales y duas. En la pantalla de inicio se eligen uno, varios o todos.
- **Un jugador**: juegas solo contra la computadora, que tira de la cuerda cada 9, 6 o 4 segundos según la velocidad elegida.

**Idiomas**: español, inglés y árabe (con escritura de derecha a izquierda y números arábigos orientales). El idioma general se elige en la pantalla de inicio o en la cabecera, y cada equipo puede cambiar el suyo durante la partida con los botones ES · EN · ع.

Abre `index.html` en un navegador (la carpeta `assets/` con las ilustraciones de las niñas debe estar al lado). No necesita instalación. Para añadir preguntas, edita las listas `QUIZ_ES`, `QUIZ_EN` y `QUIZ_AR` en el script: la misma posición en cada lista es la misma pregunta, así que añade cada pregunta en las tres y su número en la categoría que toque dentro de `CATS`. El vocabulario de árabe está en `LETTERS`, `NUMBERS`, `WORDS` y `PHRASES`. Las traducciones al inglés y al árabe conviene que las revise una persona hablante.

**Fuentes**: cada pregunta islámica muestra su fuente (Corán o hadiz sahih). La lista completa, con enlaces, está en [FUENTES.md](FUENTES.md).

**Instalar como app**: abre https://liusdy91.github.io/L/ y pulsa «Instalar app» (Android, Chrome o Edge), o en iPhone/iPad Safari → Compartir → «Añadir a pantalla de inicio». Funciona sin internet una vez instalada (`manifest.webmanifest` y `sw.js`). Si cambias imágenes o iconos, sube el número de `VERSION` en `sw.js`.

**Para niños**: niveles por edad (4–6, 7–9, 10–12), botón 🔊 para leer en voz alta, «Taller de letras» para escribir las letras árabes con el dedo, rachas y medallas por tema (guardadas solo en el dispositivo), tutorial de «¿Cómo se juega?» y celebración al ganar. La dificultad de cada pregunta está en `DIFF`. Información para familias y docentes en [padres.html](padres.html).
