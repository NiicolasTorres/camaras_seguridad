from django.db import models
from django.contrib.auth.models import User

class Camera(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    latitude = models.FloatField(blank=True, null=True)  
    longitude = models.FloatField(blank=True, null=True)  
    mac_address = models.CharField(max_length=17, unique=True, blank=True, null=True)  
    ip_address = models.GenericIPAddressField(blank=True, null=True)  
    active = models.BooleanField(default=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Cámara"
        verbose_name_plural = "Cámaras"


class Person(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    photo = models.ImageField(upload_to='faces/', blank=True, null=True)
    encodings = models.JSONField(blank=True, null=True)  
    registered = models.BooleanField(default=False)  

    def __str__(self):
        return self.name if self.name else "Desconocido"
    
    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"

    def user_profile(self):
        try:
            return self.detectionevent_set.first().camera.userprofile.user.username
        except AttributeError:
            return "Sin usuario asociado"

class DetectionEvent(models.Model):
    person = models.ForeignKey('Person', on_delete=models.CASCADE, null=True, blank=True)
    camera = models.ForeignKey('Camera', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    confidence = models.FloatField(blank=True, null=True)
    image = models.ImageField(upload_to='detections/', blank=True, null=True)
    video = models.FileField(upload_to='videos/', blank=True, null=True)
    notified = models.BooleanField(default=False)
    actions = ['download_csv']

    def __str__(self):
        return f"Detección en {self.camera} - {self.timestamp}"
    
    def get_users(self):
        from cuentas.models import UserProfile  # Importar aquí para evitar la importación circular
        return UserProfile.objects.filter(cameras=self.camera)
    
    def send_notification(self):
        """Enviar una notificación a los usuarios cercanos cuando se detecta algo"""


        from geopy.distance import geodesic
        from django.core.mail import send_mail

        # Obtener la ubicación de la cámara
        camera_location = {'latitude': self.camera.latitude, 'longitude': self.camera.longitude}

        # Obtener todos los usuarios cercanos
        users = User.objects.all()
        nearby_users = []
        for user in users:
            # Supón que el modelo User tiene latitud y longitud
            if user.profile.latitude and user.profile.longitude:
                user_location = (user.profile.latitude, user.profile.longitude)
                distance = geodesic(user_location, (camera_location['latitude'], camera_location['longitude'])).km

                # Si el usuario está dentro de 1 km de distancia, agregar a la lista
                if distance <= 1:
                    nearby_users.append(user)

        # Enviar notificaciones a los usuarios cercanos
        for user in nearby_users:
            send_mail(
                'Alerta: Cámara detectó movimiento',
                f'Un evento de detección ha ocurrido cerca de tu ubicación. Detalles: {self.camera.name} - {self.timestamp}',
                'from@example.com',  # Aquí iría tu correo
                [user.email],  # Correo del usuario
                fail_silently=False,
            )

        # Marcar el evento como notificado
        self.notified = True
        self.save()

    class Meta:
        verbose_name = "Evento de detección"
        verbose_name_plural = "Eventos de detección"

class AccessLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)  
    ip_address = models.GenericIPAddressField(blank=True, null=True)  
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"