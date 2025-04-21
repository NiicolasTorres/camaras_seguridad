async function getLocalIpPrefix() {
  return new Promise((resolve, reject) => {
    const pc = new RTCPeerConnection({ iceServers: [] });
    pc.createDataChannel('');
    pc.createOffer()
      .then(offer => pc.setLocalDescription(offer))
      .catch(err => reject(err));

    pc.onicecandidate = ({ candidate }) => {
      if (!candidate || !candidate.candidate) return;
      const m = candidate.candidate.match(/((?:\d{1,3}\.){3}\d{1,3})/);
      if (m) {
        pc.onicecandidate = null;
        pc.close();
        const parts = m[1].split('.');
        parts.pop();                
        resolve(parts.join('.'));  
      }
    };
  });
}
async function scanLan(prefix) {
  const found = [];
  const ips = Array.from({ length: 254 }, (_, i) => `${prefix}.${i + 1}`);

  await Promise.all(
    ips.map(ip => new Promise(resolve => {
      const img = new Image();
      img.onload = function() {
        found.push(ip);  
        resolve();
      };
      img.onerror = function() {
        resolve();  
      };
      img.src = `http://${ip}:8080/video`;  
    }))
  );

  return found;
}


async function startDetection() {
  let prefix;
  try {
    prefix = await getLocalIpPrefix();
  } catch (e) {
    console.error("No pude determinar tu IP local:", e);
    return;
  }

  const camsIps = await scanLan(prefix);
  if (!camsIps.length) {
    console.warn("No encontré cámaras en la red local.");
    return;
  }

  // 4) Enviás al servidor remoto para que chequee registro y devuelva datos
  try {
    const res = await fetch('/detect_cameras/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ips: camsIps })
    });
    const data = await res.json();
    console.log("Cámaras detectadas:", data.cameras);
  } catch (e) {
    console.error("Error enviando las IPs al backend:", e);
  }
}

function renderCameraList(cams) {
  const container = document.getElementById('camera-list');
  container.innerHTML = '';

  cams.forEach(cam => {
    const col = document.createElement('div');
    col.className = 'col-md-4 mt-3';
    col.innerHTML = `
      <div class="card">
        <img src="http://${cam.ip}:8080/video" class="card-img-top" alt="${cam.name}">
        <div class="card-body">
          <h5 class="card-title">${cam.name}</h5>
          <p class="card-text">IP: ${cam.ip}</p>
          <button class="btn btn-success" onclick="registerAndSetDefaultCamera(
            '${cam.mac}', '${cam.ip}', prompt('Nombre de cámara', '${cam.name}'), prompt('Ubicación', '${cam.location}')
          )">Registrar y usar</button>
        </div>
      </div>
    `;
    container.appendChild(col);
  });
}

// Registra en el servidor una cámara detectada y la marca como predeterminada
function registerAndSetDefaultCamera(mac, ip, name, location) {
  fetch('/register_and_set_default_camera/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({ mac, ip, name, location })
  })
  .then(response => response.json())
  .then(data => {
    alert(data.message);
    window.location.href = `/reconocimiento/camera_feed_template/${data.camera_id}/`;
  })
  .catch(error => {
    console.error('❌ Error al registrar y establecer cámara:', error);
    alert('Ocurrió un error al registrar la cámara.');
  });
}