const CACHE_NAME = "39";
const FILES_TO_CACHE = [
  "./",
  "./index.html",
  "./manifest.json",
  "SE/C5Beep.wav",
  "SE/C6Beep.wav",
  "SE/E5Beep.wav",
  "SE/G5Beep.wav",
  "icons/icon-512.png",
  "icons/icon-192.png",
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

// 古いキャッシュを消す処理を追加
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      );
    })
  );
});