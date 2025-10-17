from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='login', permanent=False), name='home'),
    path('admin/', admin.site.urls),
    path('cuenta/', include('cuenta.urls')),
    path('transferencia/', include('transferencia.urls')),
    path('tarjeta-credito/', include('tarjeta_credito.urls')),
]
