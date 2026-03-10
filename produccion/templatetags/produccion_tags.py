from decimal import Decimal
from django import template

register = template.Library()


@register.filter
def get_talla_field(form, talla):
    """Retorna el widget del campo de talla."""
    field_name = f'talla_{talla}'
    field = form[field_name]
    return field


@register.filter
def peso(valor):
    """Formatea un valor numérico como peso colombiano con separador de miles.
    Ej: 1250000 → $1.250.000 | 3500.50 → $3.500
    """
    if valor is None:
        return '$0'
    try:
        num = Decimal(str(valor))
    except Exception:
        return f'${valor}'
    # Redondear a entero para pesos (sin centavos)
    entero = int(num.quantize(Decimal('1')))
    formateado = f'{entero:,}'.replace(',', '.')
    return f'${formateado}'


@register.filter
def miles(valor):
    """Formatea un número con separador de miles (sin signo de peso).
    Ej: 1250000 → 1.250.000
    """
    if valor is None:
        return '0'
    try:
        num = Decimal(str(valor))
    except Exception:
        return str(valor)
    entero = int(num.quantize(Decimal('1')))
    return f'{entero:,}'.replace(',', '.')
