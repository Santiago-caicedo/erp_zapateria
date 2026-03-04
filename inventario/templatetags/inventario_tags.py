from django import template

register = template.Library()


@register.filter
def get_field_value(form, proceso_pk):
    """Retorna si el checkbox del proceso está marcado."""
    field_name = f'proceso_{proceso_pk}_aplica'
    field = form.fields.get(field_name)
    if field is None:
        return False
    # Si el form fue enviado, usar cleaned_data o data
    if hasattr(form, 'cleaned_data') and form.cleaned_data:
        return form.cleaned_data.get(field_name, False)
    # Si no fue enviado, usar initial
    return field.initial


@register.filter
def get_precio_value(form, proceso_pk):
    """Retorna el valor del campo precio para un proceso."""
    field_name = f'proceso_{proceso_pk}_precio'
    # Si el form fue enviado con errores, mostrar lo que el usuario puso
    if form.is_bound:
        return form.data.get(field_name, '')
    # Si no, mostrar el initial
    field = form.fields.get(field_name)
    if field and field.initial:
        return field.initial
    return ''


@register.filter
def get_precio_error(form, proceso_pk):
    """Retorna el error del campo precio si existe."""
    field_name = f'proceso_{proceso_pk}_precio'
    errors = form.errors.get(field_name)
    if errors:
        return errors[0]
    return ''
