from django.db import models
from django.contrib.auth.models import User
from cuenta.models import Cuenta
from django.core.validators import MinValueValidator

class Transferencia(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('COMPLETADA', 'Completada'),
        ('FALLIDA', 'Fallida'),
        ('CANCELADA', 'Cancelada'),
    ]

    cuenta_origen = models.ForeignKey(
        Cuenta,
        on_delete=models.CASCADE,
        related_name='transferencias_enviadas'
    )
    cuenta_destino = models.ForeignKey(
        Cuenta,
        on_delete=models.CASCADE,
        related_name='transferencias_recibidas'
    )
    monto = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    concepto = models.CharField(max_length=200, blank=True, null=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(blank=True, null=True)
    referencia = models.CharField(max_length=50, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.referencia:
            self.referencia = self.generar_referencia()
        super().save(*args, **kwargs)

    def generar_referencia(self):
        """Genera una referencia única para la transferencia"""
        import random
        import string
        from datetime import datetime

        fecha = datetime.now().strftime("%Y%m%d")
        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"TRF{fecha}{codigo}"

    def procesar_transferencia(self):
        """Procesa la transferencia actualizando los saldos de las cuentas"""
        from django.utils import timezone
        from django.db import transaction

        if self.estado != 'PENDIENTE':
            return False, "La transferencia ya fue procesada"

        if self.cuenta_origen.saldo_disponible < self.monto:
            self.estado = 'FALLIDA'
            self.fecha_procesamiento = timezone.now()
            self.save()
            return False, "Saldo insuficiente"

        try:
            with transaction.atomic():
                # Debitar de cuenta origen
                self.cuenta_origen.saldo_disponible -= self.monto
                self.cuenta_origen.save()

                # Acreditar a cuenta destino
                self.cuenta_destino.saldo_disponible += self.monto
                self.cuenta_destino.save()

                # Actualizar estado de transferencia
                self.estado = 'COMPLETADA'
                self.fecha_procesamiento = timezone.now()
                self.save()

                return True, "Transferencia completada exitosamente"
        except Exception as e:
            self.estado = 'FALLIDA'
            self.fecha_procesamiento = timezone.now()
            self.save()
            return False, f"Error al procesar la transferencia: {str(e)}"

    def __str__(self):
        return f"{self.referencia} - {self.cuenta_origen} → {self.cuenta_destino} - ${self.monto}"

    class Meta:
        verbose_name = "Transferencia"
        verbose_name_plural = "Transferencias"
        ordering = ['-fecha_creacion']
