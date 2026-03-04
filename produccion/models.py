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

# 2. La Orden de Producción (Cabecera)
class OrdenProduccion(models.Model):
    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('En Proceso', 'En Proceso'),
        ('Finalizado', 'Finalizado'),
        ('Entregado', 'Entregado'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='ordenes')
    fecha_creacion = models.DateField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_entrega = models.DateField(verbose_name="Fecha de Entrega Estimada")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente', verbose_name="Estado")

    def __str__(self):
        return f"Orden #{self.id} - {self.cliente.nombre} ({self.estado})"

# 3. Qué zapatos lleva la orden (Detalle)
class DetalleOrden(models.Model):
    orden = models.ForeignKey(OrdenProduccion, on_delete=models.CASCADE, related_name='detalles')
    referencia = models.ForeignKey(Referencia, on_delete=models.PROTECT)
    cantidad_solicitada = models.PositiveIntegerField(verbose_name="Cantidad Solicitada")
    cantidad_fabricada = models.PositiveIntegerField(default=0, verbose_name="Cantidad Fabricada")

    def __str__(self):
        return f"{self.cantidad_solicitada}x {self.referencia.codigo} (Orden #{self.orden.id})"

# 4. El registro de trabajo para la Nómina
class RegistroTrabajo(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name='trabajos')
    detalle_orden = models.ForeignKey(DetalleOrden, on_delete=models.CASCADE, related_name='registros_trabajo')
    proceso_referencia = models.ForeignKey(ProcesoReferencia, on_delete=models.PROTECT)
    cantidad_realizada = models.PositiveIntegerField(verbose_name="Cantidad Realizada")
    fecha = models.DateField(auto_now_add=True, verbose_name="Fecha de Registro")

    def __str__(self):
        return f"{self.empleado.nombre} - {self.proceso_referencia.proceso_base.nombre} ({self.cantidad_realizada} pares)"
    
    @property
    def total_pago(self):
        # Multiplica la cantidad de zapatos hechos por el precio de ese proceso específico
        return self.cantidad_realizada * self.proceso_referencia.precio_mano_obra