from django.contrib import admin
from .models import Person, DetectionEvent, Camera
from cuentas.models import UserProfile

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
    list_display = ('camera', 'timestamp', 'confidence', 'notified', 'image', 'video')
    search_fields = ('camera__name', 'timestamp')
    list_filter = ('camera', 'notified')
    readonly_fields = ('camera', 'timestamp', 'person', 'confidence', 'image', 'video')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user_profile_id = request.GET.get("user_profile_id")
        if user_profile_id:
            try:
                user_profile = UserProfile.objects.get(pk=user_profile_id)
                camera_ids = user_profile.cameras.values_list('id', flat=True)
                qs = qs.filter(camera__id__in=camera_ids)
            except UserProfile.DoesNotExist:
                qs = qs.none()
        return qs

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
