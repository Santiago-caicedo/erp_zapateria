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

# 2. Catálogo de Procesos (Corte, Guarnición, etc.)
class ProcesoBase(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Proceso")

    def __str__(self):
        return self.nombre

# 3. La Referencia (El Zapato)
class Referencia(models.Model):
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código/Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    talla = models.CharField(max_length=10, verbose_name="Talla")
    color = models.CharField(max_length=50, verbose_name="Color")
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de Venta")

    def __str__(self):
        return f"{self.codigo} - {self.talla} - {self.color}"

# 4. Relación: Qué materiales gasta este zapato
class ConsumoMaterial(models.Model):
    referencia = models.ForeignKey(Referencia, on_delete=models.CASCADE, related_name='consumos')
    material = models.ForeignKey(Material, on_delete=models.PROTECT) # PROTECT evita borrar un material si un zapato lo usa
    cantidad_consumida = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Cantidad Consumida")

    def __str__(self):
        return f"{self.referencia.codigo} consume {self.cantidad_consumida} de {self.material.nombre}"

# 5. Relación: Qué procesos lleva este zapato y cuánto se paga por ellos
class ProcesoReferencia(models.Model):
    referencia = models.ForeignKey(Referencia, on_delete=models.CASCADE, related_name='procesos')
    proceso_base = models.ForeignKey(ProcesoBase, on_delete=models.PROTECT)
    precio_mano_obra = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Mano de Obra")

    def __str__(self):
        return f"{self.proceso_base.nombre} para {self.referencia.codigo} - ${self.precio_mano_obra}"