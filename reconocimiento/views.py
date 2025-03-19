import cv2
import requests
from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from scapy.all import ARP, Ether, srp
import json
import numpy as np
import os
import threading
import time
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import face_recognition
import socket
import queue
from .models import Person, DetectionEvent, Camera
from django.core.files.base import ContentFile
import asyncio
import websockets
from geopy.distance import geodesic
from cuentas.models import UserProfile
from django.core.mail import send_mail
from firebase_admin import messaging

def manifest(request):
    return JsonResponse({
        "name": "Mi PWA en Django",
        "short_name": "MiPWA",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#000000",
        "icons": [
            {
                "src": "/static/icons/icon-192x192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-512x512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    })


def home(request):
    cameras = Camera.objects.all()  
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

def is_camera(mac_address):
    try:
        camera = Camera.objects.get(mac_address=mac_address)
        camera_ip = camera.ip_address  
        return f"http://{camera_ip}:8080/video"
    except Camera.DoesNotExist:
        return None

def detect_cameras(request):
    local_ip = get_local_ip()  
    devices = scan_network(local_ip)  
    cameras_list = []

    for device in devices:
        mac = device['mac']
        ip = device['ip']
        print(f"Buscando cámara con MAC: {mac}")  
        try:

            camera = Camera.objects.get(mac_address__iexact=mac)
            print(f"Cámara encontrada: {camera}") 
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
            print(f"No se encontró cámara para MAC: {mac}") 
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

MEDIA_FACE_PATH = "media/faces/"

def save_face_image(frame, top, right, bottom, left):
    """ Guarda la imagen del rostro detectado """
    if not os.path.exists(MEDIA_FACE_PATH):
        os.makedirs(MEDIA_FACE_PATH)

    face_image = frame[top:bottom, left:right]
    _, buffer = cv2.imencode('.jpg', face_image)
    return buffer.tobytes()

def recognize_face(encoding, known_encodings):
    """ Compara el rostro detectado con los registrados """
    matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.6)
    return matches

class VideoStream(threading.Thread):
    def __init__(self, camera):
        super().__init__()
        self.camera = camera  
        self.camera_ip = camera.ip_address
        self.url = f"http://{self.camera_ip}:8080/video"
        self.running = True
        self.lock = threading.Lock()
        self.frame = None
        self.frame_queue = queue.Queue(maxsize=5)
        self.unknown_count = 0  
        self.processing_thread = threading.Thread(target=self.process_frames, daemon=True)
        self.processing_thread.start()

    def run(self):
        """ Hilo de captura de frames desde la cámara IP """
        try:
            stream = requests.get(self.url, stream=True, timeout=10)
            bytes_data = b""
            for chunk in stream.iter_content(chunk_size=1024):
                if not self.running:
                    break
                bytes_data += chunk

                while True:
                    a = bytes_data.find(b'\xff\xd8')  
                    b = bytes_data.find(b'\xff\xd9')  
                    if a != -1 and b != -1 and b > a:
                        jpg = bytes_data[a:b + 2]
                        bytes_data = bytes_data[b + 2:]
                        if len(jpg) > 100:
                            try:
                                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                            except cv2.error as e:
                                print(f"Error decodificando la imagen: {e}")
                                continue
                            if frame is not None:
                                frame = cv2.resize(frame, (640, 480))
                                try:
                                    self.frame_queue.put(frame, timeout=0.1)
                                except queue.Full:
                                    pass
                            else:
                                print("Advertencia: OpenCV no pudo decodificar el frame.")
                        else:
                            print("Advertencia: Frame JPEG demasiado pequeño, descartado.")
                    else:
                        break
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión con la cámara: {e}")
        except Exception as e:
            print(f"Error en transmisión: {e}")

    def process_frames(self):
        """ Procesa los frames, detecta rostros, anota la imagen y crea eventos de detección """
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=0.1)
                # Crear una copia para realizar las anotaciones sin afectar el frame original
                annotated_frame = frame.copy()
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame, model="hog")
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                # Cargar rostros registrados
                persons = list(Person.objects.all())
                known_encodings = []
                persons_with_encodings = []
                for p in persons:
                    if p.encodings:
                        known_encodings.append(np.array(p.encodings))
                        persons_with_encodings.append(p)

                for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
                    # Obtener imagen del rostro detectado
                    face_image = save_face_image(frame, top, right, bottom, left)
                    
                    # Comparar con la base de datos
                    matched = recognize_face(encoding, known_encodings)
                    if any(matched):
                        idx = matched.index(True)
                        matched_person = persons_with_encodings[idx]
                        print(f"🔴 Alerta: Se detectó a {matched_person.name}")
                        # Crear evento de detección para rostro reconocido
                        DetectionEvent.objects.create(
                            person=matched_person,
                            camera=self.camera,
                            image=ContentFile(face_image, name=f"{matched_person.id}_{int(time.time())}.jpg")
                        )
                        # Dibujar rectángulo verde y etiqueta con el nombre
                        cv2.rectangle(annotated_frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        cv2.putText(annotated_frame, matched_person.name, (left, top - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    else:
                        label = "Desconocido"
                        # Limitar a 10 fotos de rostros desconocidos
                        if self.unknown_count < 10:
                            print("⚠ Rostro no reconocido. Guardando foto y codificación...")
                            unknown_person = Person.objects.create(name=label)
                            unknown_person.photo.save(f"{unknown_person.id}.jpg", ContentFile(face_image))
                            # Guardar la codificación en el campo encodings (convertida a lista)
                            unknown_person.encodings = encoding.tolist()
                            unknown_person.save()
                            self.unknown_count += 1
                        else:
                            print("⚠ Rostro no reconocido. Límite de fotos alcanzado.")
                        # Crear evento de detección para rostro desconocido
                        DetectionEvent.objects.create(
                            person=None,
                            camera=self.camera,
                            image=ContentFile(face_image, name=f"desconocido_{int(time.time())}.jpg")
                        )
                        # Dibujar rectángulo rojo y etiqueta "Desconocido"
                        cv2.rectangle(annotated_frame, (left, top), (right, bottom), (0, 0, 255), 2)
                        cv2.putText(annotated_frame, label, (left, top - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                with self.lock:
                    self.frame = annotated_frame
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error en procesamiento de frames: {e}")

    def get_frame(self):
        """ Devuelve el frame procesado en formato JPEG """
        with self.lock:
            if self.frame is not None:
                _, buffer = cv2.imencode('.jpg', self.frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                return buffer.tobytes()
            return None

    def stop(self):
        self.running = False
        self.join()
        self.processing_thread.join()


stream_threads = {}

def camera_feed(request, camera_id):
    camera = get_object_or_404(Camera, id=camera_id)
    if camera.ip_address not in stream_threads:
        stream_threads[camera.ip_address] = VideoStream(camera)
        stream_threads[camera.ip_address].start()

    def generate():
        while True:
            frame = stream_threads[camera.ip_address].get_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
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


def camera_list(request):
    cameras = Camera.objects.all()
    return render(request, "reconocimiento/camera_list.html", {"cameras": cameras})

@csrf_exempt  
@require_POST
def register_and_set_default_camera(request):
    data = json.loads(request.body)
    mac = data.get('mac')
    ip = data.get('ip')
    name = data.get('name') or 'Cámara Detectada'
    location = data.get('location') or 'Desconocido'

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

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
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
    """Inicia la grabación de una cámara específica y alerta a usuarios cercanos"""
    print(f"✅ Recibida solicitud de grabación para la cámara {camera_id}")

    camera = get_object_or_404(Camera, id=camera_id)

    if camera_id in active_recordings:
        print("⚠ La cámara ya está grabando.")
        return JsonResponse({"error": "La cámara ya está grabando."}, status=400)

    print("🎥 Iniciando grabación...")
    recording_thread = threading.Thread(target=record_video, args=(camera.ip_address, 10, camera_id))
    recording_thread.start()
    active_recordings[camera_id] = recording_thread

    # Leer la geolocalización enviada desde el frontend
    body = json.loads(request.body)
    user_lat = body.get("latitude")
    user_lon = body.get("longitude")
    
    # Si la cámara no tiene ubicación, se usa la geolocalización del usuario
    if camera.latitude is None or camera.longitude is None:
        location = {
            "latitude": user_lat,
            "longitude": user_lon
        }
    else:
        location = {
            "latitude": camera.latitude,
            "longitude": camera.longitude
        }

    print(f"Usando ubicación: {location}")

    # 🔥 Enviar notificación a usuarios cercanos
    send_location_to_nearby_users(location)

    return JsonResponse({
        "message": "Grabación iniciada correctamente",
        "redirect_url": f"/recording_in_progress/{camera_id}/",
        "location": location
    })
def recording_in_progress(request, camera_id):
    camera = get_object_or_404(Camera, id=camera_id)
    return render(request, 'reconocimiento/recording_in_progress.html', {'camera': camera})


def send_location_to_nearby_users(camera_location):
    """Enviar alerta de grabación a usuarios cercanos (dentro de 1 km)"""
    print(f"Ejecutando send_location_to_nearby_users con ubicación: {camera_location}")
    
    users = UserProfile.objects.all()
    print(f"Usuarios totales en la base de datos: {len(users)}")
    
    nearby_users = []
    for user in users:
        if user.latitude and user.longitude:
            user_location = (user.latitude, user.longitude)
            distance = geodesic(user_location, (camera_location['latitude'], camera_location['longitude'])).km
            
            print(f"Usuario: {user.user.username} | Distancia: {distance} km")
            
            if distance <= 1:
                nearby_users.append(user)
    
    print(f"Usuarios cercanos detectados: {len(nearby_users)}")
    
    for user in nearby_users:
        print(f"Enviando notificación a {user.user.username}, Token: {user.fcm_token}")
        send_push_notification(user, "Alerta de Seguridad", "Una cámara cercana ha comenzado a grabar.")

def send_push_notification(user, title, message):
    """Enviar notificación push usando Firebase Cloud Messaging (FCM)"""
    if not user.fcm_token:
        print(f"Error: El usuario {user.user.username} no tiene un token FCM registrado.")
        return
    
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=message,
            ),
            token=user.fcm_token,
        )
        
        response = messaging.send(message)
        print(f"Notificación enviada a {user.user.username}: {response}")
    except Exception as e:
        print(f"Error al enviar notificación a {user.user.username}: {e}")

def send_push_notification(user, title, message):
    """Enviar notificación push usando Firebase Cloud Messaging (FCM)"""
    if not user.fcm_token:
        print(f"Error: El usuario {user.user.username} no tiene un token FCM registrado.")
        return
    
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=message,
            ),
            token=user.fcm_token,
        )
        
        response = messaging.send(message)
        print(f"Notificación enviada a {user.user.username}: {response}")
    except Exception as e:
        print(f"Error al enviar notificación a {user.user.username}: {e}")

@csrf_exempt
@login_required
def update_location(request):
    """Actualizar la ubicación del usuario en la base de datos en tiempo real"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_profile = request.user.userprofile  # Suponiendo que tienes un perfil de usuario

            user_profile.latitude = data.get("latitude")
            user_profile.longitude = data.get("longitude")
            user_profile.save()

            return JsonResponse({"message": "Ubicación actualizada correctamente"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)

