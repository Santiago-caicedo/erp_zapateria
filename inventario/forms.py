from django import forms
from .models import TipoMaterial, Material, ProcesoBase, Referencia, ConsumoMaterial, ProcesoReferencia


class TipoMaterialForm(forms.ModelForm):
    class Meta:
        model = TipoMaterial
        fields = ['nombre']


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['tipo', 'nombre', 'unidad_medida', 'cantidad_stock']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
        }


class ProcesoBaseForm(forms.ModelForm):
    class Meta:
        model = ProcesoBase
        fields = ['nombre']


class ReferenciaForm(forms.ModelForm):
    class Meta:
        model = Referencia
        fields = ['codigo', 'descripcion', 'talla', 'color', 'precio_venta']


class ConsumoMaterialForm(forms.ModelForm):
    class Meta:
        model = ConsumoMaterial
        fields = ['material', 'cantidad_consumida']
        widgets = {
            'material': forms.Select(attrs={'class': 'form-select'}),
        }


class ProcesoReferenciaForm(forms.ModelForm):
    class Meta:
        model = ProcesoReferencia
        fields = ['proceso_base', 'precio_mano_obra']
        widgets = {
            'proceso_base': forms.Select(attrs={'class': 'form-select'}),
        }


class ReferenciaConProcesosForm(forms.ModelForm):
    """
    Form de Referencia que incluye dinámicamente todos los ProcesoBase
    como checkboxes con campo de precio.
    """
    class Meta:
        model = Referencia
        fields = ['codigo', 'descripcion', 'talla', 'color', 'precio_venta']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Precios existentes indexados por proceso_base_id
        precios_existentes = {}
        if self.instance and self.instance.pk:
            for pr in self.instance.procesos.select_related('proceso_base').all():
                precios_existentes[pr.proceso_base_id] = pr.precio_mano_obra

        # Crear un campo checkbox + precio por cada ProcesoBase
        for proceso in ProcesoBase.objects.all().order_by('nombre'):
            check_field = f'proceso_{proceso.pk}_aplica'
            precio_field = f'proceso_{proceso.pk}_precio'

            self.fields[check_field] = forms.BooleanField(
                required=False,
                label=proceso.nombre,
                initial=proceso.pk in precios_existentes,
            )
            self.fields[precio_field] = forms.DecimalField(
                required=False,
                max_digits=10,
                decimal_places=2,
                label=f'Precio {proceso.nombre}',
                initial=precios_existentes.get(proceso.pk, ''),
            )

    def clean(self):
        cleaned = super().clean()
        for proceso in ProcesoBase.objects.all():
            check = cleaned.get(f'proceso_{proceso.pk}_aplica')
            precio = cleaned.get(f'proceso_{proceso.pk}_precio')
            if check and (precio is None or precio <= 0):
                self.add_error(
                    f'proceso_{proceso.pk}_precio',
                    f'Debes indicar el precio para {proceso.nombre}.'
                )
        return cleaned

    def save(self, commit=True):
        referencia = super().save(commit=commit)
        if commit:
            self._save_procesos(referencia)
        return referencia

    def _save_procesos(self, referencia):
        procesos_actuales = {
            pr.proceso_base_id: pr
            for pr in referencia.procesos.all()
        }

        for proceso in ProcesoBase.objects.all():
            aplica = self.cleaned_data.get(f'proceso_{proceso.pk}_aplica')
            precio = self.cleaned_data.get(f'proceso_{proceso.pk}_precio')

            if aplica and precio:
                if proceso.pk in procesos_actuales:
                    # Actualizar precio si cambió
                    pr = procesos_actuales[proceso.pk]
                    if pr.precio_mano_obra != precio:
                        pr.precio_mano_obra = precio
                        pr.save()
                else:
                    # Crear nuevo
                    ProcesoReferencia.objects.create(
                        referencia=referencia,
                        proceso_base=proceso,
                        precio_mano_obra=precio,
                    )
            elif not aplica and proceso.pk in procesos_actuales:
                # Desmarcar = eliminar relación
                procesos_actuales[proceso.pk].delete()
