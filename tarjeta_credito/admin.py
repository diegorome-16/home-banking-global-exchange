# from django.contrib import admin
# from .models import TarjetaCredito, TransaccionTarjeta


# @admin.register(TarjetaCredito)
# class TarjetaCreditoAdmin(admin.ModelAdmin):
#     list_display = ('numero_tarjeta', 'marca', 'ultimos_4_digitos', 'usuario', 'credito_disponible', 'limite_credito', 'activa', 'fecha_creacion')
#     list_filter = ('marca', 'activa', 'fecha_creacion')
#     search_fields = ('numero_tarjeta', 'ultimos_4_digitos', 'usuario__username', 'usuario__email')
#     readonly_fields = ('identificador_unico', 'numero_tarjeta', 'ultimos_4_digitos', 'fecha_creacion')

#     fieldsets = (
#         ('Información Básica', {
#             'fields': ('usuario', 'marca', 'identificador_unico', 'numero_tarjeta', 'ultimos_4_digitos')
#         }),
#         ('Seguridad', {
#             'fields': ('cvc', 'fecha_vencimiento')
#         }),
#         ('Límites y Saldo', {
#             'fields': ('limite_credito', 'credito_disponible')
#         }),
#         ('Estado', {
#             'fields': ('activa', 'fecha_creacion')
#         }),
#     )


# @admin.register(TransaccionTarjeta)
# class TransaccionTarjetaAdmin(admin.ModelAdmin):
#     list_display = ('id_transaccion', 'tarjeta', 'monto', 'estado', 'fecha_pago', 'fecha_cobro', 'numero_cuenta_destino')
#     list_filter = ('estado', 'fecha_pago', 'fecha_cobro', 'tarjeta__marca')
#     search_fields = ('id_transaccion', 'tarjeta__numero_tarjeta', 'numero_cuenta_destino', 'descripcion')
#     readonly_fields = ('id_transaccion', 'fecha_pago')

#     fieldsets = (
#         ('Información de Transacción', {
#             'fields': ('id_transaccion', 'tarjeta', 'monto', 'descripcion')
#         }),
#         ('Estado y Fechas', {
#             'fields': ('estado', 'fecha_pago', 'fecha_cobro')
#         }),
#         ('Cobro', {
#             'fields': ('numero_cuenta_destino',)
#         }),
#     )

#     def get_readonly_fields(self, request, obj=None):
#         if obj and obj.estado == 'cobrada':
#             return self.readonly_fields + ('tarjeta', 'monto', 'estado', 'fecha_cobro', 'numero_cuenta_destino')
#         return self.readonly_fields
