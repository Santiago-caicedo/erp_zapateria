from django import forms
from .models import Cliente, OrdenProduccion, RegistroTrabajo


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'contacto', 'telefono', 'direccion']


class OrdenProduccionForm(forms.ModelForm):
    class Meta:
        model = OrdenProduccion
        fields = [
            'cliente', 'referencia', 'fecha_entrega',
            'talla_34', 'talla_35', 'talla_36', 'talla_37',
            'talla_38', 'talla_39', 'talla_40',
        ]
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'referencia': forms.Select(attrs={'class': 'form-select', 'id': 'id_referencia'}),
            'fecha_entrega': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'talla_34': forms.NumberInput(attrs={'class': 'form-control talla-input', 'min': '0', 'value': '0'}),
            'talla_35': forms.NumberInput(attrs={'class': 'form-control talla-input', 'min': '0', 'value': '0'}),
            'talla_36': forms.NumberInput(attrs={'class': 'form-control talla-input', 'min': '0', 'value': '0'}),
            'talla_37': forms.NumberInput(attrs={'class': 'form-control talla-input', 'min': '0', 'value': '0'}),
            'talla_38': forms.NumberInput(attrs={'class': 'form-control talla-input', 'min': '0', 'value': '0'}),
            'talla_39': forms.NumberInput(attrs={'class': 'form-control talla-input', 'min': '0', 'value': '0'}),
            'talla_40': forms.NumberInput(attrs={'class': 'form-control talla-input', 'min': '0', 'value': '0'}),
        }

    def clean(self):
        cleaned = super().clean()
        total = sum(
            cleaned.get(f'talla_{t}', 0) or 0
            for t in range(34, 41)
        )
        if total == 0:
            raise forms.ValidationError('Debes indicar al menos una talla con cantidad mayor a 0.')
        return cleaned


class OrdenEditarForm(forms.ModelForm):
    class Meta:
        model = OrdenProduccion
        fields = [
            'cliente', 'referencia', 'fecha_entrega', 'estado',
            'talla_34', 'talla_35', 'talla_36', 'talla_37',
            'talla_38', 'talla_39', 'talla_40',
        ]
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'referencia': forms.Select(attrs={'class': 'form-select', 'id': 'id_referencia'}),
            'fecha_entrega': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'talla_34': forms.NumberInput(attrs={'class': 'form-control talla-input', 'min': '0'}),
            'talla_35': forms.NumberInput(attrs={'class': 'form-control talla-input', 'min': '0'}),
            'talla_36': forms.NumberInput(attrs={'class': 'form-control talla-input', 'min': '0'}),
            'talla_37': forms.NumberInput(attrs={'class': 'form-control talla-input', 'min': '0'}),
            'talla_38': forms.NumberInput(attrs={'class': 'form-control talla-input', 'min': '0'}),
            'talla_39': forms.NumberInput(attrs={'class': 'form-control talla-input', 'min': '0'}),
            'talla_40': forms.NumberInput(attrs={'class': 'form-control talla-input', 'min': '0'}),
        }


class RegistroTrabajoForm(forms.ModelForm):
    class Meta:
        model = RegistroTrabajo
        fields = ['empleado', 'proceso_referencia']
        widgets = {
            'empleado': forms.Select(attrs={'class': 'form-select'}),
            'proceso_referencia': forms.Select(attrs={'class': 'form-select'}),
        }
