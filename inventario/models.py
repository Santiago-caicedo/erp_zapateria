from django.db import models


# 1. Tipos de Material (Capellada, Forro, Suela, etc.)
class TipoMaterial(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Tipo de Material")

    class Meta:
        verbose_name = "Tipo de Material"
        verbose_name_plural = "Tipos de Material"

    def __str__(self):
        return self.nombre


# 2. Catálogo de Materiales
class Material(models.Model):
    tipo = models.ForeignKey(TipoMaterial, on_delete=models.PROTECT, related_name='materiales', verbose_name="Tipo")
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Material")
    unidad_medida = models.CharField(max_length=50, help_text="Ej: cm2, metros, unidades")
    cantidad_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Cantidad en Stock")

    class Meta:
        unique_together = ['tipo', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.unidad_medida})"


# 3. Catálogo de Procesos (Corte, Guarnición, etc.)
class ProcesoBase(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Proceso")

    def __str__(self):
        return self.nombre


# 4. Tipo de Zapato (Bota, Sandalia, Tacón, etc.)
class TipoZapato(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Tipo de Zapato")

    class Meta:
        verbose_name = "Tipo de Zapato"
        verbose_name_plural = "Tipos de Zapato"

    def __str__(self):
        return self.nombre


# 5. La Referencia (El Zapato)
class Referencia(models.Model):
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código/Nombre")
    tipo_zapato = models.ForeignKey(TipoZapato, on_delete=models.PROTECT, related_name='referencias', verbose_name="Tipo de Zapato")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    imagen = models.ImageField(upload_to='referencias/', blank=True, null=True, verbose_name="Imagen")

    def __str__(self):
        return f"{self.codigo} - {self.tipo_zapato.nombre}"


# 6. Relación: Qué materiales gasta este zapato
class ConsumoMaterial(models.Model):
    referencia = models.ForeignKey(Referencia, on_delete=models.CASCADE, related_name='consumos')
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    cantidad_consumida = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Cantidad Consumida")

    class Meta:
        unique_together = ['referencia', 'material']

    def __str__(self):
        return f"{self.referencia.codigo} consume {self.cantidad_consumida} de {self.material.nombre}"


# 7. Relación: Qué procesos lleva este zapato y cuánto se paga por ellos
class ProcesoReferencia(models.Model):
    referencia = models.ForeignKey(Referencia, on_delete=models.CASCADE, related_name='procesos')
    proceso_base = models.ForeignKey(ProcesoBase, on_delete=models.PROTECT)
    precio_mano_obra = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Mano de Obra")

    def __str__(self):
        return f"{self.proceso_base.nombre} para {self.referencia.codigo} - ${self.precio_mano_obra}"
