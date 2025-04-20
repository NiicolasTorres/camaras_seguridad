function startDetection() {
    document.getElementById('status-message').innerText = 'Detectando cámaras en tu red local...';

    fetch('/reconocimiento/detect_cameras/', { 
        method: 'POST', 
        headers: { 
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken  
        },
        body: JSON.stringify({}) 
    })
    .then(response => response.json())
    .then(data => {
        console.log('Dispositivos detectados:', data);
        const cameraList = document.getElementById('camera-list');
        cameraList.innerHTML = '';

        if (!Array.isArray(data.cameras)) {
            console.error('data.cameras no es un arreglo');
            document.getElementById('status-message').innerText = 'No se encontraron cámaras.';
            return;
        }

        // Procesamos la respuesta y la mostramos
        data.cameras.forEach(camera => {
            const cameraItem = document.createElement('div');
            cameraItem.classList.add('col-md-6');
            cameraItem.innerHTML = `
                <h4>${camera.name} - ${camera.location}</h4>
                <p>IP: ${camera.ip}</p>
                <p>MAC: ${camera.mac}</p>
                <img src="${camera.url}" class="img-fluid border" width="100%">
                <button class="btn btn-success mt-2" onclick="setDefaultCamera(${camera.id})">
                    Usar como predeterminada
                </button>
            `;
            cameraList.appendChild(cameraItem);
        });

        document.getElementById('status-message').innerText = '¡Cámaras detectadas!';
    })
    .catch(error => {
        console.error('Error al detectar cámaras:', error);
        document.getElementById('status-message').innerText = 'Error al detectar cámaras en tu red local.';
    });
}

function setDefaultCamera(cameraId) {
    fetch(`/set_default_camera/${cameraId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ cameraId: cameraId })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        window.location.href = `/camera_feed/${cameraId}/`;
    })
    .catch(error => console.error('Error al establecer cámara:', error));
}

function registerAndSetDefaultCamera(mac, ip, name, location) {
    fetch('/register_and_set_default_camera/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ mac: mac, ip: ip, name: name, location: location })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        window.location.href = `/camera_feed/${data.camera_id}/`;
    })
    .catch(error => console.error('Error al registrar y establecer cámara:', error));
}
