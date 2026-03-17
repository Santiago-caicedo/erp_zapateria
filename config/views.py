from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.db.models import Count, Sum, F, Q
from empleados.models import Empleado
from inventario.models import Material, ProcesoBase, Referencia
from produccion.models import Cliente, OrdenProduccion, RegistroTrabajo


def dashboard(request):
    ordenes_por_estado = {
        'pendientes': OrdenProduccion.objects.filter(estado='Pendiente').count(),
        'en_proceso': OrdenProduccion.objects.filter(estado='En Proceso').count(),
        'finalizados': OrdenProduccion.objects.filter(estado='Finalizado').count(),
        'entregados': OrdenProduccion.objects.filter(estado='Entregado').count(),
    }

    ultimas_ordenes = (
        OrdenProduccion.objects
        .select_related('cliente', 'referencia')
        .order_by('-numero')[:5]
    )

    context = {
        'total_empleados': Empleado.objects.count(),
        'total_materiales': Material.objects.count(),
        'total_referencias': Referencia.objects.count(),
        'total_clientes': Cliente.objects.count(),
        'total_ordenes': OrdenProduccion.objects.count(),
        'ordenes_por_estado': ordenes_por_estado,
        'ultimas_ordenes': ultimas_ordenes,
    }
    return render(request, 'dashboard.html', context)


def cerrar_sesion(request):
    auth_logout(request)
    return redirect('login')
