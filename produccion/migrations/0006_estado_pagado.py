from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0005_fechas_por_estado'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordenproduccion',
            name='estado',
            field=models.CharField(
                choices=[
                    ('Pendiente', 'Pendiente'),
                    ('En Proceso', 'En Proceso'),
                    ('Finalizado', 'Finalizado'),
                    ('Entregado', 'Entregado'),
                    ('Pagado', 'Pagado'),
                ],
                default='Pendiente',
                max_length=20,
                verbose_name='Estado',
            ),
        ),
        migrations.AddField(
            model_name='ordenproduccion',
            name='fecha_pagado',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha Pagado'),
        ),
    ]
