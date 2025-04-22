function registerAndSetDefaultCamera(mac, ip, name, location) {
  fetch('/reconocimiento/register_and_set_default_camera/', {
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
    window.location.href = '/home/'; 
  })
  .catch(() => alert('❌ Error al registrar la cámara.'));
}
