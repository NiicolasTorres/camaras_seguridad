from django.contrib import admin
from django.urls import path, include
from reconocimiento.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('reconocimiento.urls')),  
    path('', home, name='home'),
]