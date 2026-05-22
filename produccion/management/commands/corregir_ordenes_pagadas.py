"""
Corrige órdenes mal marcadas como 'Pagado' por el bug previo de
`_verificar_orden_pagada`, que comparaba contra los RegistroTrabajo
existentes en vez del total de procesos de la referencia.

Una orden solo debe estar en 'Pagado' cuando todos los procesos de la
referencia tienen RegistroTrabajo Y todos están con pagado=True.
Si no, se revierte al estado real:
  - sin todos los procesos registrados → 'En Proceso'
  - con todos registrados pero alguno sin pagar → 'Finalizado'

Uso:
    python manage.py corregir_ordenes_pagadas              # solo muestra reporte
    python manage.py corregir_ordenes_pagadas --aplicar    # aplica los cambios
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from produccion.models import OrdenProduccion


class Command(BaseCommand):
    help = (
        'Revierte el estado de órdenes mal marcadas como Pagado cuando aún '
        'les faltan procesos por registrar o por pagar.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--aplicar',
            action='store_true',
            help='Aplica los cambios en la base de datos.',
        )

    def handle(self, *args, **options):
        aplicar = options['aplicar']

        ordenes = (
            OrdenProduccion.objects
            .filter(estado='Pagado')
            .select_related('referencia')
            .prefetch_related('registros_trabajo', 'referencia__procesos')
            .order_by('numero')
        )

        a_revertir = []
        for orden in ordenes:
            total_procesos = orden.referencia.procesos.count()
            registros = list(orden.registros_trabajo.all())
            total_registros = len(registros)
            total_pagados = sum(1 for r in registros if r.pagado)

            if total_procesos == 0:
                continue

            if total_pagados >= total_procesos:
                # Está bien marcada como Pagado.
                continue

            # Determinar estado correcto.
            if total_registros < total_procesos:
                nuevo_estado = 'En Proceso'
            else:
                nuevo_estado = 'Finalizado'

            a_revertir.append({
                'orden': orden,
                'total_procesos': total_procesos,
                'total_registros': total_registros,
                'total_pagados': total_pagados,
                'nuevo_estado': nuevo_estado,
            })

        if not a_revertir:
            self.stdout.write(self.style.SUCCESS(
                'No hay órdenes en estado Pagado que requieran corrección.'
            ))
            return

        self.stdout.write(self.style.NOTICE(
            f'\nÓrdenes a revertir: {len(a_revertir)}\n'
        ))
        header = (
            f'{"N°":>5}  {"Referencia":<20}  {"Procesos":>8}  '
            f'{"Registrados":>11}  {"Pagados":>8}  {"Nuevo estado":<15}'
        )
        self.stdout.write(header)
        self.stdout.write('-' * len(header))

        for item in a_revertir:
            o = item['orden']
            self.stdout.write(
                f'{o.numero:>5}  {o.referencia.codigo[:20]:<20}  '
                f'{item["total_procesos"]:>8}  {item["total_registros"]:>11}  '
                f'{item["total_pagados"]:>8}  {item["nuevo_estado"]:<15}'
            )

        if not aplicar:
            self.stdout.write(self.style.WARNING(
                '\n[DRY-RUN] No se modificó nada. '
                'Ejecutá con --aplicar para revertir el estado.'
            ))
            return

        with transaction.atomic():
            for item in a_revertir:
                o = item['orden']
                o.estado = item['nuevo_estado']
                o.fecha_pagado = None
                o.save(update_fields=['estado', 'fecha_pagado'])

        self.stdout.write(self.style.SUCCESS(
            f'\n{len(a_revertir)} órdenes revertidas. Las que aún tenían '
            'procesos sin registrar quedan en "En Proceso" y se les puede '
            'registrar trabajo nuevamente.'
        ))
