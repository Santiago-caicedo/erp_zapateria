"""Borrado de registros protegidos por claves foráneas con PROTECT.

Dos niveles:

  - Borrado normal: `procesar_borrado` traduce el ProtectedError a un mensaje
    legible en vez de reventar con un 500.
  - Eliminación forzada: arrastra en cascada todo lo que protege al registro.
    Reservada a superusuarios y siempre precedida de la vista previa exacta
    que calcula `simular_eliminacion`.
"""
import logging
from collections import Counter

from django.apps import apps
from django.contrib import messages
from django.db import transaction
from django.db.models import ProtectedError
from django.shortcuts import redirect

logger = logging.getLogger(__name__)

# Tope de vueltas por objeto para no quedar en bucle si el esquema tuviera
# un ciclo de FKs protegidas.
MAX_ITERACIONES = 20


class _Rollback(Exception):
    """Aborta la transacción de simulación llevándose el resumen calculado."""

    def __init__(self, resumen):
        self.resumen = resumen
        super().__init__()


def eliminar_en_cascada(objeto, _profundidad=0):
    """Borra `objeto` eliminando antes todo lo que lo bloquea por PROTECT.

    Devuelve un Counter {'app.Modelo': cantidad} con todo lo borrado.
    Debe ejecutarse dentro de una transacción.
    """
    if _profundidad > MAX_ITERACIONES:
        raise RuntimeError('Cadena de dependencias protegidas demasiado profunda.')

    resumen = Counter()
    for _ in range(MAX_ITERACIONES):
        try:
            _, por_modelo = objeto.delete()
        except ProtectedError as e:
            # ProtectedError se lanza al recolectar, antes de ejecutar ningún
            # DELETE, así que la transacción sigue sana y se puede continuar.
            for protegido in e.protected_objects:
                resumen.update(eliminar_en_cascada(protegido, _profundidad + 1))
            continue
        resumen.update(por_modelo)
        return resumen

    raise RuntimeError(f'No se pudo eliminar {objeto._meta.label} tras {MAX_ITERACIONES} intentos.')


def simular_eliminacion(objeto):
    """Calcula qué se borraría, ejecutando el borrado y deshaciéndolo.

    El resultado es exacto porque corre exactamente el mismo código que el
    borrado real, dentro de una transacción que siempre se revierte. A cambio
    toma locks de fila un instante, algo asumible al volumen de este sistema.
    """
    pk_original = objeto.pk
    try:
        with transaction.atomic():
            raise _Rollback(eliminar_en_cascada(objeto))
    except _Rollback as corte:
        resumen = corte.resumen
    finally:
        # delete() deja el pk en None sobre el objeto en memoria.
        objeto.pk = pk_original
    return resumen


def resumen_legible(resumen):
    """Convierte el Counter en filas ordenadas para mostrar en pantalla."""
    filas = []
    for etiqueta, cantidad in resumen.items():
        meta = apps.get_model(etiqueta)._meta
        nombre = meta.verbose_name if cantidad == 1 else meta.verbose_name_plural
        filas.append({'nombre': str(nombre).capitalize(), 'cantidad': cantidad})
    return sorted(filas, key=lambda f: (-f['cantidad'], f['nombre']))


def texto_resumen(resumen):
    """Versión de una línea del resumen, para los mensajes de feedback."""
    return ', '.join(
        f'{fila["cantidad"]} {fila["nombre"].lower()}'
        for fila in resumen_legible(resumen)
    )


def contexto_bloqueo(request, objeto, bloqueos):
    """Extras de contexto para una pantalla de confirmación de borrado.

    Solo calcula la vista previa de la eliminación forzada si hay bloqueos y
    quien mira es superusuario.
    """
    contexto = {'bloqueos': bloqueos}
    if bloqueos and request.user.is_superuser:
        contexto['resumen_forzado'] = resumen_legible(simular_eliminacion(objeto))
    return contexto


def procesar_borrado(request, objeto, nombre, url_destino, mensaje_ok, mensaje_bloqueo):
    """Procesa el POST de una pantalla de confirmación de borrado.

    Con `forzar=si` y superusuario arrastra en cascada todo lo que protege al
    registro. En cualquier otro caso hace el borrado normal y, si una FK
    PROTECT lo impide, deja `mensaje_bloqueo` en vez de reventar con un 500.
    """
    if request.POST.get('forzar') == 'si':
        if not request.user.is_superuser:
            messages.error(request, 'Solo un superusuario puede forzar una eliminación.')
            return redirect(url_destino)

        etiqueta = objeto._meta.label
        with transaction.atomic():
            resumen = eliminar_en_cascada(objeto)
        logger.warning(
            'Eliminación forzada de %s "%s" por %s. Borrado: %s',
            etiqueta, nombre, request.user, dict(resumen),
        )
        messages.warning(
            request,
            f'Eliminación forzada de "{nombre}". Registros eliminados: {texto_resumen(resumen)}.',
        )
        return redirect(url_destino)

    try:
        objeto.delete()
    except ProtectedError:
        messages.error(request, mensaje_bloqueo)
        return redirect(url_destino)

    messages.success(request, mensaje_ok)
    return redirect(url_destino)
