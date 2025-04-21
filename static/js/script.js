function getLocalIpPrefix() {
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
      ips.map(ip =>
        new Promise(resolve => {
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
  
          // timeout de 1s
          timeouts.push(setTimeout(() => {
            if (!done) {
              done = true;
              resolve();
            }
          }, 1000));
  
          img.src = `/proxy_camera/?ip=${ip}`;
        })
      )
    );
  
    timeouts.forEach(clearTimeout);
    return found;
  }
  
  async function startDetection() {
    document.getElementById('status-message').innerText = 'Escaneando tu red local…';
  
    let prefix;
    try {
      prefix = await getLocalIpPrefix();
    } catch (e) {
      console.error('No pude obtener tu IP local:', e);
      document.getElementById('status-message').innerText = 'Error al obtener IP local.';
      return;
    }
  
    const ipsDetectadas = await scanLan(prefix);
    if (ipsDetectadas.length === 0) {
      document.getElementById('status-message').innerText = 'No se encontraron cámaras.';
      return;
    }
  
    // 4) Envío al servidor para ver cuáles están registradas
    fetch('/reconocimiento/detect_cameras/', {
      method:  'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken':  csrftoken
      },
      body: JSON.stringify({ ips: ipsDetectadas })
    })
      .then(res => res.json())
      .then(data => {
        const cameraList = document.getElementById('camera-list');
        cameraList.innerHTML = '';
        data.cameras.forEach(cam => {
          const div = document.createElement('div');
          div.classList.add('col-md-6');
          div.innerHTML = `
            <h4>${cam.name} — ${cam.location}</h4>
            <p>IP: ${cam.ip}</p>
            <p>MAC: ${cam.mac || '—'}</p>
            <img src="${cam.url}" class="img-fluid border" width="100%">
            <button class="btn btn-success mt-2"
                    onclick="setDefaultCamera(${cam.id || 'null'})">
              Usar como predeterminada
            </button>
          `;
          cameraList.appendChild(div);
        });
        document.getElementById('status-message').innerText = '¡Detección finalizada!';
      })
      .catch(err => {
        console.error(err);
        document.getElementById('status-message').innerText = 'Error al contactar al servidor.';
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
