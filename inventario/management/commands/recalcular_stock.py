"""
Recalcula el stock real de materiales descontando lo consumido por todas
las órdenes que ya tienen registros de trabajo.

Uso:
    python manage.py recalcular_stock              # solo muestra reporte
    python manage.py recalcular_stock --aplicar    # aplica el descuento

ADVERTENCIA: este script está pensado como una corrección histórica
única. Si lo ejecutás dos veces seguidas con --aplicar, vas a descontar
el stock dos veces. Hacelo justo después de migrar y antes de registrar
nuevos trabajos.
"""

from collections import defaultdict
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F

from inventario.models import Material
from produccion.models import OrdenProduccion


class Command(BaseCommand):
    help = (
        'Calcula el material consumido por todas las órdenes con registros '
        'de trabajo y lo resta del stock. Sin --aplicar solo muestra el '
        'reporte.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--aplicar',
            action='store_true',
            help='Aplica el descuento en la base de datos.',
        )

    def handle(self, *args, **options):
        aplicar = options['aplicar']

        # Órdenes que tienen al menos un RegistroTrabajo
        ordenes = (
            OrdenProduccion.objects
            .filter(registros_trabajo__isnull=False)
            .distinct()
            .prefetch_related('referencia__consumos__material')
        )

        consumido_por_material = defaultdict(Decimal)
        ordenes_procesadas = 0
        for orden in ordenes:
            cantidad_total = orden.cantidad_total
            if cantidad_total <= 0:
                continue
            ordenes_procesadas += 1
            for c in orden.referencia.consumos.all():
                consumido_por_material[c.material_id] += (
                    c.cantidad_consumida * cantidad_total
                )

        if not consumido_por_material:
            self.stdout.write(self.style.WARNING(
                'No hay órdenes con registros de trabajo. Nada que descontar.'
            ))
            return

        # Reporte
        materiales = {
            m.pk: m
            for m in Material.objects.filter(pk__in=consumido_por_material)
        }

        self.stdout.write(self.style.NOTICE(
            f'\nÓrdenes con trabajo registrado: {ordenes_procesadas}\n'
            f'Materiales afectados: {len(consumido_por_material)}\n'
        ))

        header = f'{"Material":<35} {"Stock actual":>14} {"A descontar":>14} {"Stock nuevo":>14}'
        self.stdout.write(header)
        self.stdout.write('-' * len(header))

        hay_negativos = False
        # Ordenar por nombre del material
        items = sorted(
            consumido_por_material.items(),
            key=lambda x: materiales[x[0]].nombre,
        )
        for mat_id, total in items:
            mat = materiales[mat_id]
            stock_nuevo = mat.cantidad_stock - total
            line = (
                f'{mat.nombre[:35]:<35} '
                f'{str(mat.cantidad_stock):>14} '
                f'{str(total):>14} '
                f'{str(stock_nuevo):>14}'
            )
            if stock_nuevo < 0:
                hay_negativos = True
                self.stdout.write(self.style.ERROR(line + '  (NEGATIVO)'))
            else:
                self.stdout.write(line)

        if hay_negativos:
            self.stdout.write(self.style.WARNING(
                '\nAviso: algunos materiales quedarán en stock negativo. '
                'Eso indica que en la realidad se consumió más de lo que '
                'había cargado. Revisá esos casos antes de aplicar.'
            ))

        if not aplicar:
            self.stdout.write(self.style.WARNING(
                '\n[DRY-RUN] No se modificó nada. '
                'Ejecutá con --aplicar para descontar.'
            ))
            return

        # Aplicar
        with transaction.atomic():
            for mat_id, total in consumido_por_material.items():
                Material.objects.filter(pk=mat_id).update(
                    cantidad_stock=F('cantidad_stock') - total
                )

        self.stdout.write(self.style.SUCCESS(
            f'\nStock actualizado para {len(consumido_por_material)} materiales.'
        ))
