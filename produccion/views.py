import json
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Sum, F, Q
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML
from .models import Cliente, OrdenProduccion, RegistroTrabajo
from .forms import ClienteForm, OrdenProduccionForm, OrdenEditarForm, RegistroTrabajoForm
from empleados.models import Empleado
from inventario.models import Referencia


def _fmt_peso(valor):
    """Formatea valor como peso colombiano con separador de miles."""
    try:
        entero = int(Decimal(str(valor)).quantize(Decimal('1')))
    except Exception:
        return f'${valor}'
    return f'${entero:,}'.replace(',', '.')

def _verificar_orden_finalizada(orden):
    """Si todos los procesos de la referencia ya tienen registro, marca la orden como Finalizada."""
    total_procesos = orden.referencia.procesos.count()
    registrados = orden.registros_trabajo.values('proceso_referencia').distinct().count()
    if total_procesos > 0 and registrados >= total_procesos and orden.estado not in ('Finalizado', 'Entregado', 'Pagado'):
        orden.estado = 'Finalizado'
        orden.save(update_fields=['estado', 'fecha_finalizado'])


def _verificar_orden_pagada(orden):
    """Si todos los registros de trabajo de la orden están pagados, marca la orden como Pagada."""
    total_registros = orden.registros_trabajo.count()
    pagados = orden.registros_trabajo.filter(pagado=True).count()
    if total_registros > 0 and pagados >= total_registros and orden.estado != 'Pagado':
        orden.estado = 'Pagado'
        orden.save(update_fields=['estado', 'fecha_pagado'])


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
        .order_by('-numero')
    )

    # Filtro: búsqueda por número o referencia
    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        ordenes = ordenes.filter(
            Q(referencia__codigo__icontains=busqueda) |
            Q(numero__icontains=busqueda)
        )

    # Filtro: cliente
    cliente_id = request.GET.get('cliente', '')
    if cliente_id:
        ordenes = ordenes.filter(cliente_id=cliente_id)

    # Filtro: estado
    estado = request.GET.get('estado', '')
    if estado:
        ordenes = ordenes.filter(estado=estado)

    # Filtro: fecha por estado
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    if fecha_desde or fecha_hasta:
        # Filtrar por la fecha del estado seleccionado, o fecha_creacion si no hay estado
        fecha_field_map = {
            'Pendiente': 'fecha_pendiente',
            'En Proceso': 'fecha_en_proceso',
            'Finalizado': 'fecha_finalizado',
            'Entregado': 'fecha_entregado',
            'Pagado': 'fecha_pagado',
        }
        campo_fecha = fecha_field_map.get(estado, 'fecha_creacion')
        if fecha_desde:
            ordenes = ordenes.filter(**{f'{campo_fecha}__gte': fecha_desde})
        if fecha_hasta:
            ordenes = ordenes.filter(**{f'{campo_fecha}__lte': fecha_hasta})

    # Paginación
    paginator = Paginator(ordenes, 15)
    pagina = request.GET.get('pagina', 1)
    ordenes_page = paginator.get_page(pagina)

    # Datos para los selects de filtro
    clientes = Cliente.objects.order_by('nombre')

    # Construir query string sin 'pagina' para los links de paginación
    params = request.GET.copy()
    params.pop('pagina', None)
    params_sin_pagina = params.urlencode()

    return render(request, 'produccion/orden_lista.html', {
        'ordenes': ordenes_page,
        'clientes': clientes,
        'estados': OrdenProduccion.ESTADOS,
        'params_sin_pagina': params_sin_pagina,
        'filtros': {
            'q': busqueda,
            'cliente': cliente_id,
            'estado': estado,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        },
    })


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
    for t in range(34, 42):
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


def orden_pdf(request, pk):
    """Genera PDF de la orden de producción con tickets recortables por proceso."""
    import base64
    orden = get_object_or_404(
        OrdenProduccion.objects.select_related('cliente', 'referencia__tipo_zapato'),
        pk=pk,
    )
    consumos = orden.referencia.consumos.select_related('material__tipo').all()
    procesos = orden.referencia.procesos.select_related('proceso_base').all()

    materiales = []
    for c in consumos:
        materiales.append({
            'tipo': c.material.tipo.nombre,
            'nombre': c.material.nombre,
            'cantidad': c.cantidad_consumida * orden.cantidad_total,
            'unidad': c.material.unidad_medida,
        })

    tallas = []
    for t in range(34, 42):
        val = getattr(orden, f'talla_{t}')
        tallas.append({'numero': t, 'cantidad': val})

    # Agrupar procesos en filas de 2 para el grid
    procesos_lista = list(procesos)
    procesos_pares = []
    for i in range(0, len(procesos_lista), 2):
        fila = [procesos_lista[i]]
        if i + 1 < len(procesos_lista):
            fila.append(procesos_lista[i + 1])
        procesos_pares.append(fila)

    # Convertir imagen a data URI para WeasyPrint.
    # Usamos imagen.open() (no .path) para que funcione tanto con
    # FileSystemStorage local como con S3 en producción.
    imagen_uri = ''
    if orden.referencia.imagen:
        try:
            with orden.referencia.imagen.open('rb') as f:
                img_data = base64.b64encode(f.read()).decode()
            nombre = orden.referencia.imagen.name
            ext = nombre.rsplit('.', 1)[-1].lower() if '.' in nombre else 'jpg'
            mime = {
                'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                'png': 'image/png', 'webp': 'image/webp', 'gif': 'image/gif',
            }.get(ext, 'image/jpeg')
            imagen_uri = f'data:{mime};base64,{img_data}'
        except Exception:
            imagen_uri = ''

    # Cambiar estado a "En Proceso" si está en Pendiente
    if orden.estado == 'Pendiente':
        orden.estado = 'En Proceso'
        orden.save(update_fields=['estado', 'fecha_en_proceso'])

    fecha_generacion = timezone.localdate()

    html_string = render_to_string('produccion/orden_pdf.html', {
        'orden': orden,
        'materiales': materiales,
        'procesos_pares': procesos_pares,
        'tallas': tallas,
        'cantidad_total': orden.cantidad_total,
        'imagen_uri': imagen_uri,
        'fecha_generacion': fecha_generacion,
    })

    pdf = HTML(string=html_string).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="orden_{orden.numero}_{fecha_generacion}.pdf"'
    return response


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
            _verificar_orden_finalizada(orden)
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


def registro_trabajo(request):
    """Registro de trabajo en lote centrado en el empleado."""
    empleados = Empleado.objects.order_by('nombre')

    if request.method == 'POST':
        try:
            datos = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'ok': False, 'error': 'Datos inválidos.'}, status=400)

        empleado_id = datos.get('empleado')
        lineas = datos.get('lineas', [])

        if not empleado_id or not lineas:
            return JsonResponse({'ok': False, 'error': 'Debe seleccionar empleado y al menos una línea.'}, status=400)

        empleado = get_object_or_404(Empleado, pk=empleado_id)
        registros_creados = 0
        errores = []

        for linea in lineas:
            orden = get_object_or_404(OrdenProduccion, pk=linea['orden_id'])
            proceso_ref = get_object_or_404(
                orden.referencia.procesos.select_related('proceso_base'),
                pk=linea['proceso_id'],
            )
            cantidad = orden.cantidad_total
            if cantidad <= 0:
                continue

            # Verificar que no exista ya este proceso en esta orden
            if RegistroTrabajo.objects.filter(orden=orden, proceso_referencia=proceso_ref).exists():
                errores.append(f'Orden #{orden.numero} ya tiene registrado el proceso "{proceso_ref.proceso_base.nombre}".')
                continue

            try:
                RegistroTrabajo.objects.create(
                    empleado=empleado,
                    orden=orden,
                    proceso_referencia=proceso_ref,
                    cantidad_realizada=cantidad,
                )
                registros_creados += 1
            except IntegrityError:
                errores.append(f'Orden #{orden.numero} - {proceso_ref.proceso_base.nombre}: ya registrado.')

        # Verificar si alguna orden quedó con todos sus procesos registrados
        ordenes_afectadas = set(linea['orden_id'] for linea in lineas)
        for oid in ordenes_afectadas:
            try:
                o = OrdenProduccion.objects.select_related('referencia').get(pk=oid)
                _verificar_orden_finalizada(o)
            except OrdenProduccion.DoesNotExist:
                pass

        if errores and registros_creados == 0:
            return JsonResponse({'ok': False, 'error': ' | '.join(errores)}, status=400)

        mensaje = f'Se registraron {registros_creados} trabajos para {empleado.nombre}.'
        if errores:
            mensaje += f' ({len(errores)} omitidos por duplicado)'

        return JsonResponse({'ok': True, 'mensaje': mensaje})

    return render(request, 'produccion/registro_trabajo.html', {
        'empleados': empleados,
    })


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


