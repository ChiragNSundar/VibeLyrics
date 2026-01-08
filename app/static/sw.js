const CACHE_NAME = 'vibelyrics-v1';
const ASSETS_TO_CACHE = [
    '/static/css/style.css',
    '/static/js/session.js',
    '/static/js/alpine-components.js',
    'https://cdn.jsdelivr.net/npm/alpinejs@3.13.3/dist/cdn.min.js',
    'https://cdn.tailwindcss.com'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Cache rhyme/synonym lookups (API GET requests)
    if (url.pathname.startsWith('/api/rhyme/') || url.pathname.startsWith('/api/tools/lookup')) {
        event.respondWith(
            caches.open(CACHE_NAME).then((cache) => {
                return cache.match(event.request).then((cachedResponse) => {
                    const fetchPromise = fetch(event.request).then((networkResponse) => {
                        cache.put(event.request, networkResponse.clone());
                        return networkResponse;
                    });
                    return cachedResponse || fetchPromise;
                });
            })
        );
        return;
    }

    // Network first for everything else, fallback to cache
    event.respondWith(
        fetch(event.request).catch(() => {
            return caches.match(event.request);
        })
    );
});
