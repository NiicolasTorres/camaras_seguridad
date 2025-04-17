from django.contrib import admin
from .models import Person, DetectionEvent, Camera
from cuentas.models import UserProfile
import csv
from django.http import HttpResponse

class DetectionEventInline(admin.TabularInline):
    model = DetectionEvent
    extra = 0

class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_profile', 'registered')
    inlines = [DetectionEventInline]
    verbose_name = "Persona"
    verbose_name_plural = "Personas"

admin.site.register(Person, PersonAdmin)

class DetectionEventAdmin(admin.ModelAdmin):
    actions = ['download_csv']

    def download_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="detections.csv"'
        writer = csv.writer(response)
        writer.writerow(["Fecha", "Hora", "Cámara", "Confianza", "Notificado"])

        for event in queryset:
            writer.writerow([
                event.timestamp.date(),
                event.timestamp.time(),
                event.camera.name if event.camera else "Cámara no registrada",
                event.confidence if event.confidence else "N/A",
                "Sí" if event.notified else "No"
            ])

        return response

    download_csv.short_description = "Descargar CSV de detecciones"

admin.site.register(DetectionEvent, DetectionEventAdmin)



class CameraAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'ip_address', 'active', 'created_at')
    search_fields = ('name', 'location', 'ip_address')
    list_filter = ('active',)
    ordering = ('-created_at',)
    list_editable = ('name',) 
    list_display_links = ('location',) 
    verbose_name = "Cámara"
    verbose_name_plural = "Cámaras"

admin.site.register(Camera, CameraAdmin)
