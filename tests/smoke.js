// Pruebas automáticas del juego (Chromium + Playwright).
// Uso: npm install && npm test        (o: node tests/smoke.js)
// Sirve la carpeta del proyecto en un puerto local; la prueba online arranca su propio servidor PeerJS
// si el paquete «peer» está instalado (si no, se marca como OMITIDA).
const http = require("http"), fs = require("fs"), path = require("path"), assert = require("assert");
const { chromium, devices } = require("playwright");

const ROOT = path.join(__dirname, ".."), PORT = 8790, PEER_PORT = 9010;
const TYPES = { ".html":"text/html", ".js":"text/javascript", ".json":"application/json", ".css":"text/css", ".png":"image/png",
  ".jpg":"image/jpeg", ".webp":"image/webp", ".mp3":"audio/mpeg", ".webmanifest":"application/manifest+json", ".txt":"text/plain" };
const server = http.createServer((req, res) => {
  const file = path.join(ROOT, decodeURIComponent(req.url.split("?")[0]).replace(/\/$/, "/index.html"));
  if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream" });
  fs.createReadStream(file).pipe(res);
});
const URL = `http://localhost:${PORT}/index.html?test=1`;
const results = [];
async function test(name, fn){
  try { await fn(); results.push(["OK", name]); }
  catch (e) { results.push(e && e.skip ? ["OMITIDA", name + " — " + e.message] : ["FALLO", name + " — " + (e && e.message)]); }
}
const skip = msg => Object.assign(new Error(msg), { skip:true });

