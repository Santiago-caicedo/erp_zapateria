from django.urls import path
from . import views

app_name = 'produccion'

urlpatterns = [
    # Cliente
    path('clientes/', views.cliente_lista, name='cliente_lista'),
    path('clientes/crear/', views.cliente_crear, name='cliente_crear'),
    path('clientes/<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('clientes/<int:pk>/eliminar/', views.cliente_eliminar, name='cliente_eliminar'),

    # OrdenProduccion
    path('ordenes/', views.orden_lista, name='orden_lista'),
    path('ordenes/crear/', views.orden_crear, name='orden_crear'),
    path('ordenes/<int:pk>/', views.orden_detalle, name='orden_detalle'),
    path('ordenes/<int:pk>/editar/', views.orden_editar, name='orden_editar'),
    path('ordenes/<int:pk>/eliminar/', views.orden_eliminar, name='orden_eliminar'),

    # DetalleOrden (hijo de orden)
    path('ordenes/<int:orden_pk>/detalle/agregar/', views.detalle_agregar, name='detalle_agregar'),
    path('detalle/<int:pk>/eliminar/', views.detalle_eliminar, name='detalle_eliminar'),

    # RegistroTrabajo (hijo de detalle)
    path('detalle/<int:detalle_pk>/registro/agregar/', views.registro_agregar, name='registro_agregar'),
    path('registro/<int:pk>/eliminar/', views.registro_eliminar, name='registro_eliminar'),

    # Nómina
    path('nomina/', views.nomina, name='nomina'),
    path('nomina/<int:empleado_pk>/', views.nomina_detalle_empleado, name='nomina_detalle'),
]
