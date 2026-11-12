// Service worker: lets the game install as an app and work without internet.
// Bump VERSION whenever the game files change so devices pick up the new version.
const VERSION = "tug-of-war-v17";
const APP_FILES = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./padres.html",
  "./assets/equipo-a.webp",
  "./assets/equipo-b.webp",
  "./assets/icon-192.png",
  "./assets/icon-512.png",
  "./assets/icon-maskable-512.png",
  "./assets/icon-180.png",
  "./assets/vendor/qrcode.min.js",
  "./assets/vendor/peerjs.min.js",
];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(VERSION).then(async cache => {
    await cache.addAll(APP_FILES);
    // audios árabes grabados: se guardan todos para que suenen sin internet
    try {
      const idx = await fetch("./assets/audio/ar/index.json").then(r => r.json());
      await cache.put("./assets/audio/ar/index.json", new Response(JSON.stringify(idx), { headers: { "content-type": "application/json" } }));
      await cache.addAll([...new Set(Object.values(idx))].map(f => "./assets/audio/ar/" + f));
    } catch(e){}
  }).then(() => self.skipWaiting()));
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  const isFont = url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com";
  if (url.origin !== self.location.origin && !isFont) return;

  // The page itself: try the network first so updates arrive, fall back to the saved copy offline.
  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req)
        .then(res => { const copy = res.clone(); caches.open(VERSION).then(c => c.put("./index.html", copy)); return res; })
        .catch(() => caches.match("./index.html"))
    );
    return;
  }

  // The audio index must always match the published clips: network first, saved copy only offline.
  if (url.pathname.endsWith("/assets/audio/ar/index.json")) {
    event.respondWith(
      fetch(req, { cache:"no-store" })
        .then(res => { const copy = res.clone(); caches.open(VERSION).then(c => c.put("./assets/audio/ar/index.json", copy)); return res; })
        .catch(() => caches.match("./assets/audio/ar/index.json"))
    );
    return;
  }

  // Images, icons and fonts: use the saved copy, refresh it in the background.
  event.respondWith(
    caches.match(req).then(cached => {
      const fresh = fetch(req).then(res => {
        if (res.ok || res.type === "opaque") { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
        return res;
      }).catch(() => cached);
      return cached || fresh;
    })
  );
});
