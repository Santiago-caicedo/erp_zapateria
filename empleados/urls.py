from django.urls import path
from . import views

app_name = 'empleados'

urlpatterns = [
    path('', views.empleado_lista, name='lista'),
    path('crear/', views.empleado_crear, name='crear'),
    path('<int:pk>/', views.empleado_detalle, name='detalle'),
    path('<int:pk>/editar/', views.empleado_editar, name='editar'),
    path('<int:pk>/eliminar/', views.empleado_eliminar, name='eliminar'),
]
