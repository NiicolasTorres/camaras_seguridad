
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

// Función para verificar y procesar la respuesta del servidor
async function handleResponse(response) {
    if (!response.ok) {
        const errorText = await response.text();
        console.error("Error en la respuesta del servidor:", errorText);
        return null;
    }
    try {
        const data = await response.json();
        console.log("Respuesta recibida:", data);
        return data;
    } catch (error) {
        console.error("Error parseando JSON:", error);
        return null;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    let watchId;

    function stopTrackingLocation() {
        if (watchId) {
            navigator.geolocation.clearWatch(watchId);
            console.log("Seguimiento detenido antes de grabar.");
        }
    }

    function trackUserLocation() {
        if (navigator.geolocation) {
            watchId = navigator.geolocation.watchPosition(
                position => {
                    const latitude = position.coords.latitude;
                    const longitude = position.coords.longitude;
                    console.log("Nueva ubicación: " + latitude + ", " + longitude);
                    sendLocation(latitude, longitude);
                },
                error => {
                    console.error("Error al obtener geolocalización:", error);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 5000
                }
            );
        } else {
            console.error("Geolocalización no soportada en este navegador.");
        }
    }

    const updateLocationUrl = "/update_location/";

    function sendLocation(latitude, longitude) {
        console.log("Enviando ubicación:", latitude, longitude);  // <-- Agregado para debug
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
            console.log("Ubicación actualizada en el servidor:", data);
        })
        .catch(error => {
            console.error("Error al enviar la ubicación:", error);
        });
    }
    

    document.querySelectorAll('.start-recording').forEach(button => {
        button.addEventListener('click', async function(event) {
            event.preventDefault();
            const cameraId = button.getAttribute('data-camera-id');
            const url = button.getAttribute('data-url');
            console.log("Iniciando grabación para cámara " + cameraId + " en " + url);
            const csrfToken = getCSRFToken();
            console.log("CSRF Token: " + csrfToken);
            stopTrackingLocation();
            setTimeout(async () => {
                try {
                    const position = await new Promise((resolve, reject) => {
                        if (navigator.geolocation) {
                            navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 10000 });
                        } else {
                            reject('Geolocalización no soportada en este navegador.');
                        }
                    });
                    const latitude = position.coords.latitude;
                    const longitude = position.coords.longitude;
                    console.log("Geolocalización obtenida: Latitud " + latitude + ", Longitud " + longitude);
                    
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
                    
                    // Utilizamos la función handleResponse para procesar la respuesta
                    const data = await handleResponse(response);
                    if (data && response.ok) {
                        console.log("Redirigiendo a: " + data.redirect_url);
                        window.location.href = `/ubicacion/?latitude=${camera.latitude}&longitude=${camera.longitude}`;


                    } else {
                        console.error("Error en la respuesta:", data ? data.error : 'Respuesta inválida');
                        alert(data && data.error ? data.error : 'Hubo un error al iniciar la grabación');
                    }
                    
                } catch (error) {
                    console.error('Error en la petición:', error);
                    alert('Hubo un error al intentar grabar o al obtener la geolocalización.');
                }
            }, 500);
        });
    });

    trackUserLocation();
});

async function verificarSuscripcion() {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
  
    if (subscription) {
      console.log('Usuario suscrito:', subscription);
      // Envía al backend para verificar la suscripción
      fetch('/verificar-suscripcion/', {
        method: 'POST',
        body: JSON.stringify({ endpoint: subscription.endpoint }),
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        }
      })
      .then(response => response.json())
      .then(data => {
        if (data.suscrito) {
          console.log('La suscripción es válida.');
        } else {
          console.log('La suscripción no es válida en el backend.');
        }
      });
    } else {
      console.log('El usuario no está suscrito.');
    }
}

function showLocationOnMap(latitude, longitude) {
    const map = new google.maps.Map(document.getElementById('map'), {
        center: { lat: latitude, lng: longitude },
        zoom: 15
    });

    new google.maps.marker.AdvancedMarkerElement({
        position: { lat: latitude, lng: longitude },
        map: map,
        title: "Tu ubicación"
    });
}
