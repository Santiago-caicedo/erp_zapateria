# ERP Zapatería

## Stack Tecnológico
- Django 6.0 + PostgreSQL
- Django Templates + Bootstrap 5 (CDN)
- python-decouple para variables de entorno (.env)
- Idioma: español (es-co), zona horaria America/Bogota

## Estructura del Proyecto
```
erp_zapateria/
├── config/          # Proyecto Django (settings, urls, wsgi)
├── empleados/       # App: Gestión de empleados
├── inventario/      # App: Referencias, materiales, procesos
├── produccion/      # App: Clientes, órdenes, registro de trabajo, nómina
├── templates/       # Templates globales
├── static/          # Archivos estáticos
├── .env             # Variables de entorno (NO commitear)
└── manage.py
```

## Módulos y Reglas de Negocio

### 1. Empleados (`empleados`)
- CRUD completo de empleados.
- Campos: nombre, documento (único), teléfono, rol, fecha_ingreso (automática).
- Un empleado se relaciona con el trabajo que realiza a través de `RegistroTrabajo` en producción.
- No se puede eliminar un empleado si tiene registros de trabajo asociados (PROTECT).

### 2. Inventario (`inventario`)
Contiene los catálogos base del negocio.

#### Material
- Catálogo de materiales (cuero, suela, hilo, etc.).
- Campos: nombre (único), unidad_medida, cantidad_stock.
- No se puede eliminar un material si alguna referencia lo consume (PROTECT).

#### ProcesoBase
- Catálogo de procesos de fabricación (corte, guarnición, soladura, emplantillado, etc.).
- Campo: nombre (único).
- No se puede eliminar si está asignado a alguna referencia (PROTECT).

#### Referencia (el zapato)
- "Referencia" es el término de la zapatería para un modelo de zapato.
- Campos: codigo (único), descripcion, talla, color, precio_venta.
- Cada referencia tiene asociados:
  - **ConsumoMaterial**: qué materiales consume y en qué cantidad por par.
  - **ProcesoReferencia**: qué procesos de fabricación lleva y cuánto se paga de mano de obra por cada uno.
- Los procesos y precios son específicos por referencia (el mismo proceso puede tener precio distinto en zapatos diferentes).

### 3. Producción (`produccion`)

#### Cliente
- CRUD de clientes.
- Campos: nombre, contacto, teléfono, dirección.
- No se puede eliminar un cliente si tiene órdenes asociadas (PROTECT).

#### OrdenProduccion (cabecera)
- Una orden de producción se crea para un cliente.
- Estados: Pendiente → En Proceso → Finalizado → Entregado.
- Campos: cliente, fecha_creacion (automática), fecha_entrega, estado.

#### DetalleOrden (líneas de la orden)
- Cada línea indica qué referencia se fabrica y cuántos pares.
- Campos: orden, referencia, cantidad_solicitada, cantidad_fabricada.
- cantidad_fabricada se actualiza conforme se registra trabajo.

#### RegistroTrabajo (nómina)
- Registro de que un empleado realizó un proceso específico sobre un detalle de orden.
- Campos: empleado, detalle_orden, proceso_referencia, cantidad_realizada, fecha (automática).
- El proceso_referencia debe corresponder a uno de los procesos definidos para la referencia del detalle_orden.
- **Cálculo de pago**: cantidad_realizada × proceso_referencia.precio_mano_obra.
- La nómina de un empleado es la suma de todos sus registros de trabajo en un periodo.

## Flujo de Trabajo
1. Configurar catálogos: Materiales y Procesos.
2. Crear Referencias: asignar materiales (consumo) y procesos (con precio de mano de obra).
3. Registrar Clientes.
4. Crear Orden de Producción para un cliente → agregar líneas (referencia + cantidad).
5. Registrar Trabajo: asignar empleado + proceso + cantidad a cada línea de orden.
6. Consultar Nómina: sumar pagos por empleado en un rango de fechas.

## Convenciones de Código
- Vistas basadas en funciones (FBV).
- ModelForms para formularios.
- URLs con namespaces por app (empleados:lista, inventario:material_lista, etc.).
- Nombres de templates: `app/modelo_accion.html` (ej: empleados/empleado_lista.html).
- Mensajes de feedback con django.contrib.messages.
- Eliminación siempre requiere confirmación por POST.
- Idioma de código y variables: español.
