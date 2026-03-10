from django.db import migrations, models


def migrar_fechas(apps, schema_editor):
    """Copia fecha_entrega a fecha_pendiente para órdenes existentes que no tengan fechas de estado."""
    OrdenProduccion = apps.get_model('produccion', 'OrdenProduccion')
    for orden in OrdenProduccion.objects.all():
        # Asignar fecha_creacion como fecha_pendiente si no tiene
        if not orden.fecha_pendiente:
            orden.fecha_pendiente = orden.fecha_creacion
        # Si la orden ya pasó de Pendiente, asignar fechas intermedias
        estados_avanzados = {
            'En Proceso': ['fecha_en_proceso'],
            'Finalizado': ['fecha_en_proceso', 'fecha_finalizado'],
            'Entregado': ['fecha_en_proceso', 'fecha_finalizado', 'fecha_entregado'],
        }
        campos = estados_avanzados.get(orden.estado, [])
        for campo in campos:
            if not getattr(orden, campo):
                setattr(orden, campo, orden.fecha_creacion)
        orden.save()


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0004_unique_orden_proceso'),
    ]

    operations = [
        # 1. Agregar los 4 campos de fecha
        migrations.AddField(
            model_name='ordenproduccion',
            name='fecha_pendiente',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha Pendiente'),
        ),
        migrations.AddField(
            model_name='ordenproduccion',
            name='fecha_en_proceso',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha En Proceso'),
        ),
        migrations.AddField(
            model_name='ordenproduccion',
            name='fecha_finalizado',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha Finalizado'),
        ),
        migrations.AddField(
            model_name='ordenproduccion',
            name='fecha_entregado',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha Entregado'),
        ),
        # 2. Migrar datos existentes
        migrations.RunPython(migrar_fechas, migrations.RunPython.noop),
        # 3. Eliminar fecha_entrega
        migrations.RemoveField(
            model_name='ordenproduccion',
            name='fecha_entrega',
        ),
    ]
