from django import forms
from .models import (
    TipoMaterial, Material, ProcesoBase,
    TipoZapato, Referencia, ConsumoMaterial, ProcesoReferencia,
)


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
        fields = ['codigo', 'tipo_zapato', 'descripcion', 'imagen']
        widgets = {
            'tipo_zapato': forms.Select(attrs={'class': 'form-select'}),
        }


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
    nuevo_tipo_zapato = forms.CharField(
        required=False,
        label='O crear nuevo tipo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del nuevo tipo...',
        }),
    )

    class Meta:
        model = Referencia
        fields = ['codigo', 'tipo_zapato', 'descripcion', 'imagen']
        widgets = {
            'tipo_zapato': forms.Select(attrs={'class': 'form-select'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_zapato'].required = False

        # Procesos dinámicos
        precios_existentes = {}
        if self.instance and self.instance.pk:
            for pr in self.instance.procesos.select_related('proceso_base').all():
                precios_existentes[pr.proceso_base_id] = pr.precio_mano_obra

        for proceso in ProcesoBase.objects.all().order_by('nombre'):
            self.fields[f'proceso_{proceso.pk}_aplica'] = forms.BooleanField(
                required=False,
                label=proceso.nombre,
                initial=proceso.pk in precios_existentes,
            )
            self.fields[f'proceso_{proceso.pk}_precio'] = forms.DecimalField(
                required=False,
                max_digits=10,
                decimal_places=2,
                label=f'Precio {proceso.nombre}',
                initial=precios_existentes.get(proceso.pk, ''),
            )

        # Materiales dinámicos
        consumos_existentes = {}
        if self.instance and self.instance.pk:
            for c in self.instance.consumos.select_related('material').all():
                consumos_existentes[c.material_id] = c.cantidad_consumida

        for material in Material.objects.select_related('tipo').all().order_by('tipo__nombre', 'nombre'):
            self.fields[f'mat_{material.pk}_check'] = forms.BooleanField(
                required=False,
                label=material.nombre,
                initial=material.pk in consumos_existentes,
            )
            self.fields[f'mat_{material.pk}_cantidad'] = forms.DecimalField(
                required=False,
                max_digits=8,
                decimal_places=2,
                label=f'Cantidad {material.nombre}',
                initial=consumos_existentes.get(material.pk, ''),
            )

    def clean(self):
        cleaned = super().clean()

        tipo_zapato = cleaned.get('tipo_zapato')
        nuevo = cleaned.get('nuevo_tipo_zapato', '').strip()
        if not tipo_zapato and not nuevo:
            self.add_error('tipo_zapato', 'Selecciona un tipo o crea uno nuevo.')
        elif nuevo:
            tipo_zapato, _ = TipoZapato.objects.get_or_create(nombre=nuevo)
            cleaned['tipo_zapato'] = tipo_zapato

        # Validar procesos
        for proceso in ProcesoBase.objects.all():
            check = cleaned.get(f'proceso_{proceso.pk}_aplica')
            precio = cleaned.get(f'proceso_{proceso.pk}_precio')
            if check and (precio is None or precio <= 0):
                self.add_error(
                    f'proceso_{proceso.pk}_precio',
                    f'Indica el precio para {proceso.nombre}.'
                )

        # Validar materiales
        for material in Material.objects.all():
            check = cleaned.get(f'mat_{material.pk}_check')
            cantidad = cleaned.get(f'mat_{material.pk}_cantidad')
            if check and (cantidad is None or cantidad <= 0):
                self.add_error(
                    f'mat_{material.pk}_cantidad',
                    f'Indica la cantidad para {material.nombre}.'
                )

        return cleaned

    def save(self, commit=True):
        referencia = super().save(commit=commit)
        if commit:
            self._save_procesos(referencia)
            self._save_consumos(referencia)
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
                    pr = procesos_actuales[proceso.pk]
                    if pr.precio_mano_obra != precio:
                        pr.precio_mano_obra = precio
                        pr.save()
                else:
                    ProcesoReferencia.objects.create(
                        referencia=referencia,
                        proceso_base=proceso,
                        precio_mano_obra=precio,
                    )
            elif not aplica and proceso.pk in procesos_actuales:
                procesos_actuales[proceso.pk].delete()

    def _save_consumos(self, referencia):
        consumos_actuales = {
            c.material_id: c
            for c in referencia.consumos.all()
        }
        for material in Material.objects.all():
            check = self.cleaned_data.get(f'mat_{material.pk}_check')
            cantidad = self.cleaned_data.get(f'mat_{material.pk}_cantidad')
            if check and cantidad:
                if material.pk in consumos_actuales:
                    c = consumos_actuales[material.pk]
                    if c.cantidad_consumida != cantidad:
                        c.cantidad_consumida = cantidad
                        c.save()
                else:
                    ConsumoMaterial.objects.create(
                        referencia=referencia,
                        material=material,
                        cantidad_consumida=cantidad,
                    )
            elif not check and material.pk in consumos_actuales:
                consumos_actuales[material.pk].delete()
