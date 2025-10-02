from django.contrib import admin
from .models import Cuenta

@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ['numero_cuenta', 'usuario', 'saldo_disponible', 'tipo_cuenta', 'activa', 'fecha_creacion']
    list_filter = ['tipo_cuenta', 'activa', 'fecha_creacion']
    search_fields = ['numero_cuenta', 'usuario__username', 'usuario__email']
    readonly_fields = ['numero_cuenta', 'fecha_creacion']

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['usuario']
        return self.readonly_fields
