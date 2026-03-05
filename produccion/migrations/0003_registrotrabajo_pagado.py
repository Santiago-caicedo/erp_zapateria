from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0002_orden_redesign'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrotrabajo',
            name='pagado',
            field=models.BooleanField(default=False, verbose_name='Pagado'),
        ),
        migrations.AddField(
            model_name='registrotrabajo',
            name='fecha_pago',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha de Pago'),
        ),
    ]
