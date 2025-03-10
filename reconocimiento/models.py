from django.db import models
from django.contrib.auth.models import User

class Camera(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    mac_address = models.CharField(max_length=17, unique=True, blank=True, null=True)  # Dirección MAC
    ip_address = models.GenericIPAddressField(blank=True, null=True)  
    active = models.BooleanField(default=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Person(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    photo = models.ImageField(upload_to='faces/', blank=True, null=True)
    encodings = models.JSONField(blank=True, null=True)  
    registered = models.BooleanField(default=False)  

    def __str__(self):
        return self.name if self.name else "Desconocido"

class DetectionEvent(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True, blank=True)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    confidence = models.FloatField(blank=True, null=True)  
    image = models.ImageField(upload_to='detections/', blank=True, null=True)  
    video = models.FileField(upload_to='videos/', blank=True, null=True)  

    def __str__(self):
        return f"Detección en {self.camera} - {self.timestamp}"

class AccessLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)  
    ip_address = models.GenericIPAddressField(blank=True, null=True)  
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"