from django.db import models
from empleados.models import Empleado
from inventario.models import Referencia, ProcesoReferencia


# 1. Catálogo de Clientes
class Cliente(models.Model):
    nombre = models.CharField(max_length=150, verbose_name="Nombre o Empresa")
    contacto = models.CharField(max_length=150, blank=True, null=True, verbose_name="Persona de Contacto")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    direccion = models.TextField(blank=True, null=True, verbose_name="Dirección")

    def __str__(self):
        return self.nombre


# 2. La Orden de Producción
class OrdenProduccion(models.Model):
    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('En Proceso', 'En Proceso'),
        ('Finalizado', 'Finalizado'),
        ('Entregado', 'Entregado'),
    ]

    numero = models.PositiveIntegerField(unique=True, editable=False, verbose_name="Número de Orden")
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='ordenes')
    referencia = models.ForeignKey(Referencia, on_delete=models.PROTECT, related_name='ordenes', verbose_name="Referencia")
    fecha_creacion = models.DateField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_entrega = models.DateField(verbose_name="Fecha de Entrega Estimada")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente', verbose_name="Estado")

    # Tallas
    talla_34 = models.PositiveIntegerField(default=0, verbose_name="Talla 34")
    talla_35 = models.PositiveIntegerField(default=0, verbose_name="Talla 35")
    talla_36 = models.PositiveIntegerField(default=0, verbose_name="Talla 36")
    talla_37 = models.PositiveIntegerField(default=0, verbose_name="Talla 37")
    talla_38 = models.PositiveIntegerField(default=0, verbose_name="Talla 38")
    talla_39 = models.PositiveIntegerField(default=0, verbose_name="Talla 39")
    talla_40 = models.PositiveIntegerField(default=0, verbose_name="Talla 40")

    @property
    def cantidad_total(self):
        return (
            self.talla_34 + self.talla_35 + self.talla_36 +
            self.talla_37 + self.talla_38 + self.talla_39 + self.talla_40
        )

    def save(self, *args, **kwargs):
        if not self.numero:
            max_num = OrdenProduccion.objects.aggregate(
                max_num=models.Max('numero')
            )['max_num']
            self.numero = (max_num or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Orden #{self.numero} - {self.cliente.nombre} ({self.estado})"


# 3. El registro de trabajo para la Nómina
class RegistroTrabajo(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name='trabajos')
    orden = models.ForeignKey(OrdenProduccion, on_delete=models.CASCADE, related_name='registros_trabajo')
    proceso_referencia = models.ForeignKey(ProcesoReferencia, on_delete=models.PROTECT)
    cantidad_realizada = models.PositiveIntegerField(verbose_name="Cantidad Realizada")
    fecha = models.DateField(auto_now_add=True, verbose_name="Fecha de Registro")
    pagado = models.BooleanField(default=False, verbose_name="Pagado")
    fecha_pago = models.DateField(null=True, blank=True, verbose_name="Fecha de Pago")

    def __str__(self):
        return f"{self.empleado.nombre} - {self.proceso_referencia.proceso_base.nombre} ({self.cantidad_realizada} pares)"

    @property
    def total_pago(self):
        return self.cantidad_realizada * self.proceso_referencia.precio_mano_obra