def api_ordenes_activas(request):
    """Retorna órdenes con estado Pendiente o En Proceso."""
    ordenes = (
        OrdenProduccion.objects
        .filter(estado__in=['Pendiente', 'En Proceso'])
        .select_related('cliente', 'referencia__tipo_zapato')
        .order_by('-numero')
    )
    data = [
        {
            'id': o.pk,
            'numero': o.numero,
            'referencia': o.referencia.codigo,
            'tipo_zapato': o.referencia.tipo_zapato.nombre,
            'cliente': o.cliente.nombre,
            'cantidad_total': o.cantidad_total,
        }
        for o in ordenes
    ]
    return JsonResponse(data, safe=False)


def api_procesos_orden(request, orden_pk):
    """Retorna los procesos disponibles para la referencia de una orden, indicando si ya están registrados."""
    orden = get_object_or_404(
        OrdenProduccion.objects.select_related('referencia'),
        pk=orden_pk,
    )
    procesos = orden.referencia.procesos.select_related('proceso_base').all()
    registrados = set(
        RegistroTrabajo.objects
        .filter(orden=orden)
        .values_list('proceso_referencia_id', flat=True)
    )
    data = [
        {
            'id': p.pk,
            'nombre': p.proceso_base.nombre,
            'precio': str(p.precio_mano_obra),
            'registrado': p.pk in registrados,
        }
        for p in procesos
    ]
    return JsonResponse(data, safe=False)


# ─── Nómina ───

def nomina(request):
    """Lista de empleados con registros de trabajo pendientes de pago."""
    resultados = list(
        RegistroTrabajo.objects
        .filter(pagado=False)
        .values('empleado__id', 'empleado__nombre')
        .annotate(
            total_pares=Sum('cantidad_realizada'),
            total_pago=Sum(F('cantidad_realizada') * F('proceso_referencia__precio_mano_obra')),
        )
        .order_by('empleado__nombre')
    )
    gran_total_pago = sum(r['total_pago'] or 0 for r in resultados)
    gran_total_pares = sum(r['total_pares'] or 0 for r in resultados)

    return render(request, 'produccion/nomina.html', {
        'resultados': resultados,
        'total_empleados': len(resultados),
        'gran_total_pago': gran_total_pago,
        'gran_total_pares': gran_total_pares,
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

    # Formatear valores para el PDF (no tiene acceso a template tags)
    for grupo in ordenes_agrupadas:
        grupo['subtotal_fmt'] = _fmt_peso(grupo['subtotal'])[1:]  # sin $
        for r in grupo['registros']:
            r.precio_mano_obra_fmt = _fmt_peso(r.proceso_referencia.precio_mano_obra)[1:]
            r.total_pago_fmt = _fmt_peso(r.total_pago)[1:]

    html_string = render_to_string('produccion/nomina_pdf.html', {
        'empleado': empleado,
        'ordenes_agrupadas': ordenes_agrupadas,
        'total_general': total_general,
        'total_general_fmt': _fmt_peso(total_general)[1:],
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
        registros_pendientes = RegistroTrabajo.objects.filter(empleado=empleado, pagado=False)
        # Guardar las órdenes afectadas antes de actualizar
        ordenes_ids = set(registros_pendientes.values_list('orden_id', flat=True))
        cantidad = registros_pendientes.update(pagado=True, fecha_pago=timezone.localdate())
        # Verificar si alguna orden quedó completamente pagada
        for oid in ordenes_ids:
            try:
                orden = OrdenProduccion.objects.select_related('referencia').get(pk=oid)
                _verificar_orden_pagada(orden)
            except OrdenProduccion.DoesNotExist:
                pass
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
