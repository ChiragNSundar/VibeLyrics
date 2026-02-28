const CACHE_NAME = 'vibelyrics-v5';
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/manifest.json',
    '/favicon.ico',
    // We would list main CSS/JS bundles here, 
    // but Vite injects them dynamically or we cache them as they are requested
];

// Install Event
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate Event
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        })
    );
    self.clients.claim();
});

// Fetch Event - Network First with Cache Fallback for API, Cache First for Static
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Skip non-GET requests or browser extensions
    if (event.request.method !== 'GET' || !url.protocol.startsWith('http')) {
        return;
    }

    // For API requests, try network first, then fail (let offlineStore handle it on the client side)
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(fetch(event.request).catch(() => new Response(JSON.stringify({ error: "offline" }), {
            headers: { 'Content-Type': 'application/json' },
            status: 503
        })));
        return;
    }

    // For static assets, try Cache First, then Network
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
                return cachedResponse;
            }
            return fetch(event.request).then((networkResponse) => {
                // Don't cache bad responses
                if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
                    return networkResponse;
                }
                const responseToCache = networkResponse.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, responseToCache);
                });
                return networkResponse;
            }).catch(() => {
                // Fallback for navigation
                if (event.request.mode === 'navigate') {
                    return caches.match('/index.html');
                }
            });
        })
    );
});

// Background Sync Event
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-vibelyrics') {
        event.waitUntil(syncData());
    }
});

async function syncData() {
    // In a real app, this would read from IndexedDB syncQueue and push to the server
    // Since we don't have direct access to idb here easily (unless we import idb via importScripts),
    // we notify the client window to perform the sync.
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
        client.postMessage({ type: 'SYNC_NOW' });
    });
}
