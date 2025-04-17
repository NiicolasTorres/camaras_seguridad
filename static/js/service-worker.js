const CACHE_NAME = "django-pwa-cache-v1";
const urlsToCache = [
    "/static/js/bootstrap.bundle.min.js",
    "/static/js/recording-script.js",
    "/static/js/script.js",
    "/static/icons/icon-192x192.png",
    "/static/icons/icon-512x512.png",
    "/static/icons/icon.png",
    "/static/screenshots/desktop.png",
    "/static/screenshots/mobile.png"
];

// Instalación del Service Worker
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(urlsToCache);
        })
    );
});

// Interceptar fetch
self.addEventListener("fetch", (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});

// Activación del Service Worker
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

// Notificación Push recibida
self.addEventListener("push", function(event) {
  console.log("🔔 Push recibido en el Service Worker:", event.data);

  if (!event.data) {
    console.warn("❌ No se recibió contenido en el Push.");
    return;
  }

  const showNotification = async () => {
    let data = {};

    try {
      data = JSON.parse(event.data.text());
    } catch (e) {
      console.warn("⚠️ El contenido no es JSON. Usando texto plano.");
      data = { title: "📢 Notificación", body: event.data.text() };
    }

    console.log("📨 Datos de la notificación:", data);

    return self.registration.showNotification(data.title || "📢 Notificación", {
      body: data.body || "Tenés una nueva alerta",
      icon: "/static/icons/icon.png",
      data: {
        latitude: data.latitude,
        longitude: data.longitude
      }
    });
  };

  event.waitUntil(showNotification());
});



// Click en la notificación
self.addEventListener("notificationclick", function(event) {
  event.notification.close();

  const latitude = event.notification.data?.latitude;
  const longitude = event.notification.data?.longitude;

  // Redirigir a Google Maps con la ubicación
  const url = `https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`;

  event.waitUntil(
    clients.matchAll({ type: "window" }).then(function(clientList) {
      for (const client of clientList) {
        if (client.url === url && "focus" in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});