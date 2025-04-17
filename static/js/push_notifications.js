async function subscribeUserToPush() {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    console.error("⛔ Las Notificaciones Push no son compatibles con este navegador.");
    return;
  }

  try {
    const registration = await navigator.serviceWorker.register('/static/js/service-worker.js');
    let subscription = await registration.pushManager.getSubscription();

    if (subscription) {
      console.log("🔄 Eliminando suscripción anterior...");
      await subscription.unsubscribe();
    }

    const response = await fetch('/vapid_public_key/');
    if (!response.ok) {
      throw new Error(`⛔ Error al obtener la clave VAPID: ${response.status}`);
    }
    const data = await response.json();

    if (!data.publicKey) {
      throw new Error("⛔ La clave pública VAPID es undefined.");
    }

    const vapidPublicKey = data.publicKey;
    const convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey);

    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: convertedVapidKey
    });

    console.log("✅ Suscripción creada con éxito.");

    const subscriptionJson = subscription.toJSON();
    console.log("Suscripción (JSON):", subscriptionJson);

    const saveResponse = await fetch('/save_subscription/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      },
      body: JSON.stringify(subscriptionJson)
    });

    if (!saveResponse.ok) {
      throw new Error("⛔ Error al guardar la suscripción.");
    }

    console.log("✅ Suscripción guardada correctamente en el servidor.");
  } catch (error) {
    console.error(error.message);
  }
}

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

function getCSRFToken() {
  const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");
  return csrfToken ? csrfToken.value : '';
}

document.addEventListener("DOMContentLoaded", async () => {
  if (Notification.permission === "granted") {
    await subscribeUserToPush();
  } else if (Notification.permission === "default") {
    const permission = await Notification.requestPermission();
    if (permission === "granted") {
      await subscribeUserToPush();
    }
  } else {
    console.warn("⚠️ El usuario ha bloqueado las notificaciones.");
  }
});
