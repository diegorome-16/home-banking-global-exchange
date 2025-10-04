from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Transferencia
from cuenta.models import Cuenta
from decimal import Decimal
import json

@login_required
def enviar_transferencia_view(request):
    """Vista para enviar una transferencia"""
    if request.method == 'POST':
        numero_cuenta_destino = request.POST.get('numero_cuenta_destino')
        monto = request.POST.get('monto')
        concepto = request.POST.get('concepto')

        try:
            monto_decimal = Decimal(monto)
            if monto_decimal <= 0:
                messages.error(request, 'El monto debe ser mayor a cero')
                return render(request, 'transferencia/enviar.html')
        except (ValueError, TypeError):
            messages.error(request, 'Monto inválido')
            return render(request, 'transferencia/enviar.html')

        # Verificar que la cuenta destino existe
        try:
            cuenta_destino = Cuenta.objects.get(numero_cuenta=numero_cuenta_destino, activa=True)
        except Cuenta.DoesNotExist:
            messages.error(request, 'La cuenta destino no existe o está inactiva')
            return render(request, 'transferencia/enviar.html')

        # Verificar que no se transfiera a la misma cuenta
        cuenta_origen = request.user.cuenta
        if cuenta_origen == cuenta_destino:
            messages.error(request, 'No puedes transferir a tu propia cuenta')
            return render(request, 'transferencia/enviar.html')

        # Verificar saldo suficiente
        if cuenta_origen.saldo_disponible < monto_decimal:
            messages.error(request, 'Saldo insuficiente para realizar la transferencia')
            return render(request, 'transferencia/enviar.html')

        # Crear la transferencia
        transferencia = Transferencia.objects.create(
            cuenta_origen=cuenta_origen,
            cuenta_destino=cuenta_destino,
            monto=monto_decimal,
            concepto=concepto
        )

        # Procesar la transferencia inmediatamente
        exito, mensaje = transferencia.procesar_transferencia()

        if exito:
            messages.success(request, f'Transferencia exitosa. Referencia: {transferencia.referencia}')
            return redirect('dashboard')
        else:
            messages.error(request, f'Error en la transferencia: {mensaje}')

    return render(request, 'transferencia/enviar.html')

@login_required
def detalle_transferencia_view(request, referencia):
    """Vista para ver el detalle de una transferencia específica"""
    cuenta_usuario = request.user.cuenta

    # Buscar la transferencia donde el usuario sea origen o destino
    transferencia = get_object_or_404(
        Transferencia,
        Q(cuenta_origen=cuenta_usuario) | Q(cuenta_destino=cuenta_usuario),
        referencia=referencia
    )

    # Determinar si es transferencia enviada o recibida
    es_enviada = transferencia.cuenta_origen == cuenta_usuario

    context = {
        'transferencia': transferencia,
        'es_enviada': es_enviada,
    }

    return render(request, 'transferencia/detalle.html', context)

@login_required
def listar_transferencias_view(request):
    """Vista para listar todas las transferencias del usuario"""
    cuenta_usuario = request.user.cuenta

    # Obtener todas las transferencias donde el usuario participe
    transferencias = Transferencia.objects.filter(
        Q(cuenta_origen=cuenta_usuario) | Q(cuenta_destino=cuenta_usuario)
    ).order_by('-fecha_creacion')

    # Agregar información adicional a cada transferencia
    transferencias_con_info = []
    for transferencia in transferencias:
        es_enviada = transferencia.cuenta_origen == cuenta_usuario
        transferencias_con_info.append({
            'transferencia': transferencia,
            'es_enviada': es_enviada,
            'cuenta_relacionada': transferencia.cuenta_destino if es_enviada else transferencia.cuenta_origen
        })

    context = {
        'transferencias_con_info': transferencias_con_info,
    }

    return render(request, 'transferencia/lista.html', context)

