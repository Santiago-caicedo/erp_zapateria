from decimal import Decimal, InvalidOperation
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import F
from .models import TipoMaterial, Material, ProcesoBase, Referencia, ConsumoMaterial, ProcesoReferencia
from .forms import (
    TipoMaterialForm, MaterialForm, ProcesoBaseForm, ReferenciaForm,
    ConsumoMaterialForm, ProcesoReferenciaForm,
    ReferenciaConProcesosForm,
)


# ─── TipoMaterial ───

def tipo_material_lista(request):
    tipos = TipoMaterial.objects.prefetch_related('materiales').all().order_by('nombre')
    return render(request, 'inventario/tipo_material_lista.html', {'tipos': tipos})


def tipo_material_crear(request):
    if request.method == 'POST':
        form = TipoMaterialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de material creado exitosamente.')
            return redirect('inventario:tipo_material_lista')
    else:
        form = TipoMaterialForm()
    return render(request, 'inventario/tipo_material_form.html', {'form': form, 'titulo': 'Crear Tipo de Material'})


def tipo_material_editar(request, pk):
    tipo = get_object_or_404(TipoMaterial, pk=pk)
    if request.method == 'POST':
        form = TipoMaterialForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de material actualizado exitosamente.')
            return redirect('inventario:tipo_material_lista')
    else:
        form = TipoMaterialForm(instance=tipo)
    return render(request, 'inventario/tipo_material_form.html', {'form': form, 'titulo': 'Editar Tipo de Material'})


def tipo_material_eliminar(request, pk):
    tipo = get_object_or_404(TipoMaterial, pk=pk)
    if request.method == 'POST':
        tipo.delete()
        messages.success(request, 'Tipo de material eliminado exitosamente.')
        return redirect('inventario:tipo_material_lista')
    return render(request, 'inventario/tipo_material_confirmar_eliminar.html', {'tipo': tipo})


# ─── Material ───

def material_lista(request):
    tipos = TipoMaterial.objects.prefetch_related('materiales').all().order_by('nombre')

    total_materiales = Material.objects.count()
    total_tipos = tipos.count()
    sin_stock = Material.objects.filter(cantidad_stock__lte=0).count()
    stock_bajo = Material.objects.filter(cantidad_stock__gt=0, cantidad_stock__lte=10).count()

    return render(request, 'inventario/material_lista.html', {
        'tipos': tipos,
        'total_materiales': total_materiales,
        'total_tipos': total_tipos,
        'sin_stock': sin_stock,
        'stock_bajo': stock_bajo,
    })


