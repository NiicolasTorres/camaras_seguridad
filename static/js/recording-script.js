document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.start-recording').forEach(button => {
        button.addEventListener('click', async function(event) {
            event.preventDefault();

            const cameraId = button.getAttribute('data-camera-id');
            const url = button.getAttribute('data-url');

            console.log(`🎬 Iniciando grabación para cámara ${cameraId} en ${url}`);

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

            const csrfToken = getCSRFToken();
            console.log(`🛡 CSRF Token: ${csrfToken}`);

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({})
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
                alert('Hubo un error al intentar grabar.');
            }
        });
    });
});
