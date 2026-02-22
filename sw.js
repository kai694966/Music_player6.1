const CACHE_NAME = "v1";
const FILES_TO_CACHE = [
  "./",
  "./index.html",
  "./manifest.json",
];

// インストール（キャッシュ）
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(FILES_TO_CACHE);
    })
  );
});

// オフライン時の取得
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(resp => {
      return resp || fetch(event.request);
    })
  );
});
