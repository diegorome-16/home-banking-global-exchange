from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import random
import string

class Cuenta(models.Model):
    TIPO_CUENTA_CHOICES = [
        ('AHORRO', 'Cuenta de Ahorro'),
        ('CORRIENTE', 'Cuenta Corriente'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cuenta')
    numero_cuenta = models.CharField(max_length=20, unique=True, editable=False)
    saldo_disponible = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    tipo_cuenta = models.CharField(max_length=10, choices=TIPO_CUENTA_CHOICES, default='AHORRO')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.numero_cuenta:
            self.numero_cuenta = self.generar_numero_cuenta()
        super().save(*args, **kwargs)

    def generar_numero_cuenta(self):
        """Genera un número de cuenta único de 16 dígitos"""
        while True:
            numero = ''.join(random.choices(string.digits, k=16))
            if not Cuenta.objects.filter(numero_cuenta=numero).exists():
                return numero

    def __str__(self):
        return f"{self.usuario.username} - {self.numero_cuenta}"

    class Meta:
        verbose_name = "Cuenta"
        verbose_name_plural = "Cuentas"
