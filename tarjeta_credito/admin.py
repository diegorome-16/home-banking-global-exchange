from django.contrib import admin
from .models import TarjetaCredito


@admin.register(TarjetaCredito)
class TarjetaCreditoAdmin(admin.ModelAdmin):
    list_display = [
        'numero_enmascarado',
        'identificador_unico_corto',
        'usuario',
        'marca',
        'estado',
        'limite_credito',
        'credito_disponible',
        'fecha_vencimiento',
        'esta_vencida'
    ]
    list_filter = [
        'marca',
        'estado',
        'fecha_creacion',
        'fecha_vencimiento'
    ]
    search_fields = [
        'usuario__username',
        'usuario__email',
        'ultimos_4_digitos',
        'numero_tarjeta',
        'identificador_unico'
    ]
    readonly_fields = [
        'identificador_unico',
        'numero_tarjeta',
        'ultimos_4_digitos',
        'cvc',
        'fecha_vencimiento',
        'fecha_creacion',
        'numero_enmascarado',
        'esta_vencida',
        'credito_utilizado'
    ]
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('usuario',)
        }),
        ('Identificadores', {
            'fields': (
                'identificador_unico',
                'numero_enmascarado',
                'numero_tarjeta',
                'ultimos_4_digitos'
            )
        }),
        ('Información de la Tarjeta', {
            'fields': (
                'marca',
                'cvc',
                'fecha_vencimiento',
                'esta_vencida'
            )
        }),
        ('Estado y Límites', {
            'fields': (
                'estado',
                'limite_credito',
                'credito_disponible',
                'credito_utilizado'
            )
        }),
        ('Fechas', {
            'fields': ('fecha_creacion',)
        })
    )

    def identificador_unico_corto(self, obj):
        return str(obj.identificador_unico)[:8] + '...'
    identificador_unico_corto.short_description = 'ID Único'

    def numero_enmascarado(self, obj):
        return obj.numero_enmascarado
    numero_enmascarado.short_description = 'Número de Tarjeta'

    def esta_vencida(self, obj):
        return obj.esta_vencida
    esta_vencida.boolean = True
    esta_vencida.short_description = '¿Vencida?'

    def credito_utilizado(self, obj):
        return f"${obj.credito_utilizado:,.2f}"
    credito_utilizado.short_description = 'Crédito Utilizado'
