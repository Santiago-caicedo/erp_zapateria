from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    # TipoMaterial
    path('tipos-material/', views.tipo_material_lista, name='tipo_material_lista'),
    path('tipos-material/crear/', views.tipo_material_crear, name='tipo_material_crear'),
    path('tipos-material/<int:pk>/editar/', views.tipo_material_editar, name='tipo_material_editar'),
    path('tipos-material/<int:pk>/eliminar/', views.tipo_material_eliminar, name='tipo_material_eliminar'),

    # Material
    path('materiales/', views.material_lista, name='material_lista'),
    path('materiales/crear/', views.material_crear, name='material_crear'),
    path('materiales/<int:pk>/editar/', views.material_editar, name='material_editar'),
    path('materiales/<int:pk>/eliminar/', views.material_eliminar, name='material_eliminar'),
    path('materiales/<int:pk>/agregar-stock/', views.material_agregar_stock, name='material_agregar_stock'),

    # ProcesoBase
    path('procesos/', views.proceso_lista, name='proceso_lista'),
    path('procesos/crear/', views.proceso_crear, name='proceso_crear'),
    path('procesos/<int:pk>/editar/', views.proceso_editar, name='proceso_editar'),
    path('procesos/<int:pk>/eliminar/', views.proceso_eliminar, name='proceso_eliminar'),

    # Referencia
    path('referencias/', views.referencia_lista, name='referencia_lista'),
    path('referencias/crear/', views.referencia_crear, name='referencia_crear'),
    path('referencias/<int:pk>/', views.referencia_detalle, name='referencia_detalle'),
    path('referencias/<int:pk>/editar/', views.referencia_editar, name='referencia_editar'),
    path('referencias/<int:pk>/eliminar/', views.referencia_eliminar, name='referencia_eliminar'),

    # ConsumoMaterial (hijo de referencia)
    path('referencias/<int:referencia_pk>/consumo/agregar/', views.consumo_agregar, name='consumo_agregar'),
    path('consumo/<int:pk>/eliminar/', views.consumo_eliminar, name='consumo_eliminar'),

    # ProcesoReferencia (hijo de referencia)
    path('referencias/<int:referencia_pk>/proceso/agregar/', views.proceso_ref_agregar, name='proceso_ref_agregar'),
    path('proceso-ref/<int:pk>/eliminar/', views.proceso_ref_eliminar, name='proceso_ref_eliminar'),
]
