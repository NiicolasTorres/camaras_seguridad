
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile
from reconocimiento.models import DetectionEvent
from math import radians, cos, sin, sqrt, atan2
from py_vapid import Vapid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from cryptography.hazmat.primitives.asymmetric import ec
from .utils import generate_or_load_vapid_keys
from django.conf import settings

@login_required
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(
    user=request.user,
    defaults={'email': request.user.email}
)
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
        
        # Verificar si el email ha cambiado
        new_email = request.POST.get('email', '').strip()
        if new_email and new_email != user_profile.email:
            if UserProfile.objects.filter(email=new_email).exclude(user=request.user).exists():
                messages.error(request, "Este correo electrónico ya está en uso. Por favor, elige otro.")
                return redirect('edit_profile')
            else:
                user_profile.email = new_email
                user_profile.user.email = new_email


        # Manejo de la imagen de perfil
        if request.FILES.get('profile_picture'):
            user_profile.profile_picture = request.FILES['profile_picture']

        user_profile.save()
        user_profile.user.save()  # Guardar también el modelo User
        messages.success(request, "Perfil actualizado correctamente.")

        return redirect('profile')


@csrf_exempt
def save_subscription(request):
    if request.method == "POST":
        try:
            # Obtener la suscripción del cuerpo de la solicitud
            subscription_data = json.loads(request.body)
            # Guarda la suscripción (por ejemplo, en el perfil del usuario)
            user_profile = request.user.userprofile
            user_profile.subscription_info = subscription_data
            user_profile.save()
            return JsonResponse({"message": "Suscripción guardada correctamente"}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Error al procesar el JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Método no permitido"}, status=405)


def vapid_public_key(request):
    _, public_key = generate_or_load_vapid_keys()
    return JsonResponse({"publicKey": public_key})