(async () => {
  await new Promise(r => server.listen(PORT, r));
  const browser = await chromium.launch({ args:["--disable-features=WebRtcHideLocalIpsWithMdns"] });
  const page = async (opts = { viewport:{ width:1280, height:800 } }, url = URL, tut = true) => {
    const ctx = await browser.newContext(opts);
    if (tut) await ctx.addInitScript(() => localStorage.setItem("tdc-tut", "1"));
    const p = await ctx.newPage(); p.errs = [];
    p.on("pageerror", e => p.errs.push(e.message));
    p.on("console", m => { if (m.type() === "error") p.errs.push(m.text()); });
    await p.goto(url); await p.waitForTimeout(800); return p;
  };
  const T = (p, fn, arg) => p.evaluate(fn, arg);

  await test("carga sin errores y muestra el tutorial la primera vez", async () => {
    const p = await page(undefined, URL, false);
    assert.ok(await p.isVisible("#tutBox"), "no aparece el tutorial");
    assert.deepStrictEqual(p.errs, []);
    await p.context().close();
  });

  await test("datos de preguntas: 85 filas por idioma, 4 opciones distintas, fuente, dificultad y tema", async () => {
    const p = await page();
    const r = await T(p, () => {
      const d = __tdc.data, bad = [];
      for (const [L, Q] of [["es", d.QUIZ_ES], ["en", d.QUIZ_EN], ["ar", d.QUIZ_AR]]) Q.forEach((row, i) => {
        if (row.length !== 5) bad.push(`${L}#${i} columnas`);
        if (new Set(row.slice(1).map(x => String(x).trim())).size !== 4) bad.push(`${L}#${i} opciones repetidas`);
      });
      return { n:[d.QUIZ_ES.length, d.QUIZ_EN.length, d.QUIZ_AR.length, d.SOURCES.length, d.DIFF.length, d.CAT_OF.length], bad };
    });
    assert.ok(r.n.every(x => x === r.n[0]), "longitudes distintas: " + r.n);
    assert.deepStrictEqual(r.bad, []);
    await p.context().close();
  });

  await test("todos los textos árabes tienen su audio", async () => {
    const p = await page();
    const missing = await T(p, async () => { const idx = await (await fetch("assets/audio/ar/index.json")).json(); return window.tdcArTexts().filter(t => !idx[t]); });
    assert.deepStrictEqual(missing, []);
    const files = Object.values(JSON.parse(fs.readFileSync(path.join(ROOT, "assets/audio/ar/index.json"), "utf8")));
    const absent = files.filter(f => !fs.existsSync(path.join(ROOT, "assets/audio/ar", f)));
    assert.deepStrictEqual(absent, [], "archivos de audio que faltan");
    await p.context().close();
  });

  for (const [name, dev] of [["móvil vertical", devices["iPhone 13"]], ["móvil horizontal", devices["iPhone 13 landscape"]], ["escritorio", { viewport:{ width:1280, height:800 } }]]) {
    await test(`3 idiomas y RTL sin desbordar la pantalla (${name})`, async () => {
      const p = await page(dev);
      for (const l of ["es", "en", "ar"]) {
        await p.click(`#langSeg button[lang="${l}"]`); await p.waitForTimeout(150);
        const r = await T(p, () => ({ dir: document.documentElement.dir, over: document.documentElement.scrollWidth > innerWidth + 1 }));
        assert.strictEqual(r.dir, l === "ar" ? "rtl" : "ltr", `dir en ${l}`);
        assert.ok(!r.over, `desborda en ${l}`);
      }
      await p.click('#langSeg button[lang="es"]'); await p.click("#startBtn"); await p.waitForTimeout(600);
      assert.ok(!(await T(p, () => document.documentElement.scrollWidth > innerWidth + 1)), "la partida desborda");
      assert.deepStrictEqual(p.errs, []);
      await p.context().close();
    });
  }

  await test("dos equipos: aciertos mueven la cuerda y la partida termina y se reinicia", async () => {
    const p = await page();
    await p.click('#targetSeg button[data-v="5"]'); await p.click("#startBtn"); await p.waitForTimeout(400);
    for (let i = 0; i < 5; i++) { await T(p, () => { __tdc.teams.A.locked = false; __tdc.check(__tdc.teams.A, true); }); await p.waitForTimeout(400); }
    await p.waitForTimeout(1400);
    assert.strictEqual(await T(p, () => __tdc.pos), -5);
    assert.strictEqual(await T(p, () => __tdc.lastWinner), "A");
    assert.ok(await p.isVisible("#winBox"));
    await p.click("#againBtn"); await p.waitForTimeout(400);
    assert.strictEqual(await T(p, () => __tdc.pos), 0);
    assert.ok(await T(p, () => __tdc.playing));
    await p.context().close();
  });

  await test("respuesta incorrecta: no mueve la cuerda, guarda el fallo y ofrece «Siguiente»", async () => {
    const p = await page();
    await p.click("#startBtn"); await p.waitForTimeout(400);
    await T(p, () => __tdc.check(__tdc.teams.A, false)); await p.waitForTimeout(200);
    assert.strictEqual(await T(p, () => __tdc.pos), 0);
    assert.strictEqual(await T(p, () => __tdc.teams.A.missed.length), 1);
    assert.ok(await p.isVisible("#zoneA .next-btn"));
    await p.context().close();
  });

  await test("un jugador: la computadora tira sola", async () => {
    const p = await page();
    await p.click('#playersSeg button[data-v="1"]'); await p.click('#cpuSeg button[data-v="4"]'); await p.click("#startBtn");
    await p.waitForTimeout(5500);
    assert.ok(await T(p, () => __tdc.teams.B.correct) >= 1, "la computadora no tiró");
    await p.context().close();
  });

  await test("práctica: 10 preguntas, resumen con repaso y progreso guardado tras recargar", async () => {
    const p = await page();
    await p.click('#playersSeg button[data-v="0"]'); await p.click("#startBtn"); await p.waitForTimeout(300);
    for (let i = 0; i < 10; i++) {
      await T(p, i => { const t = __tdc.teams.A; t.locked = false; __tdc.check(t, i % 2 === 0); }, i); await p.waitForTimeout(120);
      await p.click("#zoneA .next-btn").catch(() => {}); await p.waitForTimeout(120);
    }
    assert.ok(await p.isVisible("#sumBox"), "no aparece el resumen");
    assert.strictEqual((await p.textContent("#sumScore")).trim(), "5/10");
    assert.strictEqual(await p.$$eval("#sumReview li", x => x.length), 5);
    await p.reload(); await p.waitForTimeout(500);
    assert.ok(await T(p, () => !!localStorage.getItem("tdc-progress")), "no se guardó el progreso");
    await p.context().close();
  });

  await test("Aprende árabe: unidades y lecciones visibles, la primera abre", async () => {
    const p = await page();
    await p.click("#learnBtn"); await p.waitForTimeout(400);
    assert.ok(await p.$$eval(".unit", x => x.length) >= 6);
    assert.ok(await p.$$eval(".lesson-btn", x => x.length) >= 29);
    await p.click(".units .unit:first-child .lesson-btn:first-child"); await p.waitForTimeout(400);
    assert.ok(await p.isVisible(".lx-show"), "la lección no abre");
    assert.deepStrictEqual(p.errs, []);
    await p.context().close();
  });

  await test("Materias: 5 áreas, módulos con estado y la práctica abre con las categorías del módulo", async () => {
    const p = await page();
    await p.click("#subjBtn"); await p.waitForSelector(".subj-area");
    assert.strictEqual(await p.$$eval(".subj-area", x => x.length), 5);
    await p.click('.subj-area[data-area="islam"]'); await p.waitForTimeout(200);
    assert.strictEqual(await p.$$eval("#subjBody .unit", x => x.length), 6);
    await p.click('#subjBody .unit[data-module="fiqh"] .next-btn'); await p.waitForTimeout(500);
    assert.ok(await T(p, () => __tdc.playing), "no empezó la práctica");
    assert.deepStrictEqual(await T(p, () => [__tdc.cfg.players, __tdc.cfg.mode, [...__tdc.cfg.cats].sort()]), [0, "quiz", ["ayuno", "hayy", "salah"]]);
    await p.click("#menuBtn"); await p.click("#subjBtn"); await p.click('.subj-area[data-area="arabic"]'); await p.waitForTimeout(200);
    await p.click('#subjBody .unit[data-module="literacy"] .next-btn'); await p.waitForTimeout(300);
    assert.ok(await p.isVisible("#learnBox"), "no abre Aprende árabe");
    await p.click("#learnClose"); await p.click('#langSeg button[lang="ar"]'); await p.click("#subjBtn"); await p.waitForTimeout(200);
    assert.strictEqual(await p.textContent("#subjTitle"), "المواد");
    assert.ok(!(await T(p, () => document.documentElement.scrollWidth > innerWidth + 1)));
    assert.deepStrictEqual(p.errs, []);
    await p.context().close();
  });

  await test("lecciones: un borrador no se ve sin ?revision=1; con él se lee, se practica y se completa", async () => {
    const p = await page();
    await p.click("#subjBtn"); await p.click('.subj-area[data-area="islam"]'); await p.waitForTimeout(300);
    assert.strictEqual(await p.$$eval('#subjBody .unit[data-module="fiqh"] .subj-units button', x => x.length), 0, "el borrador se ve para los niños");
    await p.context().close();
    const r = await page(undefined, URL + "&revision=1");
    await r.click("#subjBtn"); await r.click('.subj-area[data-area="islam"]'); await r.waitForTimeout(300);
    await r.click('#subjBody .unit[data-module="fiqh"] .subj-units button'); await r.waitForTimeout(200);
    assert.ok(await r.isVisible(".lx-banner"), "falta el aviso de borrador");
    assert.ok(await r.$$eval(".ev-card a", a => a.every(x => x.href.startsWith("https://shamela.ws/"))), "pruebas sin enlace a Shamela");
    await r.click(".lx-doc .next-btn");
    const lesson = JSON.parse(fs.readFileSync(path.join(ROOT, "content/lessons/a2-2/a2-2-01.json"), "utf8"));
    const n = lesson.activities.length;
    for (let i = 0; i < n; i++){
      // pulsa la opción correcta (las opciones salen desordenadas; se busca por su texto)
      const label = lesson.activities[i].options[lesson.activities[i].answer].es;
      await r.click(`.lx-opts button:has-text("${label}")`); await r.waitForTimeout(80);
      await r.click(".lx-why .next-btn"); await r.waitForTimeout(80);
    }
    assert.match(await r.textContent(".lx-doc .lx-q"), new RegExp(`${n} de ${n}`));
    assert.ok(await r.evaluate(() => JSON.parse(localStorage.getItem("tdc-learn")).done["a2-2-01"] === 3), "no se guardó la lección");
    assert.deepStrictEqual(r.errs, []);
    await r.context().close();
  });

  await test("perfiles en el dispositivo: progreso separado, repaso de fallos y migración del progreso anterior", async () => {
    const ctx = await browser.newContext({ viewport:{ width:1280, height:800 } });
    await ctx.addInitScript(() => { if (!localStorage.getItem("seeded")){ localStorage.setItem("seeded", "1"); localStorage.setItem("tdc-tut", "1");
      localStorage.setItem("tdc-progress", JSON.stringify({ c:{ "cat:fe":3 }, traced:[] })); } });
    const p = await ctx.newPage(); p.errs = []; p.on("pageerror", e => p.errs.push(e.message));
    await p.goto(URL); await p.waitForTimeout(600);
    const mk = async (name, age) => {
      await p.click("#profNew"); await p.fill("#profAlias", name); await p.click(`#profAge button[data-v="${age}"]`); await p.click("#profSave"); await p.waitForTimeout(150);
    };
    await p.click("#profBtn"); await mk("Aisha", 1);
    assert.strictEqual(await T(p, () => JSON.parse(localStorage.getItem("tdc-progress@" + __tdc.profiles.active)).c["cat:fe"]), 3, "no migró el progreso anterior");
    assert.strictEqual(await T(p, () => __tdc.cfg.age), 1);
    await mk("Maryam", 3);
    assert.strictEqual(await p.$$eval(".prof-card", x => x.length), 2);
    await p.click("#profClose");
    assert.strictEqual(await p.inputValue("#inA"), "Maryam");
    // Maryam falla una pregunta → aparece el repaso
    await p.click('#playersSeg button[data-v="0"]'); await p.click("#startBtn"); await p.waitForTimeout(300);
    await T(p, () => __tdc.check(__tdc.teams.A, false)); await p.click("#menuBtn"); await p.waitForTimeout(200);
    assert.ok(await p.isVisible("#reviewBtn"), "no aparece el botón de repaso");
    assert.match(await p.textContent("#reviewBtn"), /1/);
    await p.click("#reviewBtn"); await p.waitForTimeout(300);
    assert.ok(await T(p, () => __tdc.cfg.review && __tdc.playing), "no empezó el repaso");
    await T(p, () => { const t = __tdc.teams.A; t.locked = false; __tdc.check(t, true); }); await p.click("#zoneA .next-btn"); await p.waitForTimeout(300);
    assert.ok(await p.isVisible("#sumBox"), "el repaso no termina");
    assert.strictEqual((await p.textContent("#sumScore")).trim(), "1/1");
    // Aisha no tiene ese fallo
    await p.click("#sumSetup"); await p.click("#profBtn"); await p.click('.prof-card:not(.on) .next-btn'); await p.click("#profClose");
    assert.strictEqual(await p.inputValue("#inA"), "Aisha");
    assert.strictEqual(await T(p, () => Object.keys(__tdc.mastery).length), 0, "el progreso no está separado");
    // borrar Maryam borra sus datos
    await p.click("#profBtn");
    const mid = await T(p, () => __tdc.profiles.list.find(x => x.name === "Maryam").id);
    await p.click(`.prof-card[data-id="${mid}"] .row-btns button:last-child`); await p.click(`.prof-card[data-id="${mid}"] .row-btns button:first-child`);
    assert.strictEqual(await p.$$eval(".prof-card", x => x.length), 1);
    assert.ok(await T(p, id => !localStorage.getItem("tdc-mastery@" + id) && !localStorage.getItem("tdc-progress@" + id), mid), "quedaron datos del perfil borrado");
    await p.reload(); await p.waitForTimeout(500);
    assert.strictEqual(await p.inputValue("#inA"), "Aisha", "no recuerda el perfil activo");
    assert.deepStrictEqual(p.errs, []);
    await ctx.close();
  });

  await test("códigos de sala online: 6 caracteres, sin repetirse en 2000 intentos", async () => {
    const p = await page();
    const codes = await T(p, () => Array.from({ length:2000 }, () => __tdc.netCode()));
    assert.ok(codes.every(c => /^[A-HJKMNP-Z2-9]{6}$/.test(c)), "formato");
    assert.ok(new Set(codes).size > 1990, "demasiadas repeticiones");
    await p.context().close();
  });

  await test("online: dos dispositivos se conectan, la cuerda se sincroniza y se detecta la desconexión", async () => {
    let PeerServer; try { ({ PeerServer } = require("peer")); } catch (e) { throw skip("instala el paquete «peer» (npm install)"); }
    const ps = PeerServer({ port: PEER_PORT, path: "/", host: "127.0.0.1" });
    try {
      const NURL = `http://localhost:${PORT}/index.html?peerhost=127.0.0.1&peerport=${PEER_PORT}`;
      const H = await page(undefined, NURL);
      await H.fill("#inA", "Aisha"); await H.click('#playersSeg button[data-v="3"]');
      await H.waitForFunction(() => /^[A-Z0-9]{6}$/.test(document.getElementById("netCode").textContent), null, { timeout:15000 });
      const code = await H.textContent("#netCode");
      const G = await page(devices["Pixel 7 landscape"], NURL + "#join-" + code);
      await H.waitForFunction(() => /unió/.test(document.getElementById("netStatus").textContent), null, { timeout:20000 });
      await H.click('#targetSeg button[data-v="5"]'); await H.click("#startBtn"); await H.waitForTimeout(700);
      assert.ok(await T(G, () => __tdc.playing), "el invitado no empezó");
      assert.strictEqual(await T(G, () => __tdc.cfg.target), 5);
      await T(G, () => __tdc.check(__tdc.teams.B, true)); await H.waitForTimeout(500);
      assert.strictEqual(await T(H, () => __tdc.pos), 1); assert.strictEqual(await T(G, () => __tdc.pos), 1);
      await H.context().close(); await G.waitForTimeout(15000);
      assert.match(await G.textContent("#netStatus"), /conexión/, "no avisa de la desconexión");
      await G.context().close();
    } finally { ps.close && ps.close(); }
  });

  await browser.close(); server.close();
  for (const [s, n] of results) console.log(`${s.padEnd(8)} ${n}`);
  const failed = results.filter(r => r[0] === "FALLO").length;
  console.log(`\n${results.length - failed} de ${results.length} sin fallos`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
