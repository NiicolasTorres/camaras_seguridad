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
function startDetection() {
  document.getElementById("status-message").innerText = "🔍 Buscando cámaras en la red local...";
  console.log("✅ startDetection() llamada");

  let prefix;
  getLocalIpPrefix()
    .then(prefix => {
      console.log("📡 Prefijo de IP detectado:", prefix);

      return scanLan(prefix);
    })
    .then(camsIps => {
      console.log("🔎 IPs con cámara detectadas:", camsIps);

      if (!camsIps.length) {
        document.getElementById("status-message").innerText = "No se encontraron cámaras.";
        return;
      }
      return fetch('/detect_cameras/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ips: camsIps })
      });
    })
    .then(res => res.json())
    .then(data => {
      console.log("📦 Respuesta del backend:", data);
      renderCameraList(data.cameras);
      document.getElementById("status-message").innerText = `🎥 Se detectaron ${data.cameras.length} cámara(s).`;
    })
    .catch(e => {
      console.error("❌ Error detectando cámaras:", e);
      document.getElementById("status-message").innerText = "Error al contactar con el servidor.";
    });
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