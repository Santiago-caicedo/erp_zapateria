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
    path('ordenes/<int:pk>/pdf/', views.orden_pdf, name='orden_pdf'),

    # RegistroTrabajo
    path('registro-trabajo/', views.registro_trabajo, name='registro_trabajo'),
    path('ordenes/<int:orden_pk>/registro/agregar/', views.registro_agregar, name='registro_agregar'),
    path('registro/<int:pk>/eliminar/', views.registro_eliminar, name='registro_eliminar'),

    # API
    path('api/referencia/<int:pk>/', views.api_referencia_detalle, name='api_referencia_detalle'),
    path('api/ordenes-activas/', views.api_ordenes_activas, name='api_ordenes_activas'),
    path('api/procesos-orden/<int:orden_pk>/', views.api_procesos_orden, name='api_procesos_orden'),

    # Nómina
    path('nomina/', views.nomina, name='nomina'),
    path('nomina/historial/', views.nomina_historial, name='nomina_historial'),
    path('nomina/<int:empleado_pk>/', views.nomina_detalle, name='nomina_detalle'),
    path('nomina/<int:empleado_pk>/pdf/', views.nomina_pdf, name='nomina_pdf'),
    path('nomina/<int:empleado_pk>/pagar/', views.nomina_marcar_pagado, name='nomina_marcar_pagado'),
]
