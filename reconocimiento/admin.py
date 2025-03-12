from django.contrib import admin
from .models import Camera, Person, DetectionEvent

admin.site.register(Camera)
admin.site.register(Person)
admin.site.register(DetectionEvent)