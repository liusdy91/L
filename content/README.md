# Contenido de la plataforma

Aquí vive el contenido curricular, separado del código del juego (`index.html`).

- `curriculum.json` — el mapa aprobado: 5 áreas → módulos → unidades, en español, inglés y árabe.
  - `status: "available"` en una unidad = ya tiene actividad en el juego; sin `status` = en preparación.
  - `activity` en un módulo o unidad = qué abre el botón: `learn` (Aprende árabe), `spell`, `trace`,
    `quiz` (práctica con preguntas de esas categorías), `math`, `game` (Tira de la Cuerda en ese modo).
  - `religious: true` en un área = todo su contenido sigue las reglas editoriales de abajo.
- `lessons/` — (fase 4) una lección por archivo: `lessons/<id de unidad>/<id de lección>.json`.

`npm test` valida estos archivos (`tools/validate-content.js`) antes de publicar.

## Reglas editoriales del contenido religioso

Decididas por la propietaria del proyecto (17-nov-2026):

0. **Manhaj: Ahlus-Sunnah wal-Jamā'ah según el camino de los Salaf (salafi).** Nada de fuentes chiíes, sufíes
   ni de otras sectas o desviaciones. Solo se usan los libros de `content/sources.json`; el validador rechaza
   cualquier otro. Para añadir un libro hay que comprobar autor y edición, y que lo apruebe la propietaria.
1. **Fuente: la biblioteca Shamela** (shamela.ws). Cada afirmación lleva el libro, el volumen/página o número
   y el enlace a Shamela.
2. **Solo lo sahih**, según Ahlus-Sunnah wal-Jamā'ah. Los hadices llevan colección, número y grado, con quién
   lo gradúa (por ejemplo: al-Bukhari; Muslim; al-Albani en Sahih Abi Dawud). Nada da'if ni sin origen.
3. No se inventan hadices, referencias, números, grados ni consensos; no se atribuyen palabras sin fuente.
4. Donde hay diferencias reconocidas entre sabios, se dice qué explicación se enseña.
5. Solo se muestra a los niños una lección con `review.status: "published"`. Todo lo demás es borrador.
6. El texto árabe de cada prueba se copia **tal cual** de la página de Shamela enlazada (también las aleyas, tal como
   las escribe esa edición). `npm run check-sources` lo comprueba en línea página por página.
7. Las traducciones al español y al inglés son «traducción del significado», preparadas para el juego; las
   explicaciones y los ejercicios se limitan a lo que dicen las pruebas.

## Plantilla de una lección (`lessons/<unidad>/<lección>.json`)

```json
{
  "id": "a2-2-01",
  "unit": "a2-2",
  "ages": [7, 9],
  "objectives": { "es": ["…"], "en": ["…"], "ar": ["…"] },
  "prerequisites": ["a2-1-01"],
  "explanation": { "es": "…", "en": "…", "ar": "…" },
  "examples": [ { "es": "…", "en": "…", "ar": "…" } ],
  "activities": [
    { "type": "choice", "q": { "es": "…", "en": "…", "ar": "…" }, "options": [ {"es":"…","en":"…","ar":"…"} ],
      "answer": 0, "why": { "es": "…", "en": "…", "ar": "…" }, "evidence": ["e1"] }
  ],
  "evidence": [
    { "id": "e1", "claim": "…",
      "quran": { "surah": 5, "ayah": 6 },
      "hadith": { "collection": "Sahih al-Bukhari", "number": "135", "grade": "sahih", "graded_by": "al-Bukhari" },
      "source": { "book": "…", "ref": "vol./pág. o número", "shamela": "https://shamela.ws/book/…/…" } }
  ],
  "review": { "status": "draft", "reviewer": "", "date": "" }
}
```

`review.status`: `draft` → `in_review` → `approved` → `published` (o `needs_update`).
