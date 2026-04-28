from django.db import migrations, models


def marcar_ordenes_existentes(apps, schema_editor):
    """
    Las órdenes que ya tienen registros de trabajo al momento de aplicar
    esta migración se marcan como descontadas para no restar el stock una
    segunda vez cuando se les agregue un nuevo proceso.
    """
    OrdenProduccion = apps.get_model('produccion', 'OrdenProduccion')
    RegistroTrabajo = apps.get_model('produccion', 'RegistroTrabajo')
    ordenes_con_registros = RegistroTrabajo.objects.values_list(
        'orden_id', flat=True
    ).distinct()
    OrdenProduccion.objects.filter(
        pk__in=list(ordenes_con_registros)
    ).update(materiales_descontados=True)


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0007_ordenproduccion_talla_41'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordenproduccion',
            name='materiales_descontados',
            field=models.BooleanField(default=False, verbose_name='Materiales Descontados'),
        ),
        migrations.RunPython(marcar_ordenes_existentes, migrations.RunPython.noop),
    ]
