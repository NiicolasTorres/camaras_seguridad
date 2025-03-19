from django.contrib import admin
from .models import Person, DetectionEvent

class DetectionEventInline(admin.TabularInline):
    model = DetectionEvent
    extra = 0

class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_profile', 'registered')
    inlines = [DetectionEventInline]

admin.site.register(Person, PersonAdmin)

class DetectionEventAdmin(admin.ModelAdmin):
    list_display = ('camera', 'timestamp', 'confidence', 'notified')
    list_filter = ('notified',)

admin.site.register(DetectionEvent, DetectionEventAdmin)
