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

// Escanea la LAN probando cada IP en el puerto 8080/video
async function scanLan(prefix) {
  const found = [];
  const ips = Array.from({ length: 254 }, (_, i) => `${prefix}.${i + 1}`);

  await Promise.all(
    ips.map(ip => new Promise(resolve => {
      const img = new Image();
      let done = false;

      img.onload = () => {
        if (!done) {
          done = true;
          found.push(ip);
        }
        resolve();
      };
      img.onerror = () => {
        done = true;
        resolve();
      };

      img.src = `http://${ip}:8080/video`;

      // timeout para no colgar el Promise
      setTimeout(() => {
        if (!done) {
          done = true;
          resolve();
        }
      }, 800);
    }))
  );

  return found;
}

// Inicia todo el flujo de detección y renderizado
async function startDetection() {
  const status = document.getElementById('status-message');
  status.innerText = '🔍 Escaneando tu red local…';

  let prefix;
  try {
    prefix = await getLocalIpPrefix();
  } catch {
    // Fallback manual
    prefix = prompt('No se pudo obtener tu IP local automáticamente.\nPor favor ingresa el prefijo de tu red (ej. 192.168.1):');
    if (!prefix) {
      status.innerText = '❌ Se requiere el prefijo de red para escanear.';
      return;
    }
  }

  const ips = await scanLan(prefix);
  if (!ips.length) {
    status.innerText = '😕 No encontré ninguna cámara en tu red.';
    return;
  }

  // Opcional: registra en el servidor las IPs encontradas
  const res = await fetch('/reconocimiento/detect_cameras/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({ ips })
  });
  const data = await res.json();

  renderCameraList(data.cameras);
  status.innerText = '✅ Detección finalizada.';
}

// Renderiza las cámaras detectadas dinámicamente en el DOM
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