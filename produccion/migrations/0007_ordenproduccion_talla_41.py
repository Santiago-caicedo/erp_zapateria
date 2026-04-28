from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0006_estado_pagado'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordenproduccion',
            name='talla_41',
            field=models.PositiveIntegerField(default=0, verbose_name='Talla 41'),
        ),
    ]
