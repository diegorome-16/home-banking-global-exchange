from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cuenta/', include('cuenta.urls')),
    path('transferencia/', include('transferencia.urls')),
    path('tarjeta-credito/', include('tarjeta_credito.urls')),
]
