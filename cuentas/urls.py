from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import profile, edit_profile, save_subscription
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='cuentas/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('perfil/editar/', edit_profile, name='edit_profile'),
    path('vapid_public_key/', views.vapid_public_key, name='vapid_public_key'),
    path('save_subscription/', save_subscription, name='save_subscription'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
