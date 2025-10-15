from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import TarjetaCredito
from cuenta.models import Cuenta
import json

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import json
import uuid

from .models import TarjetaCredito, TransaccionTarjeta


@login_required
def solicitar_tarjeta_view(request):
    """Vista para solicitar una nueva tarjeta de crédito"""
    # Verificar si el usuario ya tiene una tarjeta activa
    tarjeta_existente = TarjetaCredito.objects.filter(
        usuario=request.user,
        estado__in=['ACTIVA', 'BLOQUEADA']
    ).first()

    if tarjeta_existente:
        messages.warning(request, 'Ya tienes una tarjeta de crédito activa.')
        return redirect('mis_tarjetas')

    if request.method == 'POST':
        marca_seleccionada = request.POST.get('marca', 'CABAL')
        limite_solicitado = request.POST.get('limite_credito', 50000)

        try:
            # Validar límite solicitado
            limite_decimal = float(limite_solicitado)
            if limite_decimal < 10000 or limite_decimal > 500000:
                messages.error(request, 'El límite de crédito debe estar entre $10,000 y $500,000')
                return render(request, 'tarjeta_credito/solicitar.html')

            # Crear la nueva tarjeta
            nueva_tarjeta = TarjetaCredito.objects.create(
                usuario=request.user,
                marca=marca_seleccionada,
                limite_credito=limite_decimal,
                credito_disponible=limite_decimal
            )

            messages.success(
                request,
                f'¡Tarjeta creada exitosamente! Tu nueva tarjeta {nueva_tarjeta.get_marca_display()} '
                f'terminada en {nueva_tarjeta.ultimos_4_digitos} está lista para usar.'
            )
            return redirect('detalle_tarjeta', tarjeta_id=nueva_tarjeta.id)

        except ValueError:
            messages.error(request, 'Límite de crédito inválido')
        except Exception as e:
            messages.error(request, f'Error al crear la tarjeta: {str(e)}')

    context = {
        'marcas': TarjetaCredito.MARCA_CHOICES
    }
    return render(request, 'tarjeta_credito/solicitar.html', context)


@login_required
def mis_tarjetas_view(request):
    """Vista para listar las tarjetas del usuario"""
    tarjetas = TarjetaCredito.objects.filter(usuario=request.user)

    # Actualizar estados de tarjetas vencidas
    for tarjeta in tarjetas:
        tarjeta.actualizar_estado_si_vencida()

    context = {
        'tarjetas': tarjetas
    }
    return render(request, 'tarjeta_credito/mis_tarjetas.html', context)


@login_required
def detalle_tarjeta_view(request, tarjeta_id):
    """Vista para ver el detalle de una tarjeta específica"""
    tarjeta = get_object_or_404(TarjetaCredito, id=tarjeta_id, usuario=request.user)
    tarjeta.actualizar_estado_si_vencida()

    context = {
        'tarjeta': tarjeta
    }
    return render(request, 'tarjeta_credito/detalle.html', context)


@login_required
@require_http_methods(["POST"])
def bloquear_tarjeta_view(request, tarjeta_id):
    """Vista para bloquear una tarjeta"""
    tarjeta = get_object_or_404(TarjetaCredito, id=tarjeta_id, usuario=request.user)

    exito, mensaje = tarjeta.bloquear_tarjeta()

    if exito:
        messages.success(request, mensaje)
    else:
        messages.error(request, mensaje)

    return redirect('detalle_tarjeta', tarjeta_id=tarjeta.id)


@login_required
@require_http_methods(["POST"])
def desbloquear_tarjeta_view(request, tarjeta_id):
    """Vista para desbloquear una tarjeta"""
    tarjeta = get_object_or_404(TarjetaCredito, id=tarjeta_id, usuario=request.user)

    exito, mensaje = tarjeta.desbloquear_tarjeta()

    if exito:
        messages.success(request, mensaje)
    else:
        messages.error(request, mensaje)

    return redirect('detalle_tarjeta', tarjeta_id=tarjeta.id)


# API Endpoints
@csrf_exempt
@require_http_methods(["POST"])
def solicitar_tarjeta_api(request):
    """
    API para solicitar una nueva tarjeta de crédito
    Recibe: marca, limite_credito (opcional)
    """
    try:
        # Verificar autenticación (en un sistema real usarías tokens)
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'No autenticado',
                'message': 'Debes estar autenticado para solicitar una tarjeta'
            }, status=401)

        # Parsear datos JSON
        data = json.loads(request.body)
        marca = data.get('marca', 'CABAL')
        limite_credito = data.get('limite_credito', 50000)

        # Verificar si el usuario ya tiene una tarjeta activa
        tarjeta_existente = TarjetaCredito.objects.filter(
            usuario=request.user,
            estado__in=['ACTIVA', 'BLOQUEADA']
        ).first()

        if tarjeta_existente:
            return JsonResponse({
                'success': False,
                'error': 'Tarjeta existente',
                'message': 'Ya tienes una tarjeta de crédito activa'
            }, status=400)

        # Validar marca
        marcas_validas = [choice[0] for choice in TarjetaCredito.MARCA_CHOICES]
        if marca not in marcas_validas:
            return JsonResponse({
                'success': False,
                'error': 'Marca inválida',
                'message': f'Las marcas válidas son: {", ".join(marcas_validas)}'
            }, status=400)

        # Validar límite de crédito
        try:
            limite_decimal = float(limite_credito)
            if limite_decimal < 10000 or limite_decimal > 500000:
                return JsonResponse({
                    'success': False,
                    'error': 'Límite inválido',
                    'message': 'El límite de crédito debe estar entre $10,000 y $500,000'
                }, status=400)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Límite inválido',
                'message': 'El formato del límite de crédito es incorrecto'
            }, status=400)

        # Crear la nueva tarjeta
        nueva_tarjeta = TarjetaCredito.objects.create(
            usuario=request.user,
            marca=marca,
            limite_credito=limite_decimal,
            credito_disponible=limite_decimal
        )

        # Preparar respuesta
        response_data = {
            'success': True,
            'message': 'Tarjeta de crédito creada exitosamente',
            'tarjeta': {
                'id': nueva_tarjeta.id,
                'numero_enmascarado': nueva_tarjeta.numero_enmascarado,
                'marca': nueva_tarjeta.marca,
                'marca_display': nueva_tarjeta.get_marca_display(),
                'ultimos_4_digitos': nueva_tarjeta.ultimos_4_digitos,
                'fecha_vencimiento': nueva_tarjeta.fecha_vencimiento.isoformat(),
                'estado': nueva_tarjeta.estado,
                'estado_display': nueva_tarjeta.get_estado_display(),
                'limite_credito': str(nueva_tarjeta.limite_credito),
                'credito_disponible': str(nueva_tarjeta.credito_disponible),
                'fecha_creacion': nueva_tarjeta.fecha_creacion.isoformat()
            }
        }

        return JsonResponse(response_data, status=201)

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


@require_http_methods(["GET"])
def consultar_tarjeta_api(request, tarjeta_id):
    """
    API para consultar los datos de una tarjeta de crédito
    """
    try:
        # En un sistema real verificarías la autenticación y autorización
        tarjeta = TarjetaCredito.objects.get(id=tarjeta_id)
        tarjeta.actualizar_estado_si_vencida()

        # Preparar datos de respuesta (sin mostrar datos sensibles)
        data = {
            'success': True,
            'tarjeta': {
                'id': tarjeta.id,
                'numero_enmascarado': tarjeta.numero_enmascarado,
                'marca': tarjeta.marca,
                'marca_display': tarjeta.get_marca_display(),
                'ultimos_4_digitos': tarjeta.ultimos_4_digitos,
                'fecha_vencimiento': tarjeta.fecha_vencimiento.isoformat(),
                'estado': tarjeta.estado,
                'estado_display': tarjeta.get_estado_display(),
                'limite_credito': str(tarjeta.limite_credito),
                'credito_disponible': str(tarjeta.credito_disponible),
                'credito_utilizado': str(tarjeta.credito_utilizado),
                'esta_vencida': tarjeta.esta_vencida,
                'fecha_creacion': tarjeta.fecha_creacion.isoformat(),
                'usuario': tarjeta.usuario.username
            }
        }

        return JsonResponse(data, status=200)

    except TarjetaCredito.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Tarjeta no encontrada',
            'message': f'No existe una tarjeta con el ID: {tarjeta_id}'
        }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor',
            'message': str(e)
        }, status=500)


@require_http_methods(["GET"])
def consultar_tarjeta_por_numero_api(request, numero_tarjeta):
    """
    API para consultar una tarjeta de crédito por su número
    Retorna el identificador único de la tarjeta si existe
    """
    try:
        # Buscar la tarjeta por número
        tarjeta = TarjetaCredito.objects.get(numero_tarjeta=numero_tarjeta)

        # Preparar datos de respuesta con identificador único
        data = {
            'success': True,
            'encontrada': True,
            'message': 'Tarjeta encontrada exitosamente',
            'tarjeta': {
                'identificador_unico': str(tarjeta.identificador_unico),
                'numero_enmascarado': tarjeta.numero_enmascarado,
                'marca': tarjeta.marca,
                'marca_display': tarjeta.get_marca_display(),
                'estado': tarjeta.estado,
                'estado_display': tarjeta.get_estado_display(),
                'usuario': tarjeta.usuario.username
            }
        }

        return JsonResponse(data, status=200)

    except TarjetaCredito.DoesNotExist:
        return JsonResponse({
            'success': False,
            'encontrada': False,
            'error': 'Tarjeta no encontrada',
            'message': f'No existe una tarjeta con el número: {numero_tarjeta}',
            'tarjeta': None
        }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'encontrada': False,
            'error': 'Error interno del servidor',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def consultar_tarjeta_por_datos_api(request):
    """
    API para consultar una tarjeta de crédito por últimos 4 dígitos, CVC y fecha de vencimiento
    Recibe: ultimos_4_digitos, cvc, fecha_vencimiento
    Retorna los datos completos de la tarjeta si existe
    """
    try:
        # Parsear datos JSON
        data = json.loads(request.body)
        ultimos_4_digitos = data.get('ultimos_4_digitos')
        cvc = data.get('cvc')
        fecha_vencimiento_str = data.get('fecha_vencimiento')

        # Validar que todos los campos estén presentes
        if not all([ultimos_4_digitos, cvc, fecha_vencimiento_str]):
            return JsonResponse({
                'success': False,
                'encontrada': False,
                'error': 'Datos incompletos',
                'message': 'Se requieren los últimos 4 dígitos, CVC y fecha de vencimiento'
            }, status=400)

        # Validar formato de últimos 4 dígitos
        if len(ultimos_4_digitos) != 4 or not ultimos_4_digitos.isdigit():
            return JsonResponse({
                'success': False,
                'encontrada': False,
                'error': 'Formato inválido',
                'message': 'Los últimos 4 dígitos deben ser exactamente 4 números'
            }, status=400)

        # Validar formato de CVC (3 o 4 dígitos)
        if len(cvc) < 3 or len(cvc) > 4 or not cvc.isdigit():
            return JsonResponse({
                'success': False,
                'encontrada': False,
                'error': 'Formato inválido',
                'message': 'El CVC debe tener entre 3 y 4 dígitos'
            }, status=400)

        # Convertir fecha de string a objeto date
        try:
            from datetime import datetime
            fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'success': False,
                'encontrada': False,
                'error': 'Formato de fecha inválido',
                'message': 'La fecha debe tener el formato YYYY-MM-DD'
            }, status=400)

        # Buscar la tarjeta por los criterios especificados
        tarjeta = TarjetaCredito.objects.filter(
            ultimos_4_digitos=ultimos_4_digitos,
            cvc=cvc,
            fecha_vencimiento=fecha_vencimiento
        ).first()

        if tarjeta:
            # Actualizar estado si está vencida
            tarjeta.actualizar_estado_si_vencida()

            # Preparar datos de respuesta completos
            data = {
                'success': True,
                'encontrada': True,
                'message': 'Tarjeta encontrada exitosamente',
                'tarjeta': {
                    'identificador_unico': str(tarjeta.identificador_unico),
                    'numero_enmascarado': tarjeta.numero_enmascarado,
                    'ultimos_4_digitos': tarjeta.ultimos_4_digitos,
                    'marca': tarjeta.marca,
                    'marca_display': tarjeta.get_marca_display(),
                    'fecha_vencimiento': tarjeta.fecha_vencimiento.isoformat(),
                    'estado': tarjeta.estado,
                    'estado_display': tarjeta.get_estado_display(),
                    'limite_credito': float(tarjeta.limite_credito),
                    'credito_disponible': float(tarjeta.credito_disponible),
                    'fecha_creacion': tarjeta.fecha_creacion.isoformat(),
                    'usuario': tarjeta.usuario.username
                }
            }

            return JsonResponse(data, status=200)
        else:
            return JsonResponse({
                'success': False,
                'encontrada': False,
                'error': 'Tarjeta no encontrada',
                'message': 'No se encontró una tarjeta con los datos proporcionados',
                'tarjeta': None
            }, status=404)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'encontrada': False,
            'error': 'JSON inválido',
            'message': 'El formato de los datos enviados no es válido'
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'encontrada': False,
            'error': 'Error interno del servidor',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def pagar_con_tarjeta(request):
    """
    Endpoint para realizar un pago con tarjeta de crédito.
    Recibe: id_tarjeta, monto
    Retorna: éxito/error, datos de la tarjeta, id de transacción
    """
    try:
        data = json.loads(request.body)
        id_tarjeta = data.get('id_tarjeta')
        monto = data.get('monto')
        descripcion = data.get('descripcion', '')

        # Validaciones básicas
        if not id_tarjeta:
            return JsonResponse({
                'success': False,
                'error': 'ID de tarjeta requerido',
                'message': 'Debe proporcionar el ID de la tarjeta'
            }, status=400)

        if not monto:
            return JsonResponse({
                'success': False,
                'error': 'Monto requerido',
                'message': 'Debe proporcionar el monto a pagar'
            }, status=400)

        try:
            monto_decimal = Decimal(str(monto))
            if monto_decimal <= 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Monto inválido',
                    'message': 'El monto debe ser mayor a 0'
                }, status=400)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Monto inválido',
                'message': 'El formato del monto es incorrecto'
            }, status=400)

        # Buscar la tarjeta
        try:
            tarjeta = TarjetaCredito.objects.get(identificador_unico=id_tarjeta, estado='ACTIVA')
        except TarjetaCredito.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Tarjeta no encontrada',
                'message': 'La tarjeta especificada no existe o está inactiva'
            }, status=404)

        # Validar saldo disponible
        if tarjeta.credito_disponible < monto_decimal:
            return JsonResponse({
                'success': False,
                'error': 'Saldo insuficiente',
                'message': f'Saldo disponible: ${tarjeta.credito_disponible}, Monto solicitado: ${monto_decimal}',
                'saldo_disponible': float(tarjeta.credito_disponible)
            }, status=400)

        # Crear transacción y actualizar saldo
        with transaction.atomic():
            # Crear la transacción
            nueva_transaccion = TransaccionTarjeta.objects.create(
                tarjeta=tarjeta,
                monto=monto_decimal,
                descripcion=descripcion,
                estado='pendiente'
            )

            # Actualizar saldo disponible
            tarjeta.credito_disponible -= monto_decimal
            tarjeta.save()

        return JsonResponse({
            'success': True,
            'message': 'Pago realizado exitosamente',
            'data': {
                'id_transaccion': str(nueva_transaccion.id_transaccion),
                'tarjeta': {
                    'id': str(tarjeta.identificador_unico),
                    'marca': tarjeta.marca,
                    'ultimos_4_digitos': tarjeta.ultimos_4_digitos,
                    'saldo_disponible_anterior': float(tarjeta.credito_disponible + monto_decimal),
                    'saldo_disponible_actual': float(tarjeta.credito_disponible)
                },
                'transaccion': {
                    'monto': float(monto_decimal),
                    'fecha': nueva_transaccion.fecha_pago.isoformat(),
                    'estado': nueva_transaccion.estado,
                    'descripcion': descripcion
                }
            }
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido',
            'message': 'El formato de los datos enviados es incorrecto'
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error interno',
            'message': 'Ocurrió un error al procesar el pago'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def cobrar_transaccion(request):
    """
    Endpoint para cobrar una transacción pendiente.
    Recibe: id_transaccion, numero_cuenta_destino
    Retorna: éxito/error, datos de la transacción cobrada
    """
    try:
        data = json.loads(request.body)
        id_transaccion = data.get('id_transaccion')
        numero_cuenta_destino = data.get('numero_cuenta_destino')

        # Validaciones básicas
        if not id_transaccion:
            return JsonResponse({
                'success': False,
                'error': 'ID de transacción requerido',
                'message': 'Debe proporcionar el ID de la transacción'
            }, status=400)

        if not numero_cuenta_destino:
            return JsonResponse({
                'success': False,
                'error': 'Número de cuenta requerido',
                'message': 'Debe proporcionar el número de cuenta destino'
            }, status=400)

        # Buscar la transacción
        try:
            transaccion = TransaccionTarjeta.objects.get(id_transaccion=id_transaccion)
        except TransaccionTarjeta.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Transacción no encontrada',
                'message': 'La transacción especificada no existe'
            }, status=404)

        # Validar que la transacción esté pendiente
        if transaccion.estado != 'pendiente':
            return JsonResponse({
                'success': False,
                'error': 'Transacción no válida',
                'message': f'La transacción ya está en estado: {transaccion.estado}',
                'estado_actual': transaccion.estado
            }, status=400)

        # Validar que la cuenta destino exista
        try:
            cuenta_destino = Cuenta.objects.get(numero_cuenta=numero_cuenta_destino, activa=True)
        except Cuenta.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Cuenta destino no encontrada',
                'message': 'La cuenta destino especificada no existe o está inactiva'
            }, status=404)
        
        # Actualizar la transacción
        with transaction.atomic():
            transaccion.estado = 'cobrada'
            transaccion.fecha_cobro = timezone.now()
            transaccion.numero_cuenta_destino = numero_cuenta_destino
            transaccion.save()

            # Acreditar a cuenta destino
            cuenta_destino.saldo_disponible += transaccion.monto
            cuenta_destino.save()

        return JsonResponse({
            'success': True,
            'message': 'Transacción cobrada exitosamente',
            'data': {
                'transaccion': {
                    'id': str(transaccion.id_transaccion),
                    'monto': float(transaccion.monto),
                    'estado': transaccion.estado,
                    'fecha_pago': transaccion.fecha_pago.isoformat(),
                    'fecha_cobro': transaccion.fecha_cobro.isoformat(),
                    'numero_cuenta_destino': transaccion.numero_cuenta_destino,
                    'descripcion': transaccion.descripcion
                },
                'tarjeta': {
                    'marca': transaccion.tarjeta.marca,
                    'ultimos_4_digitos': transaccion.tarjeta.ultimos_4_digitos
                }
            }
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido',
            'message': 'El formato de los datos enviados es incorrecto'
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error interno',
            'message': 'Ocurrió un error al procesar el cobro'
        }, status=500)


@require_http_methods(["GET"])
def consultar_transaccion(request, id_transaccion):
    """
    Endpoint para consultar el estado de una transacción.
    """
    try:
        transaccion = TransaccionTarjeta.objects.get(id_transaccion=id_transaccion)

        data = {
            'success': True,
            'data': {
                'transaccion': {
                    'id': str(transaccion.id_transaccion),
                    'monto': float(transaccion.monto),
                    'estado': transaccion.estado,
                    'fecha_pago': transaccion.fecha_pago.isoformat(),
                    'fecha_cobro': transaccion.fecha_cobro.isoformat() if transaccion.fecha_cobro else None,
                    'numero_cuenta_destino': transaccion.numero_cuenta_destino,
                    'descripcion': transaccion.descripcion
                },
                'tarjeta': {
                    'marca': transaccion.tarjeta.marca,
                    'ultimos_4_digitos': transaccion.tarjeta.ultimos_4_digitos
                }
            }
        }

        return JsonResponse(data, status=200)

    except TransaccionTarjeta.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Transacción no encontrada',
            'message': 'La transacción especificada no existe'
        }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error interno',
            'message': 'Ocurrió un error al consultar la transacción'
        }, status=500)