def material_agregar_stock(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        cantidad = request.POST.get('cantidad', '')
        try:
            cantidad = Decimal(cantidad)
            if cantidad <= 0:
                raise ValueError
            Material.objects.filter(pk=pk).update(
                cantidad_stock=F('cantidad_stock') + cantidad
            )
            material.refresh_from_db()
            messages.success(request, f'Se agregaron {cantidad} {material.unidad_medida} a {material.nombre}. Stock actual: {material.cantidad_stock}')
        except (ValueError, TypeError, InvalidOperation):
            messages.error(request, 'Ingresa una cantidad válida mayor a 0.')
        return redirect('inventario:material_lista')
    return render(request, 'inventario/material_agregar_stock.html', {'material': material})


def material_crear(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Material creado exitosamente.')
            return redirect('inventario:material_lista')
    else:
        form = MaterialForm()
    return render(request, 'inventario/material_form.html', {'form': form, 'titulo': 'Crear Material'})


def material_editar(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, 'Material actualizado exitosamente.')
            return redirect('inventario:material_lista')
    else:
        form = MaterialForm(instance=material)
    return render(request, 'inventario/material_form.html', {'form': form, 'titulo': 'Editar Material'})


def material_eliminar(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        material.delete()
        messages.success(request, 'Material eliminado exitosamente.')
        return redirect('inventario:material_lista')
    return render(request, 'inventario/material_confirmar_eliminar.html', {'material': material})


# ─── ProcesoBase ───

def proceso_lista(request):
    procesos = ProcesoBase.objects.all().order_by('nombre')
    return render(request, 'inventario/proceso_lista.html', {'procesos': procesos})


def proceso_crear(request):
    if request.method == 'POST':
        form = ProcesoBaseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proceso creado exitosamente.')
            return redirect('inventario:proceso_lista')
    else:
        form = ProcesoBaseForm()
    return render(request, 'inventario/proceso_form.html', {'form': form, 'titulo': 'Crear Proceso'})


def proceso_editar(request, pk):
    proceso = get_object_or_404(ProcesoBase, pk=pk)
    if request.method == 'POST':
        form = ProcesoBaseForm(request.POST, instance=proceso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proceso actualizado exitosamente.')
            return redirect('inventario:proceso_lista')
    else:
        form = ProcesoBaseForm(instance=proceso)
    return render(request, 'inventario/proceso_form.html', {'form': form, 'titulo': 'Editar Proceso'})


def proceso_eliminar(request, pk):
    proceso = get_object_or_404(ProcesoBase, pk=pk)
    if request.method == 'POST':
        proceso.delete()
        messages.success(request, 'Proceso eliminado exitosamente.')
        return redirect('inventario:proceso_lista')
    return render(request, 'inventario/proceso_confirmar_eliminar.html', {'proceso': proceso})


# ─── Referencia ───

def referencia_lista(request):
    referencias = Referencia.objects.all().order_by('codigo')
    return render(request, 'inventario/referencia_lista.html', {'referencias': referencias})


def referencia_crear(request):
    if request.method == 'POST':
        form = ReferenciaConProcesosForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Referencia creada exitosamente.')
            return redirect('inventario:referencia_lista')
    else:
        form = ReferenciaConProcesosForm()
    procesos = ProcesoBase.objects.all().order_by('nombre')
    return render(request, 'inventario/referencia_form.html', {
        'form': form, 'titulo': 'Crear Referencia', 'procesos': procesos,
    })


def referencia_detalle(request, pk):
    referencia = get_object_or_404(Referencia, pk=pk)
    consumos = referencia.consumos.select_related('material').all()
    procesos = referencia.procesos.select_related('proceso_base').all()
    return render(request, 'inventario/referencia_detalle.html', {
        'referencia': referencia,
        'consumos': consumos,
        'procesos': procesos,
    })


def referencia_editar(request, pk):
    referencia = get_object_or_404(Referencia, pk=pk)
    if request.method == 'POST':
        form = ReferenciaConProcesosForm(request.POST, instance=referencia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Referencia actualizada exitosamente.')
            return redirect('inventario:referencia_detalle', pk=referencia.pk)
    else:
        form = ReferenciaConProcesosForm(instance=referencia)
    procesos = ProcesoBase.objects.all().order_by('nombre')
    return render(request, 'inventario/referencia_form.html', {
        'form': form, 'titulo': 'Editar Referencia', 'procesos': procesos,
    })


def referencia_eliminar(request, pk):
    referencia = get_object_or_404(Referencia, pk=pk)
    if request.method == 'POST':
        referencia.delete()
        messages.success(request, 'Referencia eliminada exitosamente.')
        return redirect('inventario:referencia_lista')
    return render(request, 'inventario/referencia_confirmar_eliminar.html', {'referencia': referencia})


# ─── ConsumoMaterial (dentro de una referencia) ───

def consumo_agregar(request, referencia_pk):
    referencia = get_object_or_404(Referencia, pk=referencia_pk)
    if request.method == 'POST':
        form = ConsumoMaterialForm(request.POST)
        if form.is_valid():
            consumo = form.save(commit=False)
            consumo.referencia = referencia
            consumo.save()
            messages.success(request, 'Material asignado a la referencia.')
            return redirect('inventario:referencia_detalle', pk=referencia.pk)
    else:
        form = ConsumoMaterialForm()
    return render(request, 'inventario/consumo_form.html', {
        'form': form,
        'referencia': referencia,
        'titulo': f'Agregar Material a {referencia.codigo}',
    })


def consumo_eliminar(request, pk):
    consumo = get_object_or_404(ConsumoMaterial, pk=pk)
    referencia_pk = consumo.referencia.pk
    if request.method == 'POST':
        consumo.delete()
        messages.success(request, 'Material removido de la referencia.')
        return redirect('inventario:referencia_detalle', pk=referencia_pk)
    return render(request, 'inventario/consumo_confirmar_eliminar.html', {'consumo': consumo})


# ─── ProcesoReferencia (dentro de una referencia) ───

def proceso_ref_agregar(request, referencia_pk):
    referencia = get_object_or_404(Referencia, pk=referencia_pk)
    if request.method == 'POST':
        form = ProcesoReferenciaForm(request.POST)
        if form.is_valid():
            proceso_ref = form.save(commit=False)
            proceso_ref.referencia = referencia
            proceso_ref.save()
            messages.success(request, 'Proceso asignado a la referencia.')
            return redirect('inventario:referencia_detalle', pk=referencia.pk)
    else:
        form = ProcesoReferenciaForm()
    return render(request, 'inventario/proceso_ref_form.html', {
        'form': form,
        'referencia': referencia,
        'titulo': f'Agregar Proceso a {referencia.codigo}',
    })


def proceso_ref_eliminar(request, pk):
    proceso_ref = get_object_or_404(ProcesoReferencia, pk=pk)
    referencia_pk = proceso_ref.referencia.pk
    if request.method == 'POST':
        proceso_ref.delete()
        messages.success(request, 'Proceso removido de la referencia.')
        return redirect('inventario:referencia_detalle', pk=referencia_pk)
    return render(request, 'inventario/proceso_ref_confirmar_eliminar.html', {'proceso_ref': proceso_ref})
