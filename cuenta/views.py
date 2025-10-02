from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Cuenta
from transferencia.models import Transferencia

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
            Cuenta.objects.create(usuario=user, saldo_disponible=1000.00)  # Saldo inicial de $1000
            messages.success(request, 'Usuario creado exitosamente. Se ha creado tu cuenta con $1000 de saldo inicial.')
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
        cuenta = Cuenta.objects.create(usuario=request.user, saldo_disponible=1000.00)

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
