document.addEventListener('DOMContentLoaded', () => {
  const statusEl = document.getElementById('status-message');
  const detectBtn = document.querySelector('button[onclick="startDetection()"]');
  const listEl = document.getElementById('camera-list');

  detectBtn.addEventListener('click', startDetection);

async function getPublicIp() {
  const response = await fetch('https://api.ipify.org?format=json');
  const data = await response.json();
  return data.ip;
}

async function scanLan(prefix) {
  const found = [];
  const ports = [8080, 8081, 80]; 
  for (let i = 1; i <= 254; i++) {
    const ip = `${prefix}.${i}`;
    for (const port of ports) {
      try {
        const res = await fetch(`http://${ip}:${port}/video`, { timeout: 5000 });
        if (res.ok) {
          found.push(ip);
          break;
        }
      } catch (e) {
      }
    }
  }
  return found;
}

async function startDetection() {
  console.log('Iniciando detección...');
  statusEl.innerText = '🔍 Buscando cámaras en la red local...';
  detectBtn.disabled = true;
  listEl.innerHTML = '';

  let publicIp;
  try {
    publicIp = await getPublicIp(); 
  } catch {
    statusEl.innerText = '❌ No pude determinar tu IP pública.';
    detectBtn.disabled = false;
    return;
  }

  const prefix = publicIp.split('.').slice(0, 3).join('.');  
  const camsIps = await scanLan(prefix);
  
  if (!camsIps.length) {
    statusEl.innerText = '⚠️ No se encontraron cámaras.';
    detectBtn.disabled = false;
    return;
  }

  let data;
  try {
    const res = await fetch('/detect_cameras/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify({ ips: camsIps })
    });
    data = await res.json();
  } catch {
    statusEl.innerText = '❌ Error al contactar al servidor.';
    detectBtn.disabled = false;
    return;
  }

  data.cameras.forEach(cam => {
    const card = document.createElement('div');
    card.className = 'col-md-4 mt-3';
    card.innerHTML = `
      <div class="card">
        <img src="http://${cam.ip}:8080/photo.jpg" class="card-img-top" alt="${cam.name}">
        <div class="card-body">
          <h5 class="card-title">${cam.name}</h5>
          <p class="card-text">IP: ${cam.ip}</p>
          <button class="btn btn-success" onclick="registerAndSetDefaultCamera(
            '${cam.mac || ''}', 
            '${cam.ip}', 
            prompt('Nombre de cámara', '${cam.name}'),
            prompt('Ubicación', '${cam.location}')
          )">Registrar y usar</button>
        </div>
      </div>
    `;
    listEl.appendChild(card);
  });

  statusEl.innerText = `🎥 Se detectaron ${data.cameras.length} cámara(s).`;
  detectBtn.disabled = false;
}
function registerAndSetDefaultCamera(mac, ip, name, location) {
  fetch('/register_and_set_default_camera/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({ mac, ip, name, location })
  })
  .then(r => r.json())
  .then(d => {
    alert(d.message);
    window.location.href = `/reconocimiento/camera_feed_template/${d.camera_id}/`;
  })
  .catch(() => alert('❌ Error al registrar la cámara.'));
}

detectBtn.addEventListener('click', startDetection);
});