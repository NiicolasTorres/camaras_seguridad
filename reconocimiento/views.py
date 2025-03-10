import cv2
import requests
from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Camera
from scapy.all import ARP, Ether, srp
import json
import numpy as np
from .models import Camera
import os
import threading
import time
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.http import require_POST
import face_recognition
import socket

def home(request):
    cameras = Camera.objects.all()  # Obtener todas las cámaras
    return render(request, 'home.html', {'cameras': cameras})

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(('10.254.254.254', 1))
        local_ip = s.getsockname()[0]
    except:
        local_ip = '191.85.30.52'
    finally:
        s.close()
    return local_ip

# Función para escanear la red y encontrar dispositivos
def scan_network(local_ip):
    ip_parts = local_ip.split('.')
    network_range = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
    
    devices = []
    arp_request = ARP(pdst=network_range)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast / arp_request

    answered_list = srp(arp_request_broadcast, timeout=1, verbose=False)[0]
    for element in answered_list:
        ip = element[1].psrc
        mac = element[1].hwsrc
        devices.append({'ip': ip, 'mac': mac})
    
    return devices
# Función para verificar si una IP es una cámara IP
def is_camera(mac_address):
    try:
        camera = Camera.objects.get(mac_address=mac_address)
        camera_ip = camera.ip_address  # Usar la última IP conocida
        # Simplemente se construye la URL sin intentar conectar
        return f"http://{camera_ip}:8080/video"
    except Camera.DoesNotExist:
        return None

def detect_cameras(request):
    local_ip = get_local_ip()  # Obtener la IP local
    devices = scan_network(local_ip)  # Escanear la red
    cameras_list = []

    for device in devices:
        mac = device['mac']
        ip = device['ip']
        print(f"Buscando cámara con MAC: {mac}")  # Depuración
        try:
            # Búsqueda insensible a mayúsculas
            camera = Camera.objects.get(mac_address__iexact=mac)
            print(f"Cámara encontrada: {camera}")  # Depuración
            camera_url = f"http://{camera.ip_address}:8080/video"
            cameras_list.append({
                "id": camera.id,
                "name": camera.name,
                "location": camera.location,
                "mac": camera.mac_address,
                "ip": camera.ip_address,
                "url": camera_url,
                "registered": True
            })
        except Camera.DoesNotExist:
            print(f"No se encontró cámara para MAC: {mac}")  # Depuración
            # Agregar el dispositivo detectado aunque no esté registrado
            camera_url = f"http://{ip}:8080/video"
            cameras_list.append({
                "id": None,
                "name": "Cámara no registrada",
                "location": "Desconocido",
                "mac": mac,
                "ip": ip,
                "url": camera_url,
                "registered": False
            })

    return JsonResponse({'cameras': cameras_list})

# Guarda una cámara como predeterminada
def set_default_camera(request, camera_id):
    try:
        camera = Camera.objects.get(id=camera_id)
        camera.is_default = True
        camera.save()
        return JsonResponse({"message": f"Cámara {camera.name} marcada como predeterminada."})
    except Camera.DoesNotExist:
        return JsonResponse({"error": "Cámara no encontrada"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# Obtiene la cámara predeterminada y transmite video
def camera_feed(request, camera_id):
    camera = get_object_or_404(Camera, id=camera_id)
    camera_ip = camera.ip_address

    if camera_ip not in stream_threads:
        stream_threads[camera_ip] = VideoStream(camera_ip)
        stream_threads[camera_ip].start()

    def generate():
        while True:
            frame = stream_threads[camera_ip].get_frame()
            if frame:
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.03)

    return StreamingHttpResponse(generate(), content_type='multipart/x-mixed-replace; boundary=frame')


# Transmisión de video con detección facial
class VideoStream(threading.Thread):
    def __init__(self, camera_ip):
        super().__init__()
        self.camera_ip = camera_ip
        self.url = f"http://{camera_ip}:8080/video"
        self.running = True
        self.lock = threading.Lock()
        self.frame = None

    def run(self):
        try:
            stream = requests.get(self.url, stream=True, timeout=10)
            bytes_data = b""
            for chunk in stream.iter_content(chunk_size=4096):
                if not self.running:
                    break
                bytes_data += chunk
                a = bytes_data.find(b'\xff\xd8')
                b = bytes_data.find(b'\xff\xd9')
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b + 2]
                    bytes_data = bytes_data[b + 2:]
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        frame = cv2.resize(frame, (640, 480))
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        face_locations = face_recognition.face_locations(rgb_frame)
                        for (top, right, bottom, left) in face_locations:
                            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        with self.lock:
                            self.frame = frame
        except Exception as e:
            print(f"Error en transmisión: {e}")

    def get_frame(self):
        with self.lock:
            if self.frame is not None:
                _, buffer = cv2.imencode('.jpg', self.frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                return buffer.tobytes()
            return None

    def stop(self):
        self.running = False

stream_threads = {}

# Vista para mostrar la transmisión de video en vivo de la cámara predeterminada
def camera_feed(request, camera_id):
    camera = get_object_or_404(Camera, id=camera_id)
    camera_ip = camera.ip_address

    if camera_ip not in stream_threads:
        stream_threads[camera_ip] = VideoStream(camera_ip)
        stream_threads[camera_ip].start()

    def generate():
        while True:
            frame = stream_threads[camera_ip].get_frame()
            if frame:
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.03)

    return StreamingHttpResponse(generate(), content_type='multipart/x-mixed-replace; boundary=frame')

def stop_camera_feed(camera_ip):
    if camera_ip in stream_threads:
        stream_threads[camera_ip].stop()
        stream_threads[camera_ip].join()
        del stream_threads[camera_ip]


def camera_feed_template(request, camera_id):
    try:
        camera = Camera.objects.get(id=camera_id)
        return render(request, 'reconocimiento/camera_feed.html', {'camera': camera})
    except Camera.DoesNotExist:
        return JsonResponse({"error": "No se encontró la cámara."}, status=404)


# Vista para mostrar la lista de cámaras disponibles
def camera_list(request):
    cameras = Camera.objects.all()
    return render(request, "reconocimiento/camera_list.html", {"cameras": cameras})

@csrf_exempt  # O usa @csrf_protect y envía el token desde JS
@require_POST
def register_and_set_default_camera(request):
    data = json.loads(request.body)
    mac = data.get('mac')
    ip = data.get('ip')
    # Puedes usar valores por defecto o incluso solicitar al usuario que los complete
    name = data.get('name') or 'Cámara Detectada'
    location = data.get('location') or 'Desconocido'
    
    # Crea el registro en la BD (asumiendo que el modelo Camera tiene el campo is_default)
    camera = Camera.objects.create(
        name=name,
        location=location,
        mac_address=mac,
        ip_address=ip,
        active=True
    )
    camera.is_default = True
    camera.save()
    
    return JsonResponse({
        "message": f"Cámara {camera.name} registrada y marcada como predeterminada.",
        "camera_id": camera.id
    })

# Grabar video
VIDEO_SAVE_PATH = "media/videos/"
active_recordings = {}

def record_video(camera_ip, duration=10, camera_id=None):
    if not os.path.exists(VIDEO_SAVE_PATH):
        os.makedirs(VIDEO_SAVE_PATH)

    video_filename = os.path.join(VIDEO_SAVE_PATH, f"recording_{camera_id}_{int(time.time())}.mp4")
    cap = cv2.VideoCapture(f"http://{camera_ip}:8080/video")

    if not cap.isOpened():
        print(f"Error: No se pudo abrir la cámara {camera_ip}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if width == 0 or height == 0:
        print("Error: No se pudo obtener el tamaño del frame.")
        cap.release()
        return

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(video_filename, fourcc, 20.0, (width, height))

    if not out.isOpened():
        print("Error: No se pudo inicializar el VideoWriter.")
        cap.release()
        return

    start_time = time.time()

    while time.time() - start_time < duration:
        ret, frame = cap.read()
        if not ret:
            print("Error: No se pudo leer el frame de la cámara.")
            break
        out.write(frame)

    cap.release()
    out.release()
    print(f"Grabación guardada: {video_filename}")

    active_recordings.pop(camera_id, None)

@csrf_protect
@require_POST
def start_recording(request, camera_id):
    """Inicia la grabación de una cámara específica"""
    print(f"✅ Recibida solicitud de grabación para la cámara {camera_id}")

    camera = get_object_or_404(Camera, id=camera_id)

    if camera_id in active_recordings:
        print("⚠ La cámara ya está grabando.")
        return JsonResponse({"error": "La cámara ya está grabando."}, status=400)

    print("🎥 Iniciando grabación...")
    recording_thread = threading.Thread(target=record_video, args=(camera.ip_address, 10, camera_id))
    recording_thread.start()

    active_recordings[camera_id] = recording_thread

    print(f"🔄 Redirigiendo a: /recording_in_progress/{camera_id}/")
    return JsonResponse({
        "message": "Grabación iniciada correctamente",
        "redirect_url": f"/recording_in_progress/{camera_id}/"
    })

def recording_in_progress(request, camera_id):
    camera = get_object_or_404(Camera, id=camera_id)
    return render(request, 'reconocimiento/recording_in_progress.html', {'camera': camera})