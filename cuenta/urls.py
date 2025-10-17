from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('historial/', views.historial_view, name='historial'),
    path('api/register/', views.api_register, name='api_register'),
    path('api/transferencias/enviadas/', views.api_transferencias_enviadas, name='api_transferencias_enviadas'),
    path('api/transferencias/recibidas/', views.api_transferencias_recibidas, name='api_transferencias_recibidas'),
]
