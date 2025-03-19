// Obtener CSRF Token desde las cookies
function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith('csrftoken=')) {
                cookieValue = cookie.substring('csrftoken='.length, cookie.length);
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.start-recording').forEach(button => {
        button.addEventListener('click', async function(event) {
            event.preventDefault();

            const cameraId = button.getAttribute('data-camera-id');
            const url = button.getAttribute('data-url');

            console.log(`🎬 Iniciando grabación para cámara ${cameraId} en ${url}`);

            const csrfToken = getCSRFToken();
            console.log(`🛡 CSRF Token: ${csrfToken}`);

            // Obtener geolocalización
            function getGeolocation() {
                return new Promise((resolve, reject) => {
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(resolve, reject, {timeout: 10000});
                    } else {
                        reject('Geolocalización no soportada en este navegador.');
                    }
                });
            }

            try {
                const position = await getGeolocation();
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;
                console.log(`🌍 Geolocalización obtenida: Latitud ${latitude}, Longitud ${longitude}`);

                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        cameraId: cameraId,
                        latitude: latitude,
                        longitude: longitude
                    })
                });

                const data = await response.json();

                console.log("📩 Respuesta del servidor:", data);

                if (response.ok) {
                    console.log(`✅ Redirigiendo a: ${data.redirect_url}`);
                    window.location.href = data.redirect_url; 
                } else {
                    console.error(`⚠ Error: ${data.error}`);
                    alert(data.error || 'Hubo un error al iniciar la grabación');
                }
            } catch (error) {
                console.error('❌ Error en la petición:', error);
                alert('Hubo un error al intentar grabar o al obtener la geolocalización.');
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // URL del servidor para actualizar la ubicación
    const updateLocationUrl = "/update_location/";

    function sendLocation(latitude, longitude) {
        fetch(updateLocationUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ latitude, longitude })
        })
        .then(response => response.json())
        .then(data => {
            console.log("📍 Ubicación actualizada en el servidor:", data);
        })
        .catch(error => {
            console.error("❌ Error al enviar la ubicación:", error);
        });
    }

    function trackUserLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.watchPosition(
                position => {
                    const latitude = position.coords.latitude;
                    const longitude = position.coords.longitude;
                    console.log(`🌍 Nueva ubicación: ${latitude}, ${longitude}`);

                    // Enviar ubicación cada 10 segundos
                    sendLocation(latitude, longitude);
                },
                error => {
                    console.error("⚠ Error al obtener geolocalización:", error);
                },
                {
                    enableHighAccuracy: true, // Usa GPS si es posible
                    timeout: 20000,           // Espera máximo 10 segundos
                    maximumAge: 5000          // Usa ubicación reciente si está disponible
                }
            );
        } else {
            console.error("🚫 Geolocalización no soportada en este navegador.");
        }
    }

    // Iniciar la actualización de ubicación
    trackUserLocation();
});
