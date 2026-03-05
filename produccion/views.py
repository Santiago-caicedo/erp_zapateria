from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum, F
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML
from .models import Cliente, OrdenProduccion, RegistroTrabajo
from .forms import ClienteForm, OrdenProduccionForm, OrdenEditarForm, RegistroTrabajoForm
from empleados.models import Empleado
from inventario.models import Referencia


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
    ordenes = (
        OrdenProduccion.objects
        .select_related('cliente', 'referencia__tipo_zapato')
        .all()
        .order_by('-numero')
    )
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
    return render(request, 'produccion/orden_form.html', {
        'form': form, 'titulo': 'Crear Orden de Producción',
    })


def orden_detalle(request, pk):
    orden = get_object_or_404(
        OrdenProduccion.objects.select_related('cliente', 'referencia__tipo_zapato'),
        pk=pk,
    )
    consumos = orden.referencia.consumos.select_related('material__tipo').all()
    procesos = orden.referencia.procesos.select_related('proceso_base').all()
    registros = orden.registros_trabajo.select_related(
        'empleado', 'proceso_referencia__proceso_base'
    ).order_by('-fecha')

    # Calcular material necesario por la cantidad total
    materiales_necesarios = []
    for c in consumos:
        materiales_necesarios.append({
            'material': c.material,
            'cantidad_unitaria': c.cantidad_consumida,
            'cantidad_total': c.cantidad_consumida * orden.cantidad_total,
        })

    tallas = []
    for t in range(34, 41):
        val = getattr(orden, f'talla_{t}')
        if val > 0:
            tallas.append({'numero': t, 'cantidad': val})

    return render(request, 'produccion/orden_detalle.html', {
        'orden': orden,
        'consumos': consumos,
        'materiales_necesarios': materiales_necesarios,
        'procesos': procesos,
        'registros': registros,
        'tallas': tallas,
    })


def orden_editar(request, pk):
    orden = get_object_or_404(OrdenProduccion, pk=pk)
    if request.method == 'POST':
        form = OrdenEditarForm(request.POST, instance=orden)
        if form.is_valid():
            form.save()
            messages.success(request, 'Orden actualizada exitosamente.')
            return redirect('produccion:orden_detalle', pk=orden.pk)
    else:
        form = OrdenEditarForm(instance=orden)
    return render(request, 'produccion/orden_form.html', {
        'form': form, 'titulo': f'Editar Orden #{orden.numero}',
    })


def orden_eliminar(request, pk):
    orden = get_object_or_404(OrdenProduccion, pk=pk)
    if request.method == 'POST':
        orden.delete()
        messages.success(request, 'Orden eliminada exitosamente.')
        return redirect('produccion:orden_lista')
    return render(request, 'produccion/orden_confirmar_eliminar.html', {'orden': orden})


# ─── RegistroTrabajo ───

def registro_agregar(request, orden_pk):
    orden = get_object_or_404(
        OrdenProduccion.objects.select_related('referencia'),
        pk=orden_pk,
    )
    if request.method == 'POST':
        form = RegistroTrabajoForm(request.POST)
        if form.is_valid():
            registro = form.save(commit=False)
            registro.orden = orden
            registro.cantidad_realizada = orden.cantidad_total
            registro.save()
            messages.success(request, 'Registro de trabajo guardado.')
            return redirect('produccion:orden_detalle', pk=orden.pk)
    else:
        form = RegistroTrabajoForm()
        form.fields['proceso_referencia'].queryset = orden.referencia.procesos.select_related('proceso_base')
    return render(request, 'produccion/registro_form.html', {
        'form': form,
        'orden': orden,
        'titulo': f'Registrar Trabajo - {orden.referencia.codigo} (Orden #{orden.numero})',
    })


def registro_eliminar(request, pk):
    registro = get_object_or_404(RegistroTrabajo, pk=pk)
    orden_pk = registro.orden.pk
    if request.method == 'POST':
        registro.delete()
        messages.success(request, 'Registro de trabajo eliminado.')
        return redirect('produccion:orden_detalle', pk=orden_pk)
    return render(request, 'produccion/registro_confirmar_eliminar.html', {'registro': registro})


# ─── API ───

def api_referencia_detalle(request, pk):
    """Retorna datos de una referencia para el formulario de orden."""
    ref = get_object_or_404(
        Referencia.objects.select_related('tipo_zapato'),
        pk=pk,
    )
    consumos = [
        {
            'material': c.material.nombre,
            'tipo': c.material.tipo.nombre,
            'cantidad': str(c.cantidad_consumida),
            'unidad': c.material.unidad_medida,
        }
        for c in ref.consumos.select_related('material__tipo').all()
    ]
    procesos = [
        {
            'nombre': p.proceso_base.nombre,
            'precio': str(p.precio_mano_obra),
        }
        for p in ref.procesos.select_related('proceso_base').all()
    ]
    data = {
        'codigo': ref.codigo,
        'tipo_zapato': ref.tipo_zapato.nombre,
        'descripcion': ref.descripcion or '',
        'imagen': ref.imagen.url if ref.imagen else '',
        'consumos': consumos,
        'procesos': procesos,
    }
    return JsonResponse(data)


# ─── Nómina ───

def nomina(request):
    """Lista de empleados con registros de trabajo pendientes de pago."""
    resultados = (
        RegistroTrabajo.objects
        .filter(pagado=False)
        .values('empleado__id', 'empleado__nombre')
        .annotate(
            total_pares=Sum('cantidad_realizada'),
            total_pago=Sum(F('cantidad_realizada') * F('proceso_referencia__precio_mano_obra')),
        )
        .order_by('empleado__nombre')
    )
    return render(request, 'produccion/nomina.html', {
        'resultados': resultados,
    })


def nomina_detalle(request, empleado_pk):
    """Detalle de registros pendientes de pago de un empleado, agrupados por orden."""
    empleado = get_object_or_404(Empleado, pk=empleado_pk)
    registros = (
        RegistroTrabajo.objects
        .filter(empleado=empleado, pagado=False)
        .select_related('orden__referencia', 'proceso_referencia__proceso_base')
        .order_by('orden__numero', 'fecha')
    )

    # Agrupar por orden
    ordenes_dict = {}
    total_general = 0
    total_pares = 0
    for r in registros:
        orden = r.orden
        if orden.pk not in ordenes_dict:
            ordenes_dict[orden.pk] = {
                'orden': orden,
                'registros': [],
                'subtotal': 0,
                'pares': 0,
            }
        pago = r.cantidad_realizada * r.proceso_referencia.precio_mano_obra
        ordenes_dict[orden.pk]['registros'].append(r)
        ordenes_dict[orden.pk]['subtotal'] += pago
        ordenes_dict[orden.pk]['pares'] += r.cantidad_realizada
        total_general += pago
        total_pares += r.cantidad_realizada

    ordenes_agrupadas = list(ordenes_dict.values())

    return render(request, 'produccion/nomina_detalle.html', {
        'empleado': empleado,
        'ordenes_agrupadas': ordenes_agrupadas,
        'total_general': total_general,
        'total_pares': total_pares,
    })


def nomina_pdf(request, empleado_pk):
    """Genera un PDF con los registros pendientes de pago del empleado."""
    empleado = get_object_or_404(Empleado, pk=empleado_pk)
    registros = (
        RegistroTrabajo.objects
        .filter(empleado=empleado, pagado=False)
        .select_related('orden__referencia', 'proceso_referencia__proceso_base')
        .order_by('orden__numero', 'fecha')
    )

    # Agrupar por orden
    ordenes_dict = {}
    total_general = 0
    total_pares = 0
    for r in registros:
        orden = r.orden
        if orden.pk not in ordenes_dict:
            ordenes_dict[orden.pk] = {
                'orden': orden,
                'registros': [],
                'subtotal': 0,
                'pares': 0,
            }
        pago = r.cantidad_realizada * r.proceso_referencia.precio_mano_obra
        ordenes_dict[orden.pk]['registros'].append(r)
        ordenes_dict[orden.pk]['subtotal'] += pago
        ordenes_dict[orden.pk]['pares'] += r.cantidad_realizada
        total_general += pago
        total_pares += r.cantidad_realizada

    ordenes_agrupadas = list(ordenes_dict.values())
    fecha_generacion = timezone.localdate()

    html_string = render_to_string('produccion/nomina_pdf.html', {
        'empleado': empleado,
        'ordenes_agrupadas': ordenes_agrupadas,
        'total_general': total_general,
        'total_pares': total_pares,
        'fecha_generacion': fecha_generacion,
    })

    pdf = HTML(string=html_string).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="nomina_{empleado.nombre}_{fecha_generacion}.pdf"'
    return response


def nomina_marcar_pagado(request, empleado_pk):
    """Marca todos los registros pendientes del empleado como pagados."""
    empleado = get_object_or_404(Empleado, pk=empleado_pk)
    if request.method == 'POST':
        cantidad = (
            RegistroTrabajo.objects
            .filter(empleado=empleado, pagado=False)
            .update(pagado=True, fecha_pago=timezone.localdate())
        )
        messages.success(request, f'Se marcaron {cantidad} registros como pagados para {empleado.nombre}.')
        return redirect('produccion:nomina')
    return redirect('produccion:nomina_detalle', empleado_pk=empleado.pk)


def nomina_historial(request):
    """Historial de registros ya pagados."""
    empleado_pk = request.GET.get('empleado')
    empleados = Empleado.objects.all().order_by('nombre')
    registros = []

    if empleado_pk:
        registros = (
            RegistroTrabajo.objects
            .filter(pagado=True, empleado_id=empleado_pk)
            .select_related('orden__referencia', 'proceso_referencia__proceso_base', 'empleado')
            .order_by('-fecha_pago', '-fecha')
        )

    return render(request, 'produccion/nomina_historial.html', {
        'empleados': empleados,
        'registros': registros,
        'empleado_seleccionado': empleado_pk,
    })
