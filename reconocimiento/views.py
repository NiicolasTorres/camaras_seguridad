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
from django.views.decorators.http import require_POST, require_GET
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
from pywebpush import webpush, WebPushException
from django.conf import settings
from py_vapid import Vapid
from cryptography.hazmat.primitives import serialization
from cuentas.utils import generate_or_load_vapid_keys
from geopy.geocoders import Nominatim
from django.http import FileResponse, Http404
from datetime import datetime
import csv
from django.http import HttpResponse
import scapy.all as scapy

def manifest(request):
    return JsonResponse({
        "name": "Seguridad con SilentEye",
        "short_name": "SilentEye",
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
    if request.user.is_authenticated:
        user_profile = UserProfile.objects.filter(user=request.user).first()  
        cameras = user_profile.cameras.all() if user_profile else []  

        for camera in cameras:
            if camera.latitude is None or camera.longitude is None:
                camera.latitude = 0  
                camera.longitude = 0  

    else:
        cameras = []

    return render(request, 'home.html', {'cameras': cameras})

def scan_network(client_ip):
    ip_parts = client_ip.split('.')
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
        return camera 
    except Camera.DoesNotExist:
        return None


def detect_cameras(request):
    if request.method == 'POST':
        client_ip = request.META.get('REMOTE_ADDR')  

        devices = scan_network(client_ip)  

        cameras_list = []
        for device in devices:
            mac = device['mac']
            camera = is_camera(mac)  
            if camera:
                cameras_list.append({
                    'id': camera.id,
                    'name': camera.name,
                    'location': camera.location,
                    'mac': camera.mac_address,
                    'ip': camera.ip_address,
                    'url': f"http://{camera.ip_address}:8080/video",
                    'registered': True
                })
            else:
                cameras_list.append({
                    'id': None,
                    'name': 'Cámara no registrada',
                    'location': 'Desconocido',
                    'mac': mac,
                    'ip': device['ip'],
                    'url': f'http://{device["ip"]}:8080/video',
                    'registered': False
                })

        return JsonResponse({'cameras': cameras_list})

    return JsonResponse({'error': 'Método no permitido'}, status=405)

def set_default_camera(request, camera_id):
    try:
        camera = Camera.objects.get(id=camera_id)
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        user_profile.cameras.add(camera)
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
                annotated_frame = frame.copy()
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame, model="hog") 
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                persons = list(Person.objects.all())
                known_encodings = []
                persons_with_encodings = []
                for p in persons:
                    if p.encodings:
                        known_encodings.append(np.array(p.encodings))
                        persons_with_encodings.append(p)

                for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
                    face_image = save_face_image(frame, top, right, bottom, left)
                    matched = recognize_face(encoding, known_encodings)
                    if any(matched):
                        idx = matched.index(True)
                        matched_person = persons_with_encodings[idx]
                        print(f"🔴 Alerta: Se detectó a {matched_person.name}")
                        log_detection(matched_person.name, self.camera.name)
                        try:
                            DetectionEvent.objects.create(
                                person=matched_person,
                                camera=self.camera,
                                image=ContentFile(face_image, name=f"{matched_person.name}_{int(time.time())}.jpg")
                            )
                        except Exception as e:
                            print(f"❌ Error al guardar el evento en la base de datos: {e}")
                        cv2.rectangle(annotated_frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        cv2.putText(annotated_frame, matched_person.name, (left, top - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    else:
                        label = "Desconocido"
                        if self.unknown_count < 10:
                            try:
                                unknown_person = Person.objects.create(name=label)
                                unknown_person.photo.save(f"{unknown_person.id}.jpg", ContentFile(face_image))
                                unknown_person.encodings = encoding.tolist()
                                unknown_person.save()
                                print(f"✅ Persona desconocida guardada: {unknown_person.id}")
                            except Exception as e:
                                print(f"❌ Error al guardar persona desconocida: {e}")
                            self.unknown_count += 1
                        else:
                            print("⚠ Rostro no reconocido. Límite de fotos alcanzado.")
                        try:
                            DetectionEvent.objects.create(
                                person=None,
                                camera=self.camera,
                                image=ContentFile(face_image, name=f"desconocido_{int(time.time())}.jpg")
                            )
                        except Exception as e:
                            print(f"❌ Error al crear evento de detección para desconocido: {e}")
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

@csrf_exempt  
@require_POST
def edit_camera_name(request, camera_id):
    """Edita el nombre de una cámara."""
    try:
        camera = get_object_or_404(Camera, id=camera_id)
        data = json.loads(request.body)
        new_name = data.get("name")

        if not new_name:
            return JsonResponse({"error": "El nombre no puede estar vacío."}, status=400)

        camera.name = new_name
        camera.save()

        return JsonResponse({"message": "Nombre de cámara actualizado correctamente.", "new_name": camera.name})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Formato JSON inválido."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
REPORTS_PATH = "media/reports/"
if not os.path.exists(REPORTS_PATH):
    os.makedirs(REPORTS_PATH)

def log_detection(person_name, camera_name):
    report_file = os.path.join(REPORTS_PATH, f"detections_{datetime.now().date()}.csv")
    try:
        with open(report_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            if file.tell() == 0:
                writer.writerow(["Fecha", "Hora", "Persona", "Cámara"])
            writer.writerow([datetime.now().date(), datetime.now().time(), person_name, camera_name])
        print(f"✅ Registro guardado en {report_file}: {person_name} en {camera_name}")  
    except Exception as e:
        print(f"❌ Error al escribir en el reporte CSV: {e}")

def download_csv(self, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="detections.csv"'
    writer = csv.writer(response)
    writer.writerow(["Fecha", "Hora", "Cámara", "Confianza", "Notificado"])

    print(f"🔍 Exportando {queryset.count()} eventos de detección...") 

    for event in queryset:
        print(f"➡️ {event.timestamp} - {event.camera} - {event.confidence}")  
        writer.writerow([
            event.timestamp.date(),
            event.timestamp.time(),
            event.camera.name if event.camera else "Cámara no registrada",
            event.confidence if event.confidence else "N/A",
            "Sí" if event.notified else "No"
        ])

    return response
# Cargar claves VAPID
private_key_pem, public_key = generate_or_load_vapid_keys()

# Grabar video
VIDEO_SAVE_PATH = "media/videos/"
active_recordings = {}

def record_video(camera_ip, duration=300, camera_id=None):
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
    """Inicia la grabación de una cámara y alerta a usuarios cercanos"""
    camera = get_object_or_404(Camera, id=camera_id)
    
    if camera_id in active_recordings:
        return JsonResponse({"error": "La cámara ya está grabando."}, status=400)
    
    recording_thread = threading.Thread(target=record_video, args=(camera.ip_address, 300, camera_id))
    recording_thread.start()
    active_recordings[camera_id] = recording_thread

    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "No se pudo decodificar el JSON"}, status=400)
    
    user_profile = request.user.userprofile
    user_lat = body.get("latitude")
    user_lon = body.get("longitude")

    if not user_lat or not user_lon:
        return JsonResponse({"error": "Ubicación no recibida"}, status=400)

    print(f"📍 Ubicación del usuario: {user_lat}, {user_lon}")

    location = {
        "latitude": camera.latitude or user_lat,
        "longitude": camera.longitude or user_lon
    }

    print(f"📷 Ubicación de la cámara: {location}")

    nearby_user_subscriptions = send_location_to_nearby_users(location)
    
    notification_data = json.dumps({
        "title": "🚨 Alerta de Grabación",
        "body": f"La cámara {camera.name} ha comenzado a grabar.",
        "latitude": str(location["latitude"]),  # 👈 Convertido a str
        "longitude": str(location["longitude"])  # 👈 Convertido a str
    })

    
    for subscription_info in nearby_user_subscriptions:
        send_web_push(subscription_info, notification_data, private_key_pem, "mailto:federico.-torres@hotmail.com")
    
    return JsonResponse({
        "message": "Grabación iniciada correctamente",
        "redirect_url": f"/recording_in_progress/{camera_id}/",
        "location": location
    })

def download_media(request, event_id, file_type):
    event = get_object_or_404(DetectionEvent, id=event_id)

    if file_type == 'image' and event.image:
        file_path = event.image.path
    elif file_type == 'video' and event.video:
        file_path = event.video.path
    else:
        raise Http404("Archivo no encontrado")

    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True)
    else:
        raise Http404("Archivo no encontrado")

def recording_in_progress(request, camera_id):
    camera = get_object_or_404(Camera, id=camera_id)
    recording_duration = 300  

    context = {
        "camera": camera,
        "minutes": recording_duration // 60,
        "seconds": recording_duration % 60,
    }
    return render(request, 'reconocimiento/recording_in_progress.html', {'camera': camera})

def send_location_to_nearby_users(camera_location): 
    """Enviar notificación web push a usuarios dentro de 2 km"""
    
    print(f"🔎 Ejecutando send_location_to_nearby_users con ubicación: {camera_location}")
    
    nearby_users = []
    nearby_user_subscriptions = []
    
    for user in UserProfile.objects.all():
        if not user.latitude or not user.longitude:
            print(f"❌ {user.email} excluido por falta de coordenadas")
            continue

        if not user.subscription_info:
            print(f"❌ {user.email} excluido por falta de `subscription_info`")
            continue
        
        distance = geodesic(
            (user.latitude, user.longitude), 
            (camera_location['latitude'], camera_location['longitude'])
        ).km
        
        print(f"🔍 {user.email} está a {distance:.2f} km")
        
        if distance <= 2:
            print(f"✅ {user.email} dentro del rango")
            nearby_users.append(user)
            nearby_user_subscriptions.append(user.subscription_info) 

    print(f"Usuarios cercanos encontrados: {len(nearby_users)}")

    return nearby_user_subscriptions


def send_web_push(subscription_info, data, vapid_private_key, email):
    try:
        print(f"📨 Enviando Push a: {subscription_info}")
        print(f"📤 Datos enviados: {data}")

        webpush(
            subscription_info=json.loads(subscription_info) if isinstance(subscription_info, str) else subscription_info,
            data=data,
            vapid_private_key=vapid_private_key,
            vapid_claims={"sub": email if email.startswith("mailto:") else f"mailto:{email}"}
        )
    except WebPushException as ex:
        print(f"❌ Error en Web Push: {repr(ex)}")
        if ex.response and ex.response.json():
            print("📋 Detalles del error:", ex.response.json())



@csrf_exempt
@login_required
def update_location(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')

            if latitude and longitude:
                user_profile = request.user.userprofile
                user_profile.latitude = latitude
                user_profile.longitude = longitude
                user_profile.save()
                return JsonResponse({'message': 'Ubicación del usuario actualizada correctamente'})

            return JsonResponse({'error': 'Datos inválidos'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

def get_lat_long(location):
    geolocator = Nominatim(user_agent="myGeocoder")
    location_obj = geolocator.geocode(location)
    if location_obj:
        return location_obj.latitude, location_obj.longitude
    return None, None

def show_map(request):
    latitude = request.GET.get('latitude', '0').replace(",", ".")
    longitude = request.GET.get('longitude', '0').replace(",", ".")

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        latitude, longitude = 0, 0

    return render(request, 'reconocimiento/map.html', {'latitude': latitude, 'longitude': longitude})



def get_nearby_users(user_location, users_queryset):
    nearby_users = []
    for user in users_queryset:
        user_location_coords = (user.profile.latitude, user.profile.longitude)
        distance = geodesic(user_location, user_location_coords).meters
        if distance <= 5000:
            nearby_users.append(user)
    
    return nearby_users

@require_GET
@csrf_exempt
def service_worker(request):
    sw_path = os.path.join(settings.BASE_DIR, 'camaras', 'static', 'js', 'service-worker.js')
    with open(sw_path, 'r') as f:
        response = HttpResponse(f.read(), content_type='application/javascript')
        response['Service-Worker-Allowed'] = '/'
        return response
    
def redirect_to_map(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    if lat and lon:
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        return redirect(google_maps_url)
    return HttpResponse("Faltan parámetros", status=400)