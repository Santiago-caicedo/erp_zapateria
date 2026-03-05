from django import template

register = template.Library()


@register.filter
def get_talla_field(form, talla):
    """Retorna el widget del campo de talla."""
    field_name = f'talla_{talla}'
    field = form[field_name]
    return field
