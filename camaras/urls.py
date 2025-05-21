from django.contrib import admin
from django.urls import path, include
from reconocimiento.views import home
from cuentas.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('reconocimiento/', include('reconocimiento.urls')),  
    path('cuentas/', include('cuentas.urls')),  
]