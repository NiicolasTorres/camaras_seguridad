from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile
from reconocimiento.models import DetectionEvent
from math import radians, cos, sin, sqrt, atan2


@login_required
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_camera = user_profile.camera
    suspicious_events = DetectionEvent.objects.filter(camera=user_camera, person__isnull=True).order_by('-timestamp')[:5]

    context = {
        'user': request.user,
        'user_profile': user_profile,
        'user_camera': user_camera,
        'suspicious_events': suspicious_events
    }

    return render(request, 'cuentas/profile.html', context)

@login_required
def edit_profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_profile.full_name = request.POST.get('full_name', '')
        user_profile.dni = request.POST.get('dni', '')
        user_profile.phone_number = request.POST.get('phone_number', '')
        user_profile.address = request.POST.get('address', '')
        user_profile.emergency_contact_name = request.POST.get('emergency_contact_name', '')
        user_profile.emergency_contact_phone = request.POST.get('emergency_contact_phone', '')

        # Manejo de la imagen de perfil
        if request.FILES.get('profile_picture'):
            user_profile.profile_picture = request.FILES['profile_picture']

        user_profile.save()
        messages.success(request, "Perfil actualizado correctamente.")

    return redirect('profile')


