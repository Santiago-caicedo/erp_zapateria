from django.db import migrations, models


def eliminar_duplicados(apps, schema_editor):
    """Elimina registros duplicados de orden+proceso, conservando el más reciente."""
    RegistroTrabajo = apps.get_model('produccion', 'RegistroTrabajo')
    duplicados = (
        RegistroTrabajo.objects
        .values('orden_id', 'proceso_referencia_id')
        .annotate(total=models.Count('id'), max_id=models.Max('id'))
        .filter(total__gt=1)
    )
    for dup in duplicados:
        RegistroTrabajo.objects.filter(
            orden_id=dup['orden_id'],
            proceso_referencia_id=dup['proceso_referencia_id'],
        ).exclude(id=dup['max_id']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0003_registrotrabajo_pagado'),
    ]

    operations = [
        migrations.RunPython(eliminar_duplicados, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='registrotrabajo',
            constraint=models.UniqueConstraint(
                fields=['orden', 'proceso_referencia'],
                name='unique_orden_proceso',
            ),
        ),
    ]
