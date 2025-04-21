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
  const timeouts = [];
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

      timeouts.push(setTimeout(() => {
        if (!done) {
          done = true;
          resolve();
        }
      }, 1000));
    }))
  );

  timeouts.forEach(clearTimeout);
  return found;
}

async function startDetection() {
  document.getElementById('status-message').innerText = '🔍 Escaneando tu red local…';
  let prefix;
  try {
    prefix = await getLocalIpPrefix();
  } catch {
    document.getElementById('status-message').innerText = 'Error al obtener IP local.';
    return;
  }

  const ipsDetectadas = await scanLan(prefix);
  if (!ipsDetectadas.length) {
    document.getElementById('status-message').innerText = '😕 No se encontraron cámaras.';
    return;
  }

  const res = await fetch('/reconocimiento/detect_cameras/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
    body: JSON.stringify({ ips: ipsDetectadas })
  });
  const data = await res.json();
  renderCameraList(data.cameras);
  document.getElementById('status-message').innerText = '✅ Detección finalizada.';
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
      .catch(error => console.error('❌ Error al establecer cámara:', error));
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
      .catch(error => console.error('❌ Error al registrar y establecer cámara:', error));
}
