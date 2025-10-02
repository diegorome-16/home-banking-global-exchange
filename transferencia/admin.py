from django.contrib import admin
from .models import Transferencia

@admin.register(Transferencia)
class TransferenciaAdmin(admin.ModelAdmin):
    list_display = ['referencia', 'cuenta_origen', 'cuenta_destino', 'monto', 'estado', 'fecha_creacion']
    list_filter = ['estado', 'fecha_creacion', 'fecha_procesamiento']
    search_fields = ['referencia', 'cuenta_origen__numero_cuenta', 'cuenta_destino__numero_cuenta', 'concepto']
    readonly_fields = ['referencia', 'fecha_creacion', 'fecha_procesamiento']
    ordering = ['-fecha_creacion']

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.estado == 'COMPLETADA':  # Si la transferencia ya fue completada
            return self.readonly_fields + ['cuenta_origen', 'cuenta_destino', 'monto', 'concepto', 'estado']
        return self.readonly_fields
