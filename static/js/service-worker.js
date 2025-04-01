const CACHE_NAME = "django-pwa-cache-v1";
const urlsToCache = [
    "/static/js/bootstrap.bundle.min.js",
    "/static/js/recording-script.js",
    "/static/js/script.js",
    "/static/icons/icon-192x192.png",
    "/static/icons/icon-512x512.png",
    "/static/screenshots/desktop.png",
    "/static/screenshots/mobile.png"
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(urlsToCache);
        })
    );
});

self.addEventListener("fetch", (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});

self.addEventListener("notificationclick", function(event) {
    event.notification.close();
    const data = event.notification.data;
    if (data && data.latitude && data.longitude) {
        const googleMapsUrl = `https://www.google.com/maps?q=${data.latitude},${data.longitude}`;
        event.waitUntil(clients.openWindow(googleMapsUrl));
    } else {
        event.waitUntil(clients.openWindow('/'));
    }
});

self.addEventListener("activate", (event) => {
    const cacheWhitelist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (!cacheWhitelist.includes(cacheName)) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

self.addEventListener('push', function(event) {
    if (!event.data) {
      console.error("📛 No se recibieron datos en el evento push.");
      return;
    }
  
    const notificationData = event.data.json();
  
    event.waitUntil(
      self.registration.showNotification(notificationData.title || "Notificación", {
        body: notificationData.body || "Tienes una nueva alerta.",
        icon: "/static/icons/notification-icon.png",
        badge: "/static/icons/icon.png"
      })
    );
  });