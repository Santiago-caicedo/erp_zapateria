from django.db import models

class Empleado(models.Model):
    nombre = models.CharField(max_length=150, verbose_name="Nombre Completo")
    documento = models.CharField(max_length=20, unique=True, verbose_name="Documento de Identidad")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    rol = models.CharField(max_length=100, verbose_name="Rol o Cargo")
    fecha_ingreso = models.DateField(auto_now_add=True, verbose_name="Fecha de Ingreso")

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"

    def __str__(self):
        return f"{self.nombre} - {self.rol}"