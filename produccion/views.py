from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum, F
from .models import Cliente, OrdenProduccion, DetalleOrden, RegistroTrabajo
from .forms import ClienteForm, OrdenProduccionForm, DetalleOrdenForm, RegistroTrabajoForm
from empleados.models import Empleado


# ─── Cliente ───

def cliente_lista(request):
    clientes = Cliente.objects.all().order_by('nombre')
    return render(request, 'produccion/cliente_lista.html', {'clientes': clientes})


def cliente_crear(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente creado exitosamente.')
            return redirect('produccion:cliente_lista')
    else:
        form = ClienteForm()
    return render(request, 'produccion/cliente_form.html', {'form': form, 'titulo': 'Crear Cliente'})


def cliente_editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado exitosamente.')
            return redirect('produccion:cliente_lista')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'produccion/cliente_form.html', {'form': form, 'titulo': 'Editar Cliente'})


def cliente_eliminar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente eliminado exitosamente.')
        return redirect('produccion:cliente_lista')
    return render(request, 'produccion/cliente_confirmar_eliminar.html', {'cliente': cliente})


# ─── OrdenProduccion ───

def orden_lista(request):
    ordenes = OrdenProduccion.objects.select_related('cliente').all().order_by('-fecha_creacion')
    return render(request, 'produccion/orden_lista.html', {'ordenes': ordenes})


def orden_crear(request):
    if request.method == 'POST':
        form = OrdenProduccionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Orden de producción creada exitosamente.')
            return redirect('produccion:orden_lista')
    else:
        form = OrdenProduccionForm()
    return render(request, 'produccion/orden_form.html', {'form': form, 'titulo': 'Crear Orden de Producción'})


def orden_detalle(request, pk):
    orden = get_object_or_404(OrdenProduccion, pk=pk)
    detalles = orden.detalles.select_related('referencia').all()
    return render(request, 'produccion/orden_detalle.html', {'orden': orden, 'detalles': detalles})


def orden_editar(request, pk):
    orden = get_object_or_404(OrdenProduccion, pk=pk)
    if request.method == 'POST':
        form = OrdenProduccionForm(request.POST, instance=orden)
        if form.is_valid():
            form.save()
            messages.success(request, 'Orden actualizada exitosamente.')
            return redirect('produccion:orden_detalle', pk=orden.pk)
    else:
        form = OrdenProduccionForm(instance=orden)
    return render(request, 'produccion/orden_form.html', {'form': form, 'titulo': 'Editar Orden'})


def orden_eliminar(request, pk):
    orden = get_object_or_404(OrdenProduccion, pk=pk)
    if request.method == 'POST':
        orden.delete()
        messages.success(request, 'Orden eliminada exitosamente.')
        return redirect('produccion:orden_lista')
    return render(request, 'produccion/orden_confirmar_eliminar.html', {'orden': orden})


# ─── DetalleOrden (hijo de orden) ───

def detalle_agregar(request, orden_pk):
    orden = get_object_or_404(OrdenProduccion, pk=orden_pk)
    if request.method == 'POST':
        form = DetalleOrdenForm(request.POST)
        if form.is_valid():
            detalle = form.save(commit=False)
            detalle.orden = orden
            detalle.save()
            messages.success(request, 'Referencia agregada a la orden.')
            return redirect('produccion:orden_detalle', pk=orden.pk)
    else:
        form = DetalleOrdenForm()
    return render(request, 'produccion/detalle_form.html', {
        'form': form,
        'orden': orden,
        'titulo': f'Agregar Referencia a Orden #{orden.pk}',
    })


def detalle_eliminar(request, pk):
    detalle = get_object_or_404(DetalleOrden, pk=pk)
    orden_pk = detalle.orden.pk
    if request.method == 'POST':
        detalle.delete()
        messages.success(request, 'Referencia removida de la orden.')
        return redirect('produccion:orden_detalle', pk=orden_pk)
    return render(request, 'produccion/detalle_confirmar_eliminar.html', {'detalle': detalle})


# ─── RegistroTrabajo ───

def registro_agregar(request, detalle_pk):
    detalle = get_object_or_404(DetalleOrden.objects.select_related('referencia', 'orden'), pk=detalle_pk)
    if request.method == 'POST':
        form = RegistroTrabajoForm(request.POST)
        if form.is_valid():
            registro = form.save(commit=False)
            registro.detalle_orden = detalle
            registro.save()
            messages.success(request, 'Registro de trabajo guardado.')
            return redirect('produccion:orden_detalle', pk=detalle.orden.pk)
    else:
        form = RegistroTrabajoForm()
        # Filtrar solo los procesos que corresponden a la referencia del detalle
        form.fields['proceso_referencia'].queryset = detalle.referencia.procesos.select_related('proceso_base')
    return render(request, 'produccion/registro_form.html', {
        'form': form,
        'detalle': detalle,
        'titulo': f'Registrar Trabajo - {detalle.referencia.codigo} (Orden #{detalle.orden.pk})',
    })


def registro_eliminar(request, pk):
    registro = get_object_or_404(RegistroTrabajo, pk=pk)
    orden_pk = registro.detalle_orden.orden.pk
    if request.method == 'POST':
        registro.delete()
        messages.success(request, 'Registro de trabajo eliminado.')
        return redirect('produccion:orden_detalle', pk=orden_pk)
    return render(request, 'produccion/registro_confirmar_eliminar.html', {'registro': registro})


# ─── Nómina ───

def nomina(request):
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    resultados = []

    if fecha_desde and fecha_hasta:
        resultados = (
            RegistroTrabajo.objects
            .filter(fecha__range=[fecha_desde, fecha_hasta])
            .values('empleado__id', 'empleado__nombre')
            .annotate(
                total_pares=Sum('cantidad_realizada'),
                total_pago=Sum(F('cantidad_realizada') * F('proceso_referencia__precio_mano_obra')),
            )
            .order_by('empleado__nombre')
        )

    return render(request, 'produccion/nomina.html', {
        'resultados': resultados,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    })


def nomina_detalle_empleado(request, empleado_pk):
    empleado = get_object_or_404(Empleado, pk=empleado_pk)
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    registros = []

    if fecha_desde and fecha_hasta:
        registros = (
            RegistroTrabajo.objects
            .filter(empleado=empleado, fecha__range=[fecha_desde, fecha_hasta])
            .select_related('detalle_orden__orden', 'detalle_orden__referencia', 'proceso_referencia__proceso_base')
            .order_by('-fecha')
        )

    return render(request, 'produccion/nomina_detalle.html', {
        'empleado': empleado,
        'registros': registros,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    })
