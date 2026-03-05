import django.db.models.deletion
from django.db import migrations, models


def crear_tipo_zapato_default(apps, schema_editor):
    """Crea un tipo de zapato por defecto para referencias existentes."""
    TipoZapato = apps.get_model('inventario', 'TipoZapato')
    Referencia = apps.get_model('inventario', 'Referencia')
    if Referencia.objects.exists():
        tipo, _ = TipoZapato.objects.get_or_create(nombre='General')
        Referencia.objects.filter(tipo_zapato__isnull=True).update(tipo_zapato=tipo)


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0002_tipomaterial_alter_material_nombre_material_tipo_and_more'),
    ]

    operations = [
        # 1. Crear TipoZapato
        migrations.CreateModel(
            name='TipoZapato',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True, verbose_name='Tipo de Zapato')),
            ],
            options={
                'verbose_name': 'Tipo de Zapato',
                'verbose_name_plural': 'Tipos de Zapato',
            },
        ),
        # 2. Eliminar campos viejos de Referencia
        migrations.RemoveField(
            model_name='referencia',
            name='talla',
        ),
        migrations.RemoveField(
            model_name='referencia',
            name='color',
        ),
        migrations.RemoveField(
            model_name='referencia',
            name='precio_venta',
        ),
        # 3. Agregar imagen
        migrations.AddField(
            model_name='referencia',
            name='imagen',
            field=models.ImageField(blank=True, null=True, upload_to='referencias/', verbose_name='Imagen'),
        ),
        # 4. Agregar tipo_zapato FK nullable temporalmente
        migrations.AddField(
            model_name='referencia',
            name='tipo_zapato',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='referencias',
                to='inventario.tipozapato',
                verbose_name='Tipo de Zapato',
            ),
        ),
        # 5. Asignar tipo default a referencias existentes
        migrations.RunPython(crear_tipo_zapato_default, migrations.RunPython.noop),
        # 6. Hacer la FK NOT NULL
        migrations.AlterField(
            model_name='referencia',
            name='tipo_zapato',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='referencias',
                to='inventario.tipozapato',
                verbose_name='Tipo de Zapato',
            ),
        ),
        # 7. unique_together en ConsumoMaterial
        migrations.AlterUniqueTogether(
            name='consumomaterial',
            unique_together={('referencia', 'material')},
        ),
    ]