@require_http_methods(["GET"])
def consultar_transferencia_api(request, referencia):
    """
    API para consultar los datos de una transferencia por su número de referencia
    Retorna los datos en formato JSON
    """
    try:
        transferencia = Transferencia.objects.get(referencia=referencia)

        # Preparar los datos de respuesta
        data = {
            'success': True,
            'tipo': 'transferencia',
            'transferencia': {
                'referencia': transferencia.referencia,
                'monto': str(transferencia.monto),
                'concepto': transferencia.concepto,
                'estado': transferencia.estado,
                'estado_display': transferencia.get_estado_display(),
                'fecha_creacion': transferencia.fecha_creacion.isoformat(),
                'fecha_procesamiento': transferencia.fecha_procesamiento.isoformat() if transferencia.fecha_procesamiento else None,
                'cuenta_origen': {
                    'numero_cuenta': transferencia.cuenta_origen.numero_cuenta,
                    'usuario': transferencia.cuenta_origen.usuario.username,
                    'tipo_cuenta': transferencia.cuenta_origen.get_tipo_cuenta_display()
                },
                'cuenta_destino': {
                    'numero_cuenta': transferencia.cuenta_destino.numero_cuenta,
                    'usuario': transferencia.cuenta_destino.usuario.username,
                    'tipo_cuenta': transferencia.cuenta_destino.get_tipo_cuenta_display()
                }
            }
        }

        return JsonResponse(data, status=200)

    except Transferencia.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Transferencia no encontrada',
            'message': f'No existe una transferencia con la referencia: {referencia}',
            'tipo': 'transferencia',
            'transferencia': {
                'estado': 'NO_ENCONTRADA'
            }
        }, status=200)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def realizar_transferencia_api(request):
    """
    API para realizar una transferencia entre cuentas
    Recibe: cuenta_origen, cuenta_destino, monto, motivo
    Retorna: datos de la transferencia creada en formato JSON
    """
    try:
        # Parsear datos JSON del request
        data = json.loads(request.body)

        # Extraer parámetros requeridos
        numero_cuenta_origen = data.get('cuenta_origen')
        numero_cuenta_destino = data.get('cuenta_destino')
        monto = data.get('monto')
        motivo = data.get('motivo', '')

        # Validar que todos los parámetros requeridos estén presentes
        if not all([numero_cuenta_origen, numero_cuenta_destino, monto]):
            return JsonResponse({
                'success': False,
                'error': 'Parámetros faltantes',
                'message': 'Se requieren: cuenta_origen, cuenta_destino y monto'
            }, status=400)

        # Validar y convertir el monto
        try:
            monto_decimal = Decimal(str(monto))
            if monto_decimal <= 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Monto inválido',
                    'message': 'El monto debe ser mayor a cero'
                }, status=400)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Monto inválido',
                'message': 'El formato del monto es incorrecto'
            }, status=400)

        # Verificar que las cuentas existen y están activas
        try:
            cuenta_origen = Cuenta.objects.get(numero_cuenta=numero_cuenta_origen, activa=True)
        except Cuenta.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Cuenta origen no encontrada',
                'message': f'No existe una cuenta activa con el número: {numero_cuenta_origen}'
            }, status=404)

        try:
            cuenta_destino = Cuenta.objects.get(numero_cuenta=numero_cuenta_destino, activa=True)
        except Cuenta.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Cuenta destino no encontrada',
                'message': f'No existe una cuenta activa con el número: {numero_cuenta_destino}'
            }, status=404)

        # Verificar que no se transfiera a la misma cuenta
        if cuenta_origen == cuenta_destino:
            return JsonResponse({
                'success': False,
                'error': 'Transferencia inválida',
                'message': 'No se puede transferir a la misma cuenta'
            }, status=400)

        # Verificar saldo suficiente
        if cuenta_origen.saldo_disponible < monto_decimal:
            return JsonResponse({
                'success': False,
                'error': 'Saldo insuficiente',
                'message': f'Saldo disponible: {cuenta_origen.saldo_disponible}, Monto solicitado: {monto_decimal}'
            }, status=400)

        # Crear la transferencia
        transferencia = Transferencia.objects.create(
            cuenta_origen=cuenta_origen,
            cuenta_destino=cuenta_destino,
            monto=monto_decimal,
            concepto=motivo
        )

        # Procesar la transferencia inmediatamente
        exito, mensaje = transferencia.procesar_transferencia()

        if exito:
            # Preparar respuesta exitosa con todos los datos de la transferencia
            response_data = {
                'success': True,
                'message': 'Transferencia realizada exitosamente',
                'transferencia': {
                    'referencia': transferencia.referencia,
                    'monto': str(transferencia.monto),
                    'concepto': transferencia.concepto,
                    'estado': transferencia.estado,
                    'estado_display': transferencia.get_estado_display(),
                    'fecha_creacion': transferencia.fecha_creacion.isoformat(),
                    'fecha_procesamiento': transferencia.fecha_procesamiento.isoformat() if transferencia.fecha_procesamiento else None,
                    'cuenta_origen': {
                        'numero_cuenta': transferencia.cuenta_origen.numero_cuenta,
                        'usuario': transferencia.cuenta_origen.usuario.username,
                        'saldo_actual': str(transferencia.cuenta_origen.saldo_disponible)
                    },
                    'cuenta_destino': {
                        'numero_cuenta': transferencia.cuenta_destino.numero_cuenta,
                        'usuario': transferencia.cuenta_destino.usuario.username,
                        'saldo_actual': str(transferencia.cuenta_destino.saldo_disponible)
                    }
                }
            }
            return JsonResponse(response_data, status=201)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Error al procesar transferencia',
                'message': mensaje,
                'transferencia': {
                    'referencia': transferencia.referencia,
                    'estado': transferencia.estado
                }
            }, status=400)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Formato JSON inválido',
            'message': 'El cuerpo de la petición debe ser un JSON válido'
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor',
            'message': str(e)
        }, status=500)
