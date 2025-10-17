from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Cuenta
from transferencia.models import Transferencia
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
import json

def login_view(request):
    """Vista para el login de usuarios"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'cuenta/login.html')

def register_view(request):
    """Vista para registro de nuevos usuarios"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Crear cuenta automáticamente para el nuevo usuario
            Cuenta.objects.create(usuario=user, saldo_disponible=5000000.00)  # Saldo inicial de $5000000
            messages.success(request, 'Usuario creado exitosamente. Se ha creado tu cuenta con $5000000 de saldo inicial.')
            return redirect('login')
    else:
        form = UserCreationForm()

    return render(request, 'cuenta/register.html', {'form': form})

@login_required
def dashboard_view(request):
    """Vista principal del dashboard del usuario"""
    try:
        cuenta = request.user.cuenta
    except Cuenta.DoesNotExist:
        # Si el usuario no tiene cuenta, crear una
        cuenta = Cuenta.objects.create(usuario=request.user, saldo_disponible=5000000.00)

    # Obtener últimas transferencias (enviadas y recibidas)
    transferencias_enviadas = Transferencia.objects.filter(cuenta_origen=cuenta)[:5]
    transferencias_recibidas = Transferencia.objects.filter(cuenta_destino=cuenta)[:5]

    context = {
        'cuenta': cuenta,
        'transferencias_enviadas': transferencias_enviadas,
        'transferencias_recibidas': transferencias_recibidas,
    }

    return render(request, 'cuenta/dashboard.html', context)

@login_required
def logout_view(request):
    """Vista para cerrar sesión"""
    logout(request)
    messages.success(request, 'Sesión cerrada exitosamente')
    return redirect('login')

@login_required
def historial_view(request):
    """Vista para ver el historial completo de transferencias"""
    cuenta = request.user.cuenta
    transferencias_enviadas = Transferencia.objects.filter(cuenta_origen=cuenta)
    transferencias_recibidas = Transferencia.objects.filter(cuenta_destino=cuenta)

    context = {
        'cuenta': cuenta,
        'transferencias_enviadas': transferencias_enviadas,
        'transferencias_recibidas': transferencias_recibidas,
    }

    return render(request, 'cuenta/historial.html', context)

@csrf_exempt
@require_POST
def api_register(request):
    """
    Body JSON:
    {
      "username": "usuario",
      "password": "secret",
      "saldo_inicial": "5000000.00"  # opcional
    }
    """
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON inválido"}, status=400)

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    saldo_inicial = data.get("saldo_inicial")

    if not username or not password:
        return JsonResponse({"detail": "username y password son obligatorios"}, status=400)
    if User.objects.filter(username=username).exists():
        return JsonResponse({"detail": "El usuario ya existe"}, status=409)

    # Opcional: validar fortaleza de contraseña
    # from django.contrib.auth.password_validation import validate_password
    # from django.core.exceptions import ValidationError
    # try:
    #     validate_password(password)
    # except ValidationError as e:
    #     return JsonResponse({"detail": e.messages}, status=400)

    try:
        user = User.objects.create_user(username=username, password=password)
        saldo = Decimal(str(saldo_inicial)) if saldo_inicial is not None else Decimal("5000000.00")
        cuenta = Cuenta.objects.create(usuario=user, saldo_disponible=saldo)
    except Exception:
        return JsonResponse({"detail": "No se pudo crear el usuario/cuenta"}, status=500)

    return JsonResponse(
        {
            "user": {"id": user.id, "username": user.username},
            "cuenta": {"id": cuenta.id, "saldo_disponible": str(cuenta.saldo_disponible)},
        },
        status=201,
    )


# ...existing code...

@require_GET
def api_transferencias_enviadas(request):
    #ejemplo: /cuenta/api/transferencias/enviadas/?username=karen
    username = (request.GET.get("username") or "").strip()
    if not username:
        return JsonResponse({"detail": "username es requerido"}, status=400)

    try:
        user = User.objects.get(username=username)
        cuenta = user.cuenta
    except User.DoesNotExist:
        return JsonResponse({"detail": "Usuario no existe"}, status=404)
    except Cuenta.DoesNotExist:
        return JsonResponse({"detail": "El usuario no tiene cuenta"}, status=404)

    qs = Transferencia.objects.filter(cuenta_origen=cuenta).order_by("-id")
    data = list(qs.values())
    return JsonResponse({"count": len(data), "results": data}, status=200)


@require_GET
def api_transferencias_recibidas(request):
    username = (request.GET.get("username") or "").strip()
    if not username:
        return JsonResponse({"detail": "username es requerido"}, status=400)

    try:
        user = User.objects.get(username=username)
        cuenta = user.cuenta
    except User.DoesNotExist:
        return JsonResponse({"detail": "Usuario no existe"}, status=404)
    except Cuenta.DoesNotExist:
        return JsonResponse({"detail": "El usuario no tiene cuenta"}, status=404)

    qs = Transferencia.objects.filter(cuenta_destino=cuenta).order_by("-id")
    data = list(qs.values())
    return JsonResponse({"count": len(data), "results": data}, status=200)