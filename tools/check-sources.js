// Comprueba EN LÍNEA que el texto árabe de cada prueba aparece tal cual en la página de Shamela que enlaza
// (se ignora solo el orden de las vocales, los espacios y la puntuación). Uso: node tools/check-sources.js
const fs = require("fs"), path = require("path"), { execFile } = require("child_process");
const ROOT = path.join(__dirname, ".."), LDIR = path.join(ROOT, "content/lessons");
// curl respeta la configuración de proxy del sistema (HTTPS_PROXY)
const get = url => new Promise((ok, ko) => execFile("curl", ["-sS", "--fail", "--max-time", "30", "-A", "tug-of-war-content-check", url],
  { maxBuffer: 20 * 1024 * 1024 }, (err, out) => err ? ko(new Error(url + " → " + err.message.split("\n")[0])) : ok(out)));
const pageText = html => {
  const m = html.match(/<div class="nass[^>]*>([\s\S]*?)<\/div>/);
  return (m ? m[1] : "").replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ").replace(/&quot;/g, '"').replace(/&#039;/g, "'").replace(/&amp;/g, "&");
};
// letras sin vocales; las vocales se comparan aparte como «bolsa» por letra para no depender de su orden en Unicode
const norm = s => s.replace(/⦗[^⦘]*⦘/g, "").replace(/[ـ\s"'«»().,،؛:!؟?\[\]﴿﴾-]/g, "");
const DIA = /[ً-ْٰ]/;
const units = s => { const out = []; for (const ch of norm(s)) { if (DIA.test(ch) && out.length) out[out.length - 1] += ch; else out.push(ch); } return out.map(u => u[0] + [...u.slice(1)].sort().join("")); };
const contains = (page, frag) => { const P = units(page).join("|"), F = units(frag).join("|"); return P.includes(F); };

(async () => {
  const files = fs.existsSync(LDIR) ? fs.readdirSync(LDIR, { recursive: true }).filter(f => f.endsWith(".json")) : [];
  let bad = 0, n = 0;
  for (const f of files) {
    const L = JSON.parse(fs.readFileSync(path.join(LDIR, f), "utf8"));
    for (const e of L.evidence || []) {
      n++;
      try {
        const txt = pageText(await get(e.source.shamela));
        if (contains(txt, e.text)) console.log(`OK     ${L.id} ${e.id}  ${e.source.shamela}`);
        else { bad++; console.log(`FALLO  ${L.id} ${e.id}  el texto no está en ${e.source.shamela}`); }
      } catch (err) { bad++; console.log(`FALLO  ${L.id} ${e.id}  ${err.message}`); }
    }
  }
  console.log(`\n${n - bad} de ${n} pruebas coinciden con Shamela`);
  process.exit(bad ? 1 : 0);
})();
