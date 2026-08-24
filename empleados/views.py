from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from config.eliminacion import contexto_bloqueo, procesar_borrado
from .models import Empleado
from .forms import EmpleadoForm


def empleado_lista(request):
    empleados = Empleado.objects.all().order_by('nombre')
    return render(request, 'empleados/empleado_lista.html', {'empleados': empleados})


def empleado_crear(request):
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empleado creado exitosamente.')
            return redirect('empleados:lista')
    else:
        form = EmpleadoForm()
    return render(request, 'empleados/empleado_form.html', {'form': form, 'titulo': 'Crear Empleado'})


def empleado_editar(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empleado actualizado exitosamente.')
            return redirect('empleados:lista')
    else:
        form = EmpleadoForm(instance=empleado)
    return render(request, 'empleados/empleado_form.html', {'form': form, 'titulo': 'Editar Empleado'})


def empleado_eliminar(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    # RegistroTrabajo.empleado es PROTECT: sus registros bloquean el borrado.
    bloqueos = (
        empleado.trabajos
        .select_related('orden', 'proceso_referencia__proceso_base')
        .order_by('-fecha')
    )

    if request.method == 'POST':
        return procesar_borrado(
            request, empleado, empleado.nombre,
            'empleados:lista',
            'Empleado eliminado exitosamente.',
            f'No se puede eliminar a {empleado.nombre} porque tiene registros de '
            'trabajo asociados.',
        )

    return render(request, 'empleados/empleado_confirmar_eliminar.html', {
        'empleado': empleado,
        'nombre_objeto': empleado.nombre,
        **contexto_bloqueo(request, empleado, bloqueos),
    })


def empleado_detalle(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    return render(request, 'empleados/empleado_detalle.html', {'empleado': empleado})
