import django.db.models.deletion
from django.db import migrations, models


def asignar_numeros(apps, schema_editor):
    """Asigna números a órdenes existentes."""
    OrdenProduccion = apps.get_model('produccion', 'OrdenProduccion')
    for i, orden in enumerate(OrdenProduccion.objects.order_by('id'), start=1):
        orden.numero = i
        orden.save(update_fields=['numero'])


def migrar_registros(apps, schema_editor):
    """Migra registros de trabajo de detalle_orden a orden."""
    RegistroTrabajo = apps.get_model('produccion', 'RegistroTrabajo')
    for rt in RegistroTrabajo.objects.select_related('detalle_orden').all():
        if rt.detalle_orden:
            rt.orden = rt.detalle_orden.orden
            rt.save(update_fields=['orden'])


def migrar_referencia_de_detalle(apps, schema_editor):
    """Si hay órdenes con detalles, asigna la primera referencia del detalle a la orden."""
    OrdenProduccion = apps.get_model('produccion', 'OrdenProduccion')
    DetalleOrden = apps.get_model('produccion', 'DetalleOrden')
    Referencia = apps.get_model('inventario', 'Referencia')

    for orden in OrdenProduccion.objects.filter(referencia__isnull=True):
        detalle = DetalleOrden.objects.filter(orden=orden).first()
        if detalle:
            orden.referencia = detalle.referencia
            orden.save(update_fields=['referencia'])
        else:
            # Asignar la primera referencia que exista como fallback
            ref = Referencia.objects.first()
            if ref:
                orden.referencia = ref
                orden.save(update_fields=['referencia'])


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0001_initial'),
        ('inventario', '0003_tipozapato_referencia_changes'),
    ]

    operations = [
        # 1. Agregar numero nullable temporalmente
        migrations.AddField(
            model_name='ordenproduccion',
            name='numero',
            field=models.PositiveIntegerField(null=True, verbose_name='Número de Orden'),
        ),

        # 2. Asignar números a existentes
        migrations.RunPython(asignar_numeros, migrations.RunPython.noop),

        # 3. Hacer numero unique y not null
        migrations.AlterField(
            model_name='ordenproduccion',
            name='numero',
            field=models.PositiveIntegerField(editable=False, unique=True, verbose_name='Número de Orden'),
        ),

        # 4. Agregar referencia FK nullable a OrdenProduccion
        migrations.AddField(
            model_name='ordenproduccion',
            name='referencia',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='ordenes',
                to='inventario.referencia',
                verbose_name='Referencia',
            ),
        ),

        # 5. Agregar campos de talla
        migrations.AddField(model_name='ordenproduccion', name='talla_34',
                            field=models.PositiveIntegerField(default=0, verbose_name='Talla 34')),
        migrations.AddField(model_name='ordenproduccion', name='talla_35',
                            field=models.PositiveIntegerField(default=0, verbose_name='Talla 35')),
        migrations.AddField(model_name='ordenproduccion', name='talla_36',
                            field=models.PositiveIntegerField(default=0, verbose_name='Talla 36')),
        migrations.AddField(model_name='ordenproduccion', name='talla_37',
                            field=models.PositiveIntegerField(default=0, verbose_name='Talla 37')),
        migrations.AddField(model_name='ordenproduccion', name='talla_38',
                            field=models.PositiveIntegerField(default=0, verbose_name='Talla 38')),
        migrations.AddField(model_name='ordenproduccion', name='talla_39',
                            field=models.PositiveIntegerField(default=0, verbose_name='Talla 39')),
        migrations.AddField(model_name='ordenproduccion', name='talla_40',
                            field=models.PositiveIntegerField(default=0, verbose_name='Talla 40')),

        # 6. Migrar referencia desde DetalleOrden
        migrations.RunPython(migrar_referencia_de_detalle, migrations.RunPython.noop),

        # 7. Hacer referencia NOT NULL
        migrations.AlterField(
            model_name='ordenproduccion',
            name='referencia',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='ordenes',
                to='inventario.referencia',
                verbose_name='Referencia',
            ),
        ),

        # 8. Agregar FK orden a RegistroTrabajo (nullable primero)
        migrations.AddField(
            model_name='registrotrabajo',
            name='orden',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='registros_trabajo',
                to='produccion.ordenproduccion',
            ),
        ),

        # 9. Migrar registros de detalle_orden a orden
        migrations.RunPython(migrar_registros, migrations.RunPython.noop),

        # 10. Hacer orden NOT NULL en RegistroTrabajo
        migrations.AlterField(
            model_name='registrotrabajo',
            name='orden',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='registros_trabajo',
                to='produccion.ordenproduccion',
            ),
        ),

        # 11. Eliminar FK detalle_orden de RegistroTrabajo
        migrations.RemoveField(
            model_name='registrotrabajo',
            name='detalle_orden',
        ),

        # 12. Eliminar modelo DetalleOrden
        migrations.DeleteModel(
            name='DetalleOrden',
        ),
    ]
