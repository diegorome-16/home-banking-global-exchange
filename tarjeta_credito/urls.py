from django.urls import path
from . import views

app_name = 'tarjeta_credito'

urlpatterns = [
    # Vistas web
    path('solicitar/', views.solicitar_tarjeta_view, name='solicitar_tarjeta'),
    path('mis-tarjetas/', views.mis_tarjetas_view, name='mis_tarjetas'),
    path('detalle/<int:tarjeta_id>/', views.detalle_tarjeta_view, name='detalle_tarjeta'),
    path('bloquear/<int:tarjeta_id>/', views.bloquear_tarjeta_view, name='bloquear_tarjeta'),
    path('desbloquear/<int:tarjeta_id>/', views.desbloquear_tarjeta_view, name='desbloquear_tarjeta'),

    # API endpoints
    path('api/solicitar/', views.solicitar_tarjeta_api, name='solicitar_tarjeta_api'),
    path('api/consultar/<int:tarjeta_id>/', views.consultar_tarjeta_api, name='consultar_tarjeta_api'),
    path('api/consultar-numero/<str:numero_tarjeta>/', views.consultar_tarjeta_por_numero_api, name='consultar_tarjeta_por_numero_api'),
    path('api/consultar-datos/', views.consultar_tarjeta_por_datos_api, name='consultar_tarjeta_por_datos_api'),
]
