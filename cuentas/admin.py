from django.contrib import admin
from .models import UserProfile
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from reconocimiento.models import DetectionEvent

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'email', 'detection_events_link')
    search_fields = ('user__username', 'full_name', 'email')

    def detection_events_link(self, obj):
        # Genera la URL para acceder a los eventos de detección de este usuario
        url_name = "admin:%s_%s_changelist" % (
            DetectionEvent._meta.app_label,
            DetectionEvent._meta.model_name,
        )
        url = reverse(url_name) + f"?user_profile_id={obj.id}"
        return format_html('<a href="{}">Ver actividad de detecciones</a>', url)
    detection_events_link.short_description = "Detecciones"

admin.site.register(UserProfile, UserProfileAdmin)