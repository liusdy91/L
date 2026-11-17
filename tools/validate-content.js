// Valida content/curriculum.json y las lecciones de content/lessons/. Uso: node tools/validate-content.js
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, ".."), errors = [];
const err = m => errors.push(m);
const LANGS = ["es", "en", "ar"], ACTS = ["learn", "spell", "trace", "quiz", "math", "game"];
const CATS = ["fe", "salah", "ayuno", "coran", "profetas", "historia", "hayy", "adab"];
const STATUS = ["draft", "in_review", "approved", "published", "needs_update"];
const tri = (o, where) => LANGS.forEach(l => { if (!o || typeof o[l] !== "string" || !o[l].trim()) err(`${where}: falta el texto en ${l}`); });
const act = (a, where) => {
  if (!a) return;
  if (!ACTS.includes(a.type)) err(`${where}: actividad desconocida «${a.type}»`);
  if (a.type === "quiz") (a.cats || []).forEach(c => { if (!CATS.includes(c)) err(`${where}: categoría desconocida «${c}»`); });
};

const cur = JSON.parse(fs.readFileSync(path.join(ROOT, "content/curriculum.json"), "utf8"));
const ids = new Set(), units = new Map();
const uniq = (id, where) => { if (!id) err(`${where}: sin id`); else if (ids.has(id)) err(`id repetido: ${id}`); else ids.add(id); };
if (cur.areas.length !== 5) err(`se esperaban 5 áreas, hay ${cur.areas.length}`);
cur.areas.forEach(a => {
  uniq(a.id, "área"); tri(a.t, `área ${a.id}`);
  a.modules.forEach(m => {
    uniq(m.id, `módulo de ${a.id}`); tri(m.t, `módulo ${m.id}`); act(m.activity, `módulo ${m.id}`);
    if (!m.units.length) err(`módulo ${m.id}: sin unidades`);
    m.units.forEach(u => {
      uniq(u.id, `unidad de ${m.id}`); tri(u.t, `unidad ${u.id}`); act(u.activity, `unidad ${u.id}`);
      if (u.status && u.status !== "available") err(`unidad ${u.id}: estado desconocido «${u.status}»`);
      units.set(u.id, { religious: !!a.religious });
    });
  });
});

// Lecciones (fase 4 en adelante)
const LDIR = path.join(ROOT, "content/lessons");
const files = fs.existsSync(LDIR) ? fs.readdirSync(LDIR, { recursive:true }).filter(f => f.endsWith(".json")) : [];
files.forEach(f => {
  const where = `lección ${f}`; let L;
  try { L = JSON.parse(fs.readFileSync(path.join(LDIR, f), "utf8")); } catch (e) { return err(`${where}: JSON no válido`); }
  uniq(L.id, where);
  const u = units.get(L.unit); if (!u) return err(`${where}: unidad «${L.unit}» no existe en el mapa`);
  ["objectives", "explanation"].forEach(k => { if (!L[k]) err(`${where}: falta ${k}`); });
  tri(L.explanation, `${where} explicación`);
  if (!L.review || !STATUS.includes(L.review.status)) err(`${where}: review.status no válido`);
  if (L.review && ["approved", "published"].includes(L.review.status) && (!L.review.reviewer || !L.review.date)) err(`${where}: aprobada sin revisor ni fecha`);
  const ev = new Map((L.evidence || []).map(e => [e.id, e]));
  (L.activities || []).forEach((q, i) => {
    tri(q.q, `${where} actividad ${i + 1}`); tri(q.why, `${where} actividad ${i + 1} (por qué)`);
    if (!Array.isArray(q.options) || q.answer == null || !q.options[q.answer]) err(`${where} actividad ${i + 1}: respuesta no válida`);
    if (u.religious && !(q.evidence || []).length) err(`${where} actividad ${i + 1}: contenido religioso sin evidencia`);
    (q.evidence || []).forEach(id => { if (!ev.has(id)) err(`${where} actividad ${i + 1}: evidencia «${id}» no existe`); });
  });
  ev.forEach(e => {
    if (!e.source || !/^https:\/\/shamela\.ws\//.test(e.source.shamela || "")) err(`${where} evidencia ${e.id}: falta el enlace a Shamela`);
    if (e.hadith && (e.hadith.grade !== "sahih" || !e.hadith.collection || !e.hadith.number || !e.hadith.graded_by)) err(`${where} evidencia ${e.id}: el hadiz debe ser sahih, con colección, número y quién lo gradúa`);
  });
});

if (errors.length) { console.error("Contenido NO válido:\n- " + errors.join("\n- ")); process.exit(1); }
console.log(`Contenido válido: ${cur.areas.length} áreas, ${ids.size - files.length} entradas del mapa, ${files.length} lecciones.`);
