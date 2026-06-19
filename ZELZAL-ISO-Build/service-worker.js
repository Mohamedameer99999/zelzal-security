const CACHE = 'zelzal-v1';
const ASSETS = [
  '/zelzal-security/',
  '/zelzal-security/index.html',
  '/zelzal-security/manifest.json',
  '/zelzal-security/icons/shield-192.svg',
  '/zelzal-security/icons/shield-512.svg',
  '/zelzal-security/payment.html',
  '/zelzal-security/guide.html',
  '/zelzal-security/qr-code.png'
];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(clients.claim());
});
self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request).then(res => {
      if (res.ok) {
        const clone = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
      }
      return res;
    }).catch(() => caches.match('/zelzal-security/')))
  );
});
