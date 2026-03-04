from django import forms
from .models import Cliente, OrdenProduccion, DetalleOrden, RegistroTrabajo


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'contacto', 'telefono', 'direccion']


class OrdenProduccionForm(forms.ModelForm):
    class Meta:
        model = OrdenProduccion
        fields = ['cliente', 'fecha_entrega', 'estado']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'fecha_entrega': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }


class DetalleOrdenForm(forms.ModelForm):
    class Meta:
        model = DetalleOrden
        fields = ['referencia', 'cantidad_solicitada']
        widgets = {
            'referencia': forms.Select(attrs={'class': 'form-select'}),
        }


class RegistroTrabajoForm(forms.ModelForm):
    class Meta:
        model = RegistroTrabajo
        fields = ['empleado', 'proceso_referencia', 'cantidad_realizada']
        widgets = {
            'empleado': forms.Select(attrs={'class': 'form-select'}),
            'proceso_referencia': forms.Select(attrs={'class': 'form-select'}),
        }
