from django.db import models
from reconocimiento.models import Camera
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, default=1)
    full_name = models.CharField(max_length=150)
    dni = models.CharField(max_length=20, blank=True, null=True)  # Opcional
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    timezone = models.CharField(max_length=50, default='UTC')
    emergency_contact_name = models.CharField(max_length=150, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    last_login_time = models.DateTimeField(blank=True, null=True)
    notification_method = models.CharField(max_length=20, choices=[('email', 'Email'), ('sms', 'SMS'), ('push', 'Notificaciones Push')], default='email')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    latitude = models.FloatField(null=True, blank=True)  # Añadido para la latitud
    longitude = models.FloatField(null=True, blank=True)  # Añadido para la longitud
    fcm_token = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return self.full_name