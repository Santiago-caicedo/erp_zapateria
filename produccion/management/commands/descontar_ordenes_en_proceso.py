"""
Descuenta el material de las órdenes que ya salieron de Pendiente pero que
nunca tuvieron el descuento aplicado.

Hace falta una sola vez, al desplegar el cambio que ata el descuento de
inventario al estado de la orden (antes se disparaba con el primer
RegistroTrabajo). Las órdenes que quedaron En Proceso sin trabajo registrado
nunca descontaron material y este comando las pone al día.

Uso:
    python manage.py descontar_ordenes_en_proceso              # solo reporte
    python manage.py descontar_ordenes_en_proceso --aplicar    # aplica

Es seguro ejecutarlo más de una vez: solo toca órdenes con
materiales_descontados=False y marca el flag al descontar.
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
        'Descuenta el material de las órdenes que ya no están Pendientes y '
        'todavía no tienen materiales_descontados. Sin --aplicar solo muestra '
        'el reporte.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--aplicar',
            action='store_true',
            help='Aplica el descuento en la base de datos.',
        )

    def handle(self, *args, **options):
        aplicar = options['aplicar']

        ordenes = (
            OrdenProduccion.objects
            .exclude(estado='Pendiente')
            .filter(materiales_descontados=False)
            .select_related('referencia')
            .prefetch_related('referencia__consumos__material')
            .order_by('numero')
        )

        consumido_por_material = defaultdict(Decimal)
        pendientes = []
        for orden in ordenes:
            cantidad_total = orden.cantidad_total
            if cantidad_total <= 0:
                continue
            pendientes.append(orden)
            for c in orden.referencia.consumos.all():
                consumido_por_material[c.material_id] += (
                    c.cantidad_consumida * cantidad_total
                )

        if not pendientes:
            self.stdout.write(self.style.SUCCESS(
                'Todas las órdenes fuera de Pendiente ya tienen el material descontado.'
            ))
            return

        self.stdout.write(self.style.NOTICE(
            f'\nÓrdenes por descontar: {len(pendientes)}\n'
        ))
        header = f'{"N°":>5}  {"Referencia":<20}  {"Estado":<12}  {"Pares":>6}'
        self.stdout.write(header)
        self.stdout.write('-' * len(header))
        for orden in pendientes:
            self.stdout.write(
                f'{orden.numero:>5}  {orden.referencia.codigo[:20]:<20}  '
                f'{orden.estado:<12}  {orden.cantidad_total:>6}'
            )

        materiales = {
            m.pk: m for m in Material.objects.filter(pk__in=consumido_por_material)
        }

        self.stdout.write(self.style.NOTICE(
            f'\nMateriales afectados: {len(consumido_por_material)}\n'
        ))
        header = f'{"Material":<35} {"Stock actual":>14} {"A descontar":>14} {"Stock nuevo":>14}'
        self.stdout.write(header)
        self.stdout.write('-' * len(header))

        hay_negativos = False
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
                '\nAviso: algunos materiales quedarán en stock negativo. Revisá '
                'esos casos antes de aplicar.'
            ))

        if not aplicar:
            self.stdout.write(self.style.WARNING(
                '\n[DRY-RUN] No se modificó nada. '
                'Ejecutá con --aplicar para descontar.'
            ))
            return

        with transaction.atomic():
            for mat_id, total in consumido_por_material.items():
                Material.objects.filter(pk=mat_id).update(
                    cantidad_stock=F('cantidad_stock') - total
                )
            OrdenProduccion.objects.filter(
                pk__in=[o.pk for o in pendientes]
            ).update(materiales_descontados=True)

        self.stdout.write(self.style.SUCCESS(
            f'\nStock actualizado para {len(consumido_por_material)} materiales. '
            f'{len(pendientes)} órdenes marcadas como descontadas.'
        ))
