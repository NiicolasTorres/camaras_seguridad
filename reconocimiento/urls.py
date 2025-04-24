from django.urls import path
from .views import camera_list, proxy_camera, service_worker,camera_feed, home, start_recording, recording_in_progress, manifest,update_location, edit_camera_name,download_csv
from . import views


urlpatterns = [
    path('cameras/', camera_list, name='camera_list'),
    path('camera_feed/<int:camera_id>/', views.camera_feed, name='camera_feed'),
    path('camera_feed_template/<int:camera_id>/', views.camera_feed_template, name='camera_feed_template'),
    path('set_default_camera/<int:camera_id>/', views.set_default_camera, name='set_default_camera'),
    path('start_recording/<int:camera_id>/', start_recording, name='start_recording'),
    path('recording_in_progress/<int:camera_id>/', recording_in_progress, name='recording_in_progress'),
    path('register_and_set_default_camera/', views.register_and_set_default_camera, name='register_and_set_default_camera'),
    path('admin/camera_feed/<int:camera_id>/', camera_feed, name='admin_camera_feed'),
    path('update_location/', update_location, name='update_location'),
    path('home/', home, name='home'),
    path('descargar_csv/', download_csv, name='descargar_csv'),
    path('manifest.json', manifest, name='manifest'),
    path('edit_camera_name/<int:camera_id>/', edit_camera_name, name='edit_camera_name'),
    path('ubicacion/', views.show_map, name='map'),  
    path('ubicacion/<str:latitude>/<str:longitude>/', views.show_map, name='map'),
    path('service-worker.js', service_worker, name='service_worker'),
    path('mapa_alerta/', views.redirect_to_map, name='mapa_alerta'),
    path('proxy-camera/<str:camera_ip>/', views.proxy_camera, name='proxy_camera'),

]