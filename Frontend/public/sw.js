const CACHE_NAME = 'med-app-v1';

// Assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
];

// ── Install: cache static assets ──────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// ── Activate: remove old caches ───────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// ── Fetch: network-first for API, cache-first for assets ──
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Skip non-GET and browser-extension requests
  if (request.method !== 'GET') return;
  if (!request.url.startsWith('http')) return;

  if (request.url.includes('/api/')) {
    // API calls: try network, return offline error if it fails
    event.respondWith(
      fetch(request).catch(() =>
        new Response(JSON.stringify({ offline: true, error: 'No connection' }), {
          headers: { 'Content-Type': 'application/json' },
        })
      )
    );
  } else {
    // Static assets: cache first, fallback to network
    event.respondWith(
      caches.match(request).then((cached) => cached || fetch(request))
    );
  }
});