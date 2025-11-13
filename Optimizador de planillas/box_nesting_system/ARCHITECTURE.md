# Arquitectura y contratos de módulos

Este documento describe, para cada módulo principal del sistema, las entradas que consume y las salidas que genera. El objetivo es dejar explícito qué depende de qué y qué formato deben respetar los datos que fluyen entre componentes.

> Nota: Todos los formatos mencionados están expresados en cm u otras unidades del SI, salvo que se indique lo contrario.

---

## Resumen de alto nivel (frontend vs backend)

| Capa | Módulo | Entradas clave | Salidas clave | Consumido por |
| --- | --- | --- | --- | --- |
| **Frontend** | `frontend.ui.main_window` | `PlanoParams`, señales Qt | Navegación de pestañas, diálogo de progreso | Usuario final |
| **Frontend** | `frontend.ui.plano_tab` | Entradas del editor (spins/sliders) | Nuevos `PlanoParams` | `MainWindow`, backend |
| **Frontend** | `frontend.ui.tile_tab` | Parámetros, `NestingEngine`, interacción del usuario | Render del layout, mensajes HTML | `MainWindow` |
| **Frontend** | `frontend.ui.widgets` | `PlanoParams`, data geométrica | `TileScene`, `ZoomGraphicsView` | `TileTab` |
| **Backend** | `backend.models.parameters/production` | Datos de UI o fixtures | Dataclasses validadas (`PlanoParams`, `ProductionParameters`) | Frontend, backend |
| **Backend** | `backend.nesting.engine` | Datos geométricos, políticas de búsqueda | Resultados de nesting, caché | `TileTab`, tests |
| **Backend** | `backend.nesting.algorithms/patterns/cache` | Polígonos, reglas del proceso | Patrones reutilizables, cachés | `NestingEngine` |
| **Backend** | `backend.geometry.*` | Puntos, polígonos, márgenes | Transformaciones, detección de colisiones, helpers de render | `NestingEngine`, `TileScene` |
| **Backend** | `backend.utils.*` | Configuración (logging, constantes, validaciones) | Servicios compartidos | Todo el sistema |
| **Infraestructura** | `main.py` | CLI/env, logging | Inicializa frontend/backend | Usuario final |
| **Pruebas** | `tests/*` | API pública | Validación de comportamiento | Desarrolladores |

---

## Módulo `main.py`

- **Entradas**
  - Argumentos del sistema (`sys.argv`).
  - Variables de entorno (para rutas, logs).
  - Ruta actual del proyecto.
- **Procesamiento**
  - Crea y configura `QApplication` (estilo, metadata).
  - Inicializa directorio de logs y `logging`.
  - Registra manejador global de excepciones.
  - Instancia `MainWindow`.
- **Salidas**
  - Ventana principal visible.
  - Log `logs/box_nesting_system.log`.
  - Código de salida del proceso.

---

## Módulo `ui.main_window`

- **Entradas**
  - Instancia `PlanoParams` inicial.
  - Referencias a `TileTab` y `PlanoTab`.
  - Señales de acciones de menú y botones.
- **Salidas**
  - Eventos Qt conectados (abrir/cerrar tabs, exportar).
  - Propagación de nuevos parámetros a `TileTab`.
  - Mensajes de error/éxito vía `QMessageBox`.

---

## Módulo `ui.tile_tab`

- **Entradas**
  - `PlanoParams` (dimensiones de piezas).
  - Entradas del usuario: límites de cama, márgenes, medianiles, pasos, volumen, tiros mínimos.
  - `NestingEngine` para calcular patrones.
- **Procesamiento**
  - Convierte inputs UI en llamadas a `calculate_optimal_nesting`.
  - Calcula bounding boxes (con y sin márgenes).
  - Verifica restricciones de cama mediante `_ensure_layout_within_limits`.
  - Genera mensajes ricos en HTML con resultados.
- **Salidas**
  - Actualiza labels de resultados (`planilla`, `medida_x`, `medida_y`, `tiros`).
  - Dibuja cama, márgenes y patrones en `TileScene`.
  - Emite mensajes informativos/errores al usuario.
  - Retorna diccionarios de layout (`tiles_x`, `tiles_y`, `ancho`, `alto`, `planilla_tipo`, etc.) para otros módulos.

---

## Módulo `ui.plano_tab`

- **Entradas**
  - Inputs de usuario relacionados con la geometría de la caja (longitudes, pestañas, offsets).
  - Parámetros actuales (`PlanoParams`).
- **Procesamiento**
  - Valida cada campo (longitudes positivas, tolerancias).
  - Empaqueta datos en nuevas instancias de `PlanoParams`.
- **Salidas**
  - Señales Qt para notificar cambios.
  - Nuevos `PlanoParams` enviados a `TileTab`/`MainWindow`.

---

## Módulo `ui.widgets`

- **Entradas**
  - Parámetros de escala (`PlanoParams.escala`).
  - Valores de márgenes y bounding box a resaltar.
- **Salidas**
  - `ZoomGraphicsView`: eventos de zoom/pan para la UI.
  - `TileScene`: dibuja cama, piezas, guías y maneja bounding boxes ajustados.

---

## Módulo `nesting.engine`

- **Entradas**
  - `PlanoParams`.
  - Parámetros de búsqueda (tiles_x/tiles_y, objetivos `"width"/"height"`, medianiles, pasos, clearance).
- **Procesamiento**
  - Usa `nesting.patterns` y `nesting.algorithms` para generar arreglos.
  - Administra `nesting.cache` para evitar cálculos repetidos.
  - Calcula bounding boxes y distribuciones finales.
- **Salidas**
  - Objetos `NestingResult` (coordenadas, ángulos, uso de material).
  - Actualizaciones en caches (por objetivo).
  - Bounding boxes crudos para validación posterior.

---

## Módulo `nesting.algorithms`

- **Entradas**: Piezas normalizadas, reglas de rotación, clearances.
- **Salidas**: Estrategias de posicionamiento (lineales, serpenteantes, etc.) usadas por `NestingEngine`.

## Módulo `nesting.cache`

- **Entradas**: Firmas inmutables del layout, resultados anteriores.
- **Salidas**: Patrones recuperados o almacenados para cada objetivo.

## Módulo `nesting.optimizer`

- **Entradas**: Objetivos de optimización, restricciones de producción.
- **Salidas**: Recomendaciones de `tiles_x`/`tiles_y` y orden de prueba.

## Módulo `nesting.patterns`

- **Entradas**: Parámetros de pieza y medianiles.
- **Salidas**: Plantillas geométricas listas para replicar sobre la cama.

---

## Módulo `models.parameters`

- **Entradas**
  - Datos de UI o fixtures (JSON, defaults).
- **Salidas**
  - Dataclass `PlanoParams` con validaciones mínimas.
  - Helpers para clonar/actualizar parámetros.

## Módulo `models.production`

- **Entradas**: Volumen objetivo, tiros mínimos, capacidades de máquina.
- **Salidas**: Estructuras con métricas de producción (planillas mín/máx, tiros requeridos).

---

## Módulo `geometry.*`

- `geometry.types`: define `Polyline`, `Polygon`, `BBox` y otras estructuras comunes.
- `geometry.transformations`: recibe puntos/polígonos y devuelve transformaciones (traslaciones, rotaciones).
- `geometry.collision`: toma dos polígonos/bboxes y devuelve booleanos/áreas de intersección.
- `geometry.polygons`: helpers para generar carcasas de cajas.
- `geometry.render_helpers`: recibe `TileScene` y datos geométricos y genera ítems Qt.
- `geometry.utils`: cálculos auxiliares (normalización, offsets).

En todos los casos:
- **Entradas**: listas de puntos, ángulos, escalas.
- **Salidas**: nuevos polígonos, bounding boxes o banderas de colisión que consume `NestingEngine`/`TileScene`.

---

## Módulo `utils`

- `logging_config`: recibe nivel de logging y ruta; configura `logging` estándar.
- `constants`: expone valores estándar (colores, tolerancias) para UI y geometría.
- `validators`: funciones que reciben números o arrays y lanzan `ValueError` si no cumplen los rangos.

---

## Módulo `tests`

- **Entradas**: API pública de cada módulo (funciones/classes).
- **Salidas**: Assertions que validan geometría, nesting y UI.

---

## Cómo extender el sistema

1. **Agregar un nuevo módulo**  
   - Documenta sus entradas/salidas en esta misma tabla.  
   - Define sus contratos en docstrings y, si aplica, agrega un test correspondiente.

2. **Modificar un módulo existente**  
   - Actualiza los contratos aquí descritos si cambian parámetros o resultados.  
   - Asegúrate de mantener sincronizadas las estructuras de datos compartidas (`PlanoParams`, layouts, caches, etc.).
### Contrato ejemplo `backend.service.layout_service`

Pedido:

```
{
  "params": { "L": 20.0, "A": 15.0, "h": 10.0 },
  "tiles_x": 2,
  "tiles_y": 2,
  "medianil_x": 0.5,
  "medianil_y": 0.5,
  "sangria_izquierda": 1.0,
  "sangria_derecha": 1.0,
  "pinza": 0.5,
  "contra_pinza": 0.5,
  "objective": "width"
}
```

Respuesta:

```
{
  "success": true,
  "layout": {
    "tiles_x": 2,
    "tiles_y": 2,
    "planilla": 4,
    "medida_x_cm": 43.0,
    "medida_y_cm": 22.0,
    "area_cm2": 946.0,
    "objective": "width"
  },
  "message": null
}
```
