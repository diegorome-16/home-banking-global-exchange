from django.urls import path
from . import views

urlpatterns = [
    path('enviar/', views.enviar_transferencia_view, name='enviar_transferencia'),
    path('lista/', views.listar_transferencias_view, name='listar_transferencias'),
    path('detalle/<str:referencia>/', views.detalle_transferencia_view, name='detalle_transferencia'),
    path('api/consultar/<str:referencia>/', views.consultar_transferencia_api, name='consultar_transferencia_api'),
]
