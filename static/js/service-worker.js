const CACHE_NAME = "django-pwa-cache-v1";
const urlsToCache = [
    "/",
    "/static/css/styles.css",
    "/static/js/script.js",
    "/static/icons/icon-192x192.png",
    "/static/icons/icon-512x512.png",
    "/static/screenshots/desktop.png",
    "/static/screenshots/mobile.png"
];

// Obtener el token FCM
firebase.messaging().getToken({ vapidKey: '<VAPID_KEY>' }).then(function(token) {
    // Enviar el token al backend
    fetch('/update_fcm_token/', {
      method: 'POST',
      body: JSON.stringify({ fcm_token: token }),
      headers: { 'Content-Type': 'application/json' }
    });
  });
  

// Instalación del Service Worker y cacheo de recursos
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(urlsToCache);
        })
    );
});

// Manejo de las peticiones de red
self.addEventListener("fetch", (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});

// Registro de notificaciones push
self.addEventListener('push', function(event) {
    const data = event.data ? event.data.json() : {};
    const title = data.notification ? data.notification.title : 'Notificación';
    const options = {
        body: data.notification ? data.notification.body : 'Contenido de la notificación',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/icon-512x512.png',
        data: {
            // Suponiendo que los datos contienen latitud y longitud
            latitude: data.latitude,
            longitude: data.longitude
        }
    };

    // Mostrar la notificación
    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Manejo de la acción al hacer clic en la notificación
self.addEventListener('notificationclick', function(event) {
    event.notification.close();

    // Obtener la latitud y longitud desde los datos de la notificación
    const data = event.notification.data;
    const latitude = data ? data.latitude : null;
    const longitude = data ? data.longitude : null;

    if (latitude && longitude) {
        // Construir la URL de Google Maps con las coordenadas
        const googleMapsUrl = `https://www.google.com/maps?q=${latitude},${longitude}`;
        
        // Intentar redirigir al usuario a Google Maps
        event.waitUntil(
            clients.openWindow(googleMapsUrl).then(function(client) {
                if (client) {
                    client.focus();
                }
            }).catch((error) => {
                console.error("Error al abrir Google Maps:", error);
            })
        );
    } else {
        // Si no hay coordenadas, redirigir a la página principal (o cualquier otra página de fallback)
        event.waitUntil(
            clients.openWindow('/').then(function(client) {
                if (client) {
                    client.focus();
                }
            }).catch((error) => {
                console.error("Error al abrir la ventana de fallback:", error);
            })
        );
    }
});


// Activación del Service Worker
self.addEventListener("activate", (event) => {
    var cacheWhitelist = [CACHE_NAME];
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

