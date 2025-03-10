from django.urls import path
from .views import camera_list, camera_feed, home, start_recording, recording_in_progress
from . import views

urlpatterns = [
    path('cameras/', camera_list, name='camera_list'),
    path('camera_feed/<int:camera_id>/', views.camera_feed, name='camera_feed'),
    path('camera_feed_template/<int:camera_id>/', views.camera_feed_template, name='camera_feed_template'),
    path('reconocimiento/detect_cameras/', views.detect_cameras, name='detect_cameras'),
    path('set_default_camera/<int:camera_id>/', views.set_default_camera, name='set_default_camera'),
    path('start_recording/<int:camera_id>/', start_recording, name='start_recording'),
    path('recording_in_progress/<int:camera_id>/', recording_in_progress, name='recording_in_progress'),
    path('register_and_set_default_camera/', views.register_and_set_default_camera, name='register_and_set_default_camera'),

    path('home/', home, name='home'),
]