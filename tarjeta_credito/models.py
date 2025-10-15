from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MaxLengthValidator
from datetime import datetime, timedelta
import random
import string
import uuid


class TarjetaCredito(models.Model):
    MARCA_CHOICES = [
        #('AMERICAN_EXPRESS', 'American Express'),
        ('CABAL', 'Cabal'),
        ('CREDICARD', 'Credicard'),
    ]

    ESTADO_CHOICES = [
        ('ACTIVA', 'Activa'),
        ('BLOQUEADA', 'Bloqueada'),
        ('VENCIDA', 'Vencida'),
        ('CANCELADA', 'Cancelada'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tarjetas_credito'
    )
    identificador_unico = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Identificador único de la tarjeta para uso en APIs"
    )
    numero_tarjeta = models.CharField(
        max_length=16,
        unique=True,
        editable=False,
        validators=[MinLengthValidator(16), MaxLengthValidator(16)]
    )
    ultimos_4_digitos = models.CharField(
        max_length=4,
        editable=False,
        validators=[MinLengthValidator(4), MaxLengthValidator(4)]
    )
    marca = models.CharField(
        max_length=20,
        choices=MARCA_CHOICES,
        default='CABAL'
    )
    cvc = models.CharField(
        max_length=4,
        editable=False,
        validators=[MinLengthValidator(3), MaxLengthValidator(4)]
    )
    fecha_vencimiento = models.DateField(editable=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='ACTIVA'
    )
    limite_credito = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=50000.00
    )
    credito_disponible = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=50000.00
    )

    def save(self, *args, **kwargs):
        if not self.numero_tarjeta:
            self.numero_tarjeta = self.generar_numero_tarjeta()
            self.ultimos_4_digitos = self.numero_tarjeta[-4:]

        if not self.cvc:
            self.cvc = self.generar_cvc()

        if not self.fecha_vencimiento:
            self.fecha_vencimiento = self.generar_fecha_vencimiento()

        # Asegurar que el crédito disponible no sea mayor al límite
        if self.credito_disponible > self.limite_credito:
            self.credito_disponible = self.limite_credito

        super().save(*args, **kwargs)

    def generar_numero_tarjeta(self):
        """Genera un número de tarjeta único basado en la marca seleccionada"""
        prefijos = {
            'AMERICAN_EXPRESS': ['34', '37'],  # American Express inicia con 34 o 37
            'CABAL': ['627170', '589657'],     # Cabal tiene prefijos específicos
            'CREDICARD': ['636368', '636297'], # Credicard prefijos
        }

        prefijo = random.choice(prefijos.get(self.marca, ['5555']))  # Default

        # Generar el resto de dígitos
        longitud_restante = 16 - len(prefijo) - 1  # -1 para el dígito de verificación
        resto = ''.join(random.choices(string.digits, k=longitud_restante))

        # Calcular dígito de verificación usando algoritmo de Luhn
        numero_base = prefijo + resto
        digito_verificacion = self.calcular_digito_luhn(numero_base)

        numero_completo = numero_base + str(digito_verificacion)

        # Verificar que el número no existe
        while TarjetaCredito.objects.filter(numero_tarjeta=numero_completo).exists():
            resto = ''.join(random.choices(string.digits, k=longitud_restante))
            numero_base = prefijo + resto
            digito_verificacion = self.calcular_digito_luhn(numero_base)
            numero_completo = numero_base + str(digito_verificacion)

        return numero_completo

    def calcular_digito_luhn(self, numero):
        """Calcula el dígito de verificación usando el algoritmo de Luhn"""
        suma = 0
        es_par = True

        for i in range(len(numero) - 1, -1, -1):
            digito = int(numero[i])

            if es_par:
                digito *= 2
                if digito > 9:
                    digito = digito // 10 + digito % 10

            suma += digito
            es_par = not es_par

        return (10 - (suma % 10)) % 10

    def generar_cvc(self):
        """Genera un CVC de 3 o 4 dígitos según la marca"""
        if self.marca == 'AMERICAN_EXPRESS':
            return ''.join(random.choices(string.digits, k=4))
        else:
            return ''.join(random.choices(string.digits, k=3))

    def generar_fecha_vencimiento(self):
        """Genera una fecha de vencimiento 3 años en el futuro"""
        return datetime.now().date() + timedelta(days=365 * 3)

    @property
    def numero_enmascarado(self):
        """Retorna el número de tarjeta enmascarado para mostrar al usuario"""
        return f"**** **** **** {self.ultimos_4_digitos}"

    @property
    def esta_vencida(self):
        """Verifica si la tarjeta está vencida"""
        return self.fecha_vencimiento < datetime.now().date()

    @property
    def credito_utilizado(self):
        """Calcula el crédito utilizado"""
        return self.limite_credito - self.credito_disponible

    def actualizar_estado_si_vencida(self):
        """Actualiza el estado a vencida si corresponde"""
        if self.esta_vencida and self.estado == 'ACTIVA':
            self.estado = 'VENCIDA'
            self.save()

    def bloquear_tarjeta(self, motivo="Bloqueada por el usuario"):
        """Bloquea la tarjeta"""
        if self.estado == 'ACTIVA':
            self.estado = 'BLOQUEADA'
            self.save()
            return True, "Tarjeta bloqueada exitosamente"
        return False, "La tarjeta no está activa"

    def desbloquear_tarjeta(self):
        """Desbloquea la tarjeta si es posible"""
        if self.estado == 'BLOQUEADA' and not self.esta_vencida:
            self.estado = 'ACTIVA'
            self.save()
            return True, "Tarjeta desbloqueada exitosamente"
        return False, "No es posible desbloquear la tarjeta"

    def __str__(self):
        return f"{self.get_marca_display()} - {self.numero_enmascarado} ({self.usuario.username})"

    class Meta:
        verbose_name = "Tarjeta de Crédito"
        verbose_name_plural = "Tarjetas de Crédito"
        ordering = ['-fecha_creacion']


class TransaccionTarjeta(models.Model):
    ESTADOS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('cobrada', 'Cobrada'),
        ('cancelada', 'Cancelada'),
    ]

    id_transaccion = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, primary_key=True)
    tarjeta = models.ForeignKey(TarjetaCredito, on_delete=models.CASCADE, related_name='transacciones')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS_CHOICES, default='pendiente')
    fecha_pago = models.DateTimeField(auto_now_add=True)
    fecha_cobro = models.DateTimeField(null=True, blank=True)
    numero_cuenta_destino = models.CharField(max_length=20, null=True, blank=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return f"Transacción {str(self.id_transaccion)[:8]} - ${self.monto}"

    class Meta:
        verbose_name = "Transacción de Tarjeta"
        verbose_name_plural = "Transacciones de Tarjetas"
        ordering = ['-fecha_pago']