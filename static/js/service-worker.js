const CACHE_NAME = 'casa-lupita-v2';
const STATIC_ASSETS = [
  '/static/css/styles.css',
  '/static/js/main.js',
  '/static/pwa/icon-192.png',
  '/static/pwa/icon-512.png',
  '/dashboard/offline/'
];

// Instalar el service worker y cachear activos estáticos
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Caching static assets');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Limpiar versiones antiguas de caché
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('[Service Worker] Clearing old cache');
            return caches.delete(cache);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Estrategia de Fetch
self.addEventListener('fetch', (event) => {
  // Solo manejar peticiones GET
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // Estrategia para archivos estáticos: Cache-First
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request);
      })
    );
    return;
  }

  // Estrategia para páginas: Network-First con fallback a offline
  event.respondWith(
    fetch(event.request)
      .catch(() => {
        return caches.match('/dashboard/offline/');
      })
  );
});
