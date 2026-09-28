// Offline-Speicher: App und Kartendaten aus dem Cache, Commons-Fotos nach erstem Laden ebenfalls.
const VERSION = '20260929015537';
const CORE = ['./', 'index.html', 'denkmaeler.json', 'basiskarte.json', 'aenderungen.json', 'rundgaenge.json',
  'umland.json', 'bodendenkmaeler.json', 'fotos.json', 'umrisse.json', 'wiki.json', 'architekten.json', 'manifest.webmanifest', 'icon-192.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open('core-' + VERSION).then(c => Promise.all(CORE.map(u => c.add(u).catch(() => null)))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('core-') && k !== 'core-' + VERSION).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  if (url.hostname === 'generativelanguage.googleapis.com') return;
  if (url.hostname === 'upload.wikimedia.org' || url.hostname === 'thumb.wikimedia.org' || (url.hostname === 'commons.wikimedia.org' && url.pathname.includes('Special:FilePath'))) {           // Fotos: Cache zuerst
    e.respondWith(caches.open('fotos').then(async c => (await c.match(e.request)) ||
      fetch(e.request).then(r => { if (r.ok || r.type === 'opaque') c.put(e.request, r.clone()); return r; })));
    return;
  }
  if (url.origin !== location.origin) return;
  if (e.request.mode === 'navigate') {                      // Seite: Netz zuerst, offline aus dem Cache
    e.respondWith(fetch(e.request).catch(() => caches.match('index.html')));
    return;
  }
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request)));
});
