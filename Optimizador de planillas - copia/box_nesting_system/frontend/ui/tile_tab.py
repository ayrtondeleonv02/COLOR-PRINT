"""

Tile (Cama Roland) tab implementation for nesting optimization and visualization.

"""



import math
import time

import logging

from typing import Tuple, Optional, Dict, Any



from PySide6.QtCore import Qt, QRectF, QEventLoop, QThread, Signal

from PySide6.QtGui import QColor, QTransform

from PySide6.QtWidgets import (

    QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QDoubleSpinBox,

    QPushButton, QLabel, QGroupBox, QSpinBox, QMessageBox, QApplication, QProgressDialog

)



from backend.models.parameters import PlanoParams

from backend.nesting.engine import NestingEngine


class NestingWorker(QThread):
    result_ready = Signal(dict)
    error = Signal(str)

    def __init__(self, params: PlanoParams, engine_args: Dict[str, Any]):
        super().__init__()
        self.params = params.copy()
        self.engine_args = engine_args

    def run(self) -> None:
        try:
            engine = NestingEngine(self.params)
            result = engine.calculate_optimal_nesting(**self.engine_args)
            objective = self.engine_args.get("objective", "width")
            cache = (
                engine.nesting_cache_width
                if objective == "width" else engine.nesting_cache_height
            )
            payload = {
                "nesting_result": result,
                "cache_entry": cache.pattern_data,
                "cache_key": cache.cache_key,
            }
            self.result_ready.emit(payload)
        except Exception as exc:
            self.error.emit(str(exc))

from .widgets import ZoomGraphicsView, TileScene





class TileTab(QWidget):

    """

    Nesting optimization tab for Roland cutting bed.

    """



    def __init__(self, params: PlanoParams):

        super().__init__()

        self.logger = logging.getLogger(__name__)
        self.params = params
        self.nesting_engine = NestingEngine(params)
        self._active_worker: NestingWorker | None = None
        self._worker_context: Dict[str, Any] = {}
        self._progress_dialog: QProgressDialog | None = None

        

        # Track current state for cache optimization

        self._current_state = {

            'medianil_x': 0.0,

            'medianil_y': 0.0,

            'tiles_x': 1,

            'tiles_y': 1,

            'paso_y': 0.5,

            'paso_x': 0.1,

            'clearance': 0.0,

            'objective': "width"

        }

        

        # Initialize UI components to None

        self.sb_xmax = None

        self.sb_ymax = None

        self.sb_xmin = None

        self.sb_ymin = None

        self.sb_sangria_izquierda = None

        self.sb_sangria_derecha = None

        self.sb_pinza = None

        self.sb_contra_pinza = None

        self.btn_update = None

        self.sb_paso_y = None

        self.sb_paso_x = None

        self.sb_clearance = None

        self.sb_medianil_x = None

        self.sb_medianil_y = None

        self.btn_nesting_w = None

        self.btn_nesting_h = None

        self.btn_optimizar_layout = None

        self.sb_tiles_x = None

        self.sb_tiles_y = None

        self.sb_volumen = None

        self.sb_tiros_minimos = None

        self.scene = None

        self.view = None

        self._cache_signatures = {"width": None, "height": None}

        

        self._setup_ui()

        self._connect_signals()

        self._view_fit_done = False

        self._last_bed_rect: QRectF | None = None

        self._last_bed_limits: Tuple[float, float, float, float] | None = None

        self._reset_resultados()

        

        # Initial render

        self.render()

        

        self.logger.info("TileTab initialized successfully")



    def _setup_ui(self) -> None:

        """Setup user interface components."""

        # Create main layout

        layout = QHBoxLayout(self)

        

        # Create control panels (left controls + right info)

        control_panel_left, control_panel_right = self._build_control_panels()

        layout.addWidget(control_panel_left, 0)

        

        # Create graphics scene and view

        self.scene = TileScene(self.params)

        self.view = ZoomGraphicsView(self.scene)

        self.view.setBackgroundBrush(QColor(255, 255, 255))

        self.view.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        layout.addWidget(self.view, 1)

        layout.addWidget(control_panel_right, 0)



    def _build_control_panels(self) -> Tuple[QWidget, QWidget]:

        """

        Build the control panels with nesting parameters and production settings.

        """

        left_panel = QWidget()

        left_panel.setMaximumWidth(450)

        left_column = QVBoxLayout(left_panel)

        

        right_panel = QWidget()

        right_panel.setMaximumWidth(260)

        right_column = QVBoxLayout(right_panel)

        

                # Roland bed limits group
        bed_group = QGroupBox("Limites de la cama Roland (cm)")
        bed_form = QFormLayout(bed_group)
        
        self.sb_xmax = self._create_spinbox(73.0, -10000.0, 10000.0, 1.0)
        self.sb_ymax = self._create_spinbox(103.0, -10000.0, 10000.0, 1.0)
        self.sb_xmin = self._create_spinbox(38.0, -10000.0, 10000.0, 1.0)
        self.sb_ymin = self._create_spinbox(48.0, -10000.0, 10000.0, 1.0)
        
        bed_form.addRow("Xmax:", self.sb_xmax)
        bed_form.addRow("Ymax:", self.sb_ymax)
        bed_form.addRow("Xmin:", self.sb_xmin)
        bed_form.addRow("Ymin:", self.sb_ymin)
        
        # Bed margins group
        margins_group = QGroupBox("Margenes de la cama (cm)")
        margins_form = QFormLayout(margins_group)
        
        self.sb_sangria_izquierda = self._create_spinbox(0.5, 0.0, 50.0, 0.1)
        self.sb_sangria_derecha = self._create_spinbox(0.5, 0.0, 50.0, 0.1)
        self.sb_pinza = self._create_spinbox(1.2, 0.0, 50.0, 0.1)
        self.sb_contra_pinza = self._create_spinbox(0.5, 0.0, 50.0, 0.1)
        
        margins_form.addRow("Sangria izquierda:", self.sb_sangria_izquierda)
        margins_form.addRow("Sangria derecha:", self.sb_sangria_derecha)
        margins_form.addRow("Pinza:", self.sb_pinza)
        margins_form.addRow("Contra Pinza:", self.sb_contra_pinza)

        self.btn_update = QPushButton("Actualizar Vista")

        # Search parameters group
        search_group = QGroupBox("Parametros de Busqueda")
        search_form = QFormLayout(search_group)
        
        self.sb_paso_y = self._create_spinbox(0.5, 0.1, 10.0, 0.1)
        self.sb_paso_x = self._create_spinbox(0.1, 0.05, 10.0, 0.05)
        self.sb_clearance = self._create_spinbox(0.0, 0.0, 10.0, 0.1)
        
        search_form.addRow("Paso Y (cm):", self.sb_paso_y)
        search_form.addRow("Paso X (cm):", self.sb_paso_x)
        search_form.addRow("Clearance (cm):", self.sb_clearance)

        # Medianil group
        medianil_group = QGroupBox("Medianil (Separacion entre tiles)")
        medianil_form = QFormLayout(medianil_group)
        
        self.sb_medianil_x = self._create_spinbox(0.0, 0.0, 1000.0, 0.1)
        self.sb_medianil_y = self._create_spinbox(0.0, 0.0, 1000.0, 0.1)
        
        medianil_form.addRow("Medianil X (cm):", self.sb_medianil_x)
        medianil_form.addRow("Medianil Y (cm):", self.sb_medianil_y)
        
        # Nesting optimization buttons
        self.btn_nesting_w = QPushButton("Nesting - minimizar ancho")
        self.btn_nesting_h = QPushButton("Nesting - minimizar alto")
        self.btn_optimizar_layout = QPushButton("Optimizar layout")

        # Tile count group
        tiles_group = QGroupBox("Cantidad de Tiles")
        tiles_form = QFormLayout(tiles_group)
        
        self.sb_tiles_x = self._create_spinbox(1.0, 1.0, 100.0, 1.0)
        self.sb_tiles_y = self._create_spinbox(1.0, 1.0, 100.0, 1.0)
        
        tiles_form.addRow("Tiles en X:", self.sb_tiles_x)
        tiles_form.addRow("Tiles en Y:", self.sb_tiles_y)
        
        # Production parameters group
        production_group = QGroupBox("Parametros de Produccion")
        production_form = QFormLayout(production_group)
        
        self.sb_volumen = QSpinBox()
        self.sb_volumen.setRange(0, 2_147_483_647)
        self.sb_volumen.setValue(0)
        self.sb_volumen.setSuffix(" piezas")
        
        self.sb_tiros_minimos = QSpinBox()
        self.sb_tiros_minimos.setRange(0, 2_147_483_647)  # practically unlimited within QSpinBox
        self.sb_tiros_minimos.setValue(0)
        self.sb_tiros_minimos.setSuffix(" tiros")
        
        production_form.addRow("Volumen (cantidad de piezas):", self.sb_volumen)
        production_form.addRow("Tiros minimos:", self.sb_tiros_minimos)
        
        resultados_group = QGroupBox("Resultados")
        resultados_form = QFormLayout(resultados_group)
        self.lbl_res_planilla = QLabel("-")
        self.lbl_res_x = QLabel("-")
        self.lbl_res_y = QLabel("-")
        self.lbl_res_tiros = QLabel("-")
        resultados_form.addRow("Planilla:", self.lbl_res_planilla)
        resultados_form.addRow("X (cm):", self.lbl_res_x)
        resultados_form.addRow("Y (cm):", self.lbl_res_y)
        resultados_form.addRow("Tiros:", self.lbl_res_tiros)
        
        # Add all groups to layout
        left_column.addWidget(bed_group)
        left_column.addWidget(margins_group)
        left_column.addWidget(self.btn_update)
        left_column.addWidget(search_group)
        left_column.addWidget(medianil_group)
        left_column.addWidget(self.btn_nesting_w)
        left_column.addWidget(self.btn_nesting_h)
        left_column.addWidget(self.btn_optimizar_layout)
        left_column.addStretch(1)

        right_column.addWidget(tiles_group)
        right_column.addWidget(production_group)
        right_column.addWidget(resultados_group)
        right_column.addStretch(1)
        
        return left_panel, right_panel


    def _create_spinbox(self, value: float, min_val: float, max_val: float, step: float) -> QDoubleSpinBox:

        """

        Create a standardized double spinbox.

        """

        spinbox = QDoubleSpinBox()

        spinbox.setDecimals(2)

        spinbox.setRange(min_val, max_val)

        spinbox.setSingleStep(step)

        spinbox.setValue(value)

        return spinbox



    def _connect_signals(self) -> None:

        """Connect signal handlers."""

        # Connect button clicks

        self.btn_update.clicked.connect(self.render)

        self.btn_nesting_w.clicked.connect(self.nesting_min_width)

        self.btn_nesting_h.clicked.connect(self.nesting_min_height)

        self.btn_optimizar_layout.clicked.connect(self.optimizar_layout)

        

        # Connect production parameter changes

        self.sb_volumen.valueChanged.connect(self._on_production_changed)

        self.sb_tiros_minimos.valueChanged.connect(self._on_production_changed)



        # Invalidate caches when spacing/search parameters change

        for sb in (self.sb_paso_y, self.sb_paso_x, self.sb_clearance,

                   self.sb_medianil_x, self.sb_medianil_y):

            sb.valueChanged.connect(self._on_spacing_params_changed)



    def _on_production_changed(self) -> None:

        """Handle production parameter changes."""

        # Update any dependent calculations

        pass



    def _on_spacing_params_changed(self) -> None:

        """Clear caches when spacing/search parameters change."""

        self.clear_nesting_cache()



    def _read_bed_limits(self) -> Tuple[float, float, float, float]:
        """
        Read and validate user-defined bed dimension constraints (cm).
        Margins are handled separately when evaluating layouts so these
        values always represent the total allowable dimensions.
        """
        x_min = self.sb_xmin.value()
        x_max = self.sb_xmax.value()
        y_min = self.sb_ymin.value()
        y_max = self.sb_ymax.value()

        if x_max <= x_min:
            raise ValueError("El valor de X max debe ser mayor que X min.")
        if y_max <= y_min:
            raise ValueError("El valor de Y max debe ser mayor que Y min.")

        return x_min, x_max, y_min, y_max



    def render(self, force_recalculate: bool = False) -> None:

        """

        Render the nesting pattern with current parameters.

        """

        try:

            # Read current parameters
            self._yield_ui_events()

            x_min, x_max, y_min, y_max = self._read_bed_limits()

            self._update_bed_limits(x_min, x_max, y_min, y_max)

            tiles_x = int(self.sb_tiles_x.value())

            tiles_y = int(self.sb_tiles_y.value())

            medianil_x = self.sb_medianil_x.value()

            medianil_y = self.sb_medianil_y.value()

            paso_y = self.sb_paso_y.value()

            paso_x = self.sb_paso_x.value()

            clearance = self.sb_clearance.value()

            self._update_scene_margins()

            signature = self._build_cache_signature(medianil_x, medianil_y, paso_y, paso_x, clearance)

            if force_recalculate or self._cache_signatures.get("width") != signature:
                self.logger.info(
                    "Render(width): regenerando cache base 3x2 antes de dibujar (firma %s).",
                    signature
                )
                self._generate_cache_for_objective("width", 3, 2, medianil_x, medianil_y)
            if force_recalculate or self._cache_signatures.get("height") != signature:
                self.logger.info(
                    "Render(height): regenerando cache base 3x2 (firma %s) para preparación de layouts.",
                    signature
                )
                self._generate_cache_for_objective("height", 3, 2, medianil_x, medianil_y)

            cache_obj = self.nesting_engine.nesting_cache_width

            can_use_cache = (

                not force_recalculate and

                cache_obj.pattern_data is not None and

                self._cache_signatures.get("width") == signature

            )

            self.logger.debug(
                "Render(width) cache check: signature=%s cached=%s pattern=%s force=%s -> use_cache=%s",
                signature,
                self._cache_signatures.get("width"),
                cache_obj.pattern_data is not None,
                force_recalculate,
                can_use_cache
            )

            

            # Use nesting engine for calculations
            if can_use_cache and cache_obj.pattern_data is not None:
                self.logger.info("Render(width): utilizando patrón cacheado para dibujar %dx%d tiles.", tiles_x, tiles_y)
                nesting_result = dict(cache_obj.pattern_data)
                nesting_result.setdefault('dx2', cache_obj.pattern_data.get('dx2', 0.0))
                nesting_result.setdefault('dy2', cache_obj.pattern_data.get('dy2', 0.0))
                nesting_result.setdefault('dx3', cache_obj.pattern_data.get('dx3', 0.0))
                nesting_result.setdefault('dy3', cache_obj.pattern_data.get('dy3', 0.0))
                nesting_result.setdefault('rot1', cache_obj.pattern_data.get('rot1', 0))
                nesting_result.setdefault('rot2', cache_obj.pattern_data.get('rot2', 0))
            else:
                self._yield_ui_events()
                nesting_result = self.nesting_engine.calculate_optimal_nesting(
                    tiles_x=tiles_x,
                    tiles_y=tiles_y,
                    paso_y=paso_y,
                    paso_x=paso_x,
                    clearance_cm=clearance,
                    medianil_x=medianil_x,
                    medianil_y=medianil_y,
                    objective="width",
                    force_recalculate=not can_use_cache or force_recalculate
                )

            

            self._yield_ui_events()

            if nesting_result:

                # Clear and draw bed

                self.scene.clear_scene()

                bed_rect = self.scene.draw_bed(x_min, x_max, y_min, y_max)

                

                # Draw tiling pattern

                self.scene.draw_tiling_pattern(nesting_result, tiles_x, tiles_y, medianil_x, medianil_y)
                self._yield_ui_events()

                

                # Update current state

                self._update_current_state(

                    medianil_x, medianil_y, tiles_x, tiles_y, paso_y, paso_x, clearance, "width"

                )

                self._cache_signatures["width"] = signature

                

                # Update view

                self._fit_layout_to_view(bed_rect)

                

                self.logger.debug("Nesting rendered successfully")

            else:

                # Draw simple tile as fallback

                self.scene.clear_scene()

                bed_rect = self.scene.draw_bed(x_min, x_max, y_min, y_max)

                self.scene.draw_simple_tile()

                self._fit_layout_to_view(bed_rect)

                self.logger.warning("No nesting result available, using simple tile")

            

        except ValueError as limit_error:

            QMessageBox.warning(self, "Nesting", str(limit_error))

        except Exception as e:

            self.logger.error("Error rendering nesting: %s", e, exc_info=True)

            QMessageBox.critical(self, "Error al renderizar", str(e))



    def _update_current_state(self, medianil_x: float, medianil_y: float,

                            tiles_x: int, tiles_y: int, paso_y: float,

                            paso_x: float, clearance: float, objective: str) -> None:

        """

        Update current state tracking.

        """

        self._current_state.update({

            'medianil_x': medianil_x,

            'medianil_y': medianil_y,

            'tiles_x': tiles_x,

            'tiles_y': tiles_y,

            'paso_y': paso_y,

            'paso_x': paso_x,

            'clearance': clearance,

            'objective': objective

        })



    def nesting_min_width(self) -> None:

        """Run nesting optimization to minimize width."""

        self._run_nesting_optimization("width")



    def nesting_min_height(self) -> None:

        """Run nesting optimization to minimize height."""

        self._run_nesting_optimization("height")



    def _run_nesting_optimization(self, objective: str) -> None:
        """Run nesting optimization with specified objective."""
        try:
            x_min, x_max, y_min, y_max = self._read_bed_limits()
            self._update_bed_limits(x_min, x_max, y_min, y_max)
            tiles_x = int(self.sb_tiles_x.value())
            tiles_y = int(self.sb_tiles_y.value())
            paso_y = self.sb_paso_y.value()
            paso_x = self.sb_paso_x.value()
            clearance = self.sb_clearance.value()
            medianil_x = self.sb_medianil_x.value()
            medianil_y = self.sb_medianil_y.value()
            self._update_scene_margins()
            self._yield_ui_events()

            signature = self._build_cache_signature(medianil_x, medianil_y, paso_y, paso_x, clearance)
            cache_obj = (
                self.nesting_engine.nesting_cache_width
                if objective == "width" else self.nesting_engine.nesting_cache_height
            )
            can_use_cache = (
                cache_obj.pattern_data is not None and
                self._cache_signatures.get(objective) == signature
            )

            self.logger.debug(
                "Run nesting (%s): signature=%s cached=%s pattern=%s -> use_cache=%s",
                objective,
                signature,
                self._cache_signatures.get(objective),
                cache_obj.pattern_data is not None,
                can_use_cache
            )
            if can_use_cache:
                self.logger.info("Nesting (%s): cache detectado (firma %s). Se reutilizará el patrón almacenado.", objective, signature)
            else:
                self.logger.info("Nesting (%s): cache no disponible (firma %s). Se recalculará el patrón.", objective, signature)

            engine_args = {
                "tiles_x": tiles_x,
                "tiles_y": tiles_y,
                "paso_y": paso_y,
                "paso_x": paso_x,
                "clearance_cm": clearance,
                "medianil_x": medianil_x,
                "medianil_y": medianil_y,
                "objective": objective,
                "force_recalculate": not can_use_cache,
            }
            context = {
                "engine_args": engine_args,
                "signature": signature,
                "x_limits": (x_min, x_max),
                "y_limits": (y_min, y_max),
            }

            if can_use_cache and cache_obj.pattern_data is not None and cache_obj.cache_key is not None:
                self.logger.debug("Nesting (%s): usando patrón cacheado directamente, sin worker.", objective)
                context["start_time"] = time.perf_counter()
                self._worker_context = context
                payload = {
                    "nesting_result": cache_obj.pattern_data,
                    "cache_entry": cache_obj.pattern_data,
                    "cache_key": cache_obj.cache_key,
                }
                self._on_nesting_worker_success(payload)
                self._worker_context = {}
                return

            self._start_nesting_worker(engine_args, context, f"Calculando nesting ({objective})...", show_progress=False)
            return

        except Exception as e:
            self.logger.error("Error in nesting optimization: %s", e, exc_info=True)
            QMessageBox.critical(self, "Error en Nesting", str(e))
    def optimizar_layout(self) -> None:

        """
        Run comprehensive layout optimization considering production parameters.
        """

        try:
            volumen = self.sb_volumen.value()
            tiros_minimos = self.sb_tiros_minimos.value()

            if volumen == 0:
                mensaje = self._format_alert_message([
                    "Por favor ingrese un volumen de produccion mayor a 0."
                ])
                QMessageBox.warning(self, "Optimizacion", mensaje)
                return

            x_min_roland, x_max_roland, y_min_roland, y_max_roland = self._read_bed_limits()
            medianil_x = self.sb_medianil_x.value()
            medianil_y = self.sb_medianil_y.value()
            self._yield_ui_events()

            self.logger.info("Generating cache for both nesting objectives...")
            self._yield_ui_events()

            self._generate_cache_for_objective("width", 3, 2, medianil_x, medianil_y)
            self._yield_ui_events()

            self._generate_cache_for_objective("height", 3, 2, medianil_x, medianil_y)
            self._yield_ui_events()

            self.logger.info("Calculating optimal layout for width minimization...")
            layout_width = self._calculate_layout_for_objective(
                "width", x_min_roland, x_max_roland, y_min_roland, y_max_roland,
                medianil_x, medianil_y, volumen, tiros_minimos
            )
            self._yield_ui_events()

            self.logger.info("Calculating optimal layout for height minimization...")
            layout_height = self._calculate_layout_for_objective(
                "height", x_min_roland, x_max_roland, y_min_roland, y_max_roland,
                medianil_x, medianil_y, volumen, tiros_minimos
            )
            self._yield_ui_events()

            layout_optimo = self._compare_layouts(layout_width, layout_height)
            self._yield_ui_events()

            if not layout_optimo:
                mensaje = self._format_alert_message([
                    "No se pudo encontrar un layout valido para ninguno de los objetivos.",
                    "Pruebe ajustando los parametros de produccion o los limites de la cama."
                ])
                QMessageBox.warning(self, "Optimizacion", mensaje)
                return

            self._apply_optimal_layout(
                layout_optimo, layout_width, layout_height,
                volumen, tiros_minimos, medianil_x, medianil_y
            )

            self.logger.info("Layout optimization completed successfully")

        except Exception as e:
            self.logger.error("Error in layout optimization: %s", e, exc_info=True)
            mensaje = self._format_alert_message([
                "Error al optimizar el layout.",
                f"<b>Detalle:</b> {str(e)}"
            ])
            QMessageBox.critical(self, "Error en Optimizacion", mensaje)


    def _generate_cache_for_objective(self, objective: str, tiles_x_base: int, 

                                    tiles_y_base: int, medianil_x: float, medianil_y: float) -> None:

        """

        Generate cache for specific nesting objective.

        """

        try:

            paso_y = self.sb_paso_y.value()

            paso_x = self.sb_paso_x.value()

            clearance = self.sb_clearance.value()

            signature = self._build_cache_signature(medianil_x, medianil_y, paso_y, paso_x, clearance)

            cache_obj = (self.nesting_engine.nesting_cache_width 

                         if objective == "width" else self.nesting_engine.nesting_cache_height)

            

            cache_is_current = cache_obj.pattern_data is not None and self._cache_signatures.get(objective) == signature

            if cache_is_current:

                self.logger.debug(

                    "Skipping cache generation for %s (geometría, medianil y parámetros sin cambios).",

                    objective

                )
                self.logger.info("Optimizar planilla: cache detectado para objetivo %s (firma %s); se reutiliza plantilla 3x2.", objective, signature)

                return

            

            # Use nesting engine to generate cache

            self._yield_ui_events()
            result = self.nesting_engine.calculate_optimal_nesting(

                tiles_x=tiles_x_base,

                tiles_y=tiles_y_base,

                paso_y=paso_y,

                paso_x=paso_x,

                clearance_cm=clearance,

                medianil_x=medianil_x,

                medianil_y=medianil_y,

                objective=objective,

                force_recalculate=True

            )

            self._yield_ui_events()

            if result:

                self._cache_signatures[objective] = signature
                self.logger.info("Optimizar planilla: cache regenerado para objetivo %s (firma %s).", objective, signature)

            

        except Exception as e:

            self.logger.error("Error generating cache for %s: %s", objective, e)



    def _calculate_layout_for_objective(self, objective: str, x_min_roland: float,

                                      x_max_roland: float, y_min_roland: float,

                                      y_max_roland: float, medianil_x: float,

                                      medianil_y: float, volumen: int, 

                                      tiros_minimos: int) -> Optional[dict]:

        """

        Calculate optimal layout for specific objective.

        """

        try:

            # Calculate layout bounds

            layout_bounds = self._calculate_layout_bounds(

                objective, x_min_roland, x_max_roland, y_min_roland, y_max_roland,

                medianil_x, medianil_y

            )

            

            if not layout_bounds:

                return None

                

            tiles_x_min, tiles_y_min, tiles_x_max, tiles_y_max = layout_bounds

            

            # Calculate production metrics

            production_metrics = self._calculate_production_metrics(

                tiles_x_min, tiles_y_min, tiles_x_max, tiles_y_max, volumen, tiros_minimos

            )

            

            # Find optimal layout

            return self._find_optimal_layout(

                objective, production_metrics, medianil_x, medianil_y

            )

            

        except Exception as e:

            self.logger.error("Error calculating layout for %s: %s", objective, e)

            return None



    def _calculate_layout_bounds(self, objective: str, x_min_roland: float,

                               x_max_roland: float, y_min_roland: float,

                               y_max_roland: float, medianil_x: float,

                               medianil_y: float) -> Optional[tuple]:

        """

        Calculate layout bounds that fit within Roland bed.

        """

        try:

            # Find minimum tiles_x using nesting engine

            tiles_x_min = 1
            while True:
                self._yield_ui_events()
                bbox = self.nesting_engine.calculate_global_bbox(tiles_x_min, 1, medianil_x, medianil_y, objective)
                ancho_raw = bbox[2] - bbox[0]
                alto_raw = bbox[3] - bbox[1]
                ancho_total, _ = self._apply_margins_to_dims(ancho_raw, alto_raw)
                if ancho_total >= x_min_roland:
                    break
                tiles_x_min += 1
                if tiles_x_min > 100:
                    return None



            # Find minimum tiles_y

            tiles_y_min = 1
            while True:
                self._yield_ui_events()
                bbox = self.nesting_engine.calculate_global_bbox(tiles_x_min, tiles_y_min, medianil_x, medianil_y, objective)
                ancho_raw = bbox[2] - bbox[0]
                alto_raw = bbox[3] - bbox[1]
                _, alto_total = self._apply_margins_to_dims(ancho_raw, alto_raw)
                if alto_total >= y_min_roland:
                    break
                tiles_y_min += 1
                if tiles_y_min > 100:
                    return None



            # Find maximum tiles_x

            tiles_x_max = tiles_x_min
            while True:
                self._yield_ui_events()
                bbox = self.nesting_engine.calculate_global_bbox(tiles_x_max + 1, 1, medianil_x, medianil_y, objective)
                ancho_raw = bbox[2] - bbox[0]
                alto_raw = bbox[3] - bbox[1]
                ancho_total, _ = self._apply_margins_to_dims(ancho_raw, alto_raw)
                if ancho_total > x_max_roland:
                    break
                tiles_x_max += 1
                if tiles_x_max > 100:
                    break



            # Find maximum tiles_y

            tiles_y_max = tiles_y_min
            while True:
                self._yield_ui_events()
                bbox = self.nesting_engine.calculate_global_bbox(tiles_x_max, tiles_y_max + 1, medianil_x, medianil_y, objective)
                ancho_raw = bbox[2] - bbox[0]
                alto_raw = bbox[3] - bbox[1]
                _, alto_total = self._apply_margins_to_dims(ancho_raw, alto_raw)
                if alto_total > y_max_roland:
                    break
                tiles_y_max += 1
                if tiles_y_max > 100:
                    break



            return (tiles_x_min, tiles_y_min, tiles_x_max, tiles_y_max)

            

        except Exception as e:

            self.logger.error("Error calculating layout bounds: %s", e)

            return None



    def _calculate_production_metrics(self, tiles_x_min: int, tiles_y_min: int,

                                    tiles_x_max: int, tiles_y_max: int,

                                    volumen: int, tiros_minimos: int) -> dict:

        """Calculate production metrics for layout bounds."""

        planos_min = tiles_x_min * tiles_y_min

        planos_max = tiles_x_max * tiles_y_max

        

        tiros_con_min = max(1, math.ceil(volumen / planos_min)) if planos_min > 0 else 0

        tiros_con_max = max(1, math.ceil(volumen / planos_max)) if planos_max > 0 else 0

        

        return {

            'tiles_x_min': tiles_x_min,

            'tiles_y_min': tiles_y_min,

            'tiles_x_max': tiles_x_max,

            'tiles_y_max': tiles_y_max,

            'planos_min': planos_min,

            'planos_max': planos_max,

            'tiros_con_min': tiros_con_min,

            'tiros_con_max': tiros_con_max,

            'volumen': volumen,

            'tiros_minimos': tiros_minimos

        }



    def _find_optimal_layout(self, objective: str, metrics: dict,
                           medianil_x: float, medianil_y: float) -> Optional[dict]:
        """Find optimal layout based on production metrics."""

        tiles_x_min = metrics['tiles_x_min']
        tiles_y_min = metrics['tiles_y_min']
        tiles_x_max = metrics['tiles_x_max']
        tiles_y_max = metrics['tiles_y_max']
        tiros_con_min = metrics['tiros_con_min']
        tiros_con_max = metrics['tiros_con_max']
        tiros_minimos = metrics['tiros_minimos']
        volumen = metrics['volumen']

        layout_optimo = None
        razon_decision = ""
        tipo_planilla = "intermedia"

        # Strategy selection
        if tiros_con_min <= tiros_minimos:
            layout_optimo = (tiles_x_min, tiles_y_min)
            razon_decision = f"Layout MÍNIMO - {tiros_con_min} tiros ≤ {tiros_minimos} tiros minimos"
            tipo_planilla = "minima"
        elif tiros_con_max >= tiros_minimos:
            layout_optimo = (tiles_x_max, tiles_y_max)
            razon_decision = f"Layout MÁXIMO - {tiros_con_max} tiros ≥ {tiros_minimos} tiros minimos"
            tipo_planilla = "maxima"
        else:
            total_tiles_necesario = math.ceil(volumen / tiros_minimos)
            layout_optimo = self._find_intermediate_layout(
                tiles_x_min, tiles_y_min, tiles_x_max, tiles_y_max,
                total_tiles_necesario, medianil_x, medianil_y, objective
            )
            razon_decision = f"Layout INTERMEDIO - {total_tiles_necesario} tiles necesarios"
            tipo_planilla = "intermedia"

        if layout_optimo:
            tiles_x, tiles_y = layout_optimo
            return self._create_layout_result(
                tiles_x, tiles_y, medianil_x, medianil_y, objective,
                tipo_planilla, razon_decision, volumen, tiros_minimos
            )

        return None

    def _find_intermediate_layout(self, tiles_x_min: int, tiles_y_min: int,

                                tiles_x_max: int, tiles_y_max: int,

                                total_tiles_necesario: int, medianil_x: float,

                                medianil_y: float, objective: str) -> Optional[tuple]:

        """Find intermediate layout matching required tile count."""

        factores_posibles = []

        

        for tx in range(tiles_x_min, tiles_x_max + 1):

            for ty in range(tiles_y_min, tiles_y_max + 1):

                self._yield_ui_events()

                if tx * ty == total_tiles_necesario:

                    bbox = self.nesting_engine.calculate_global_bbox(tx, ty, medianil_x, medianil_y, objective)

                    ancho = bbox[2] - bbox[0]

                    alto = bbox[3] - bbox[1]

                    ancho_total, alto_total = self._apply_margins_to_dims(ancho, alto)
                    try:
                        self._ensure_layout_within_limits(ancho_total, alto_total)
                    except ValueError:
                        continue
                    area_total = ancho_total * alto_total
                    factores_posibles.append((tx, ty, area_total, ancho_total, alto_total))

        

        if factores_posibles:

            mejor_factor = min(factores_posibles, key=lambda x: x[2])

            return (mejor_factor[0], mejor_factor[1])

        

        return (tiles_x_max, tiles_y_max)



    def _create_layout_result(self, tiles_x: int, tiles_y: int,
                            medianil_x: float, medianil_y: float,
                            objective: str, tipo_planilla: str, razon: str,
                            volumen: int, tiros_minimos: int) -> dict:
        """Create layout result dictionary with layout metadata."""

        bbox = self.nesting_engine.calculate_global_bbox(tiles_x, tiles_y, medianil_x, medianil_y, objective)
        ancho_raw = bbox[2] - bbox[0]
        alto_raw = bbox[3] - bbox[1]
        ancho, alto = self._apply_margins_to_dims(ancho_raw, alto_raw)
        self._ensure_layout_within_limits(ancho, alto)

        area = ancho * alto
        total_tiles = tiles_x * tiles_y
        tiros_necesarios = max(1, math.ceil(volumen / total_tiles))

        return {
            'tiles_x': tiles_x,
            'tiles_y': tiles_y,
            'total_tiles': total_tiles,
            'width_raw': ancho_raw,
            'height_raw': alto_raw,
            'ancho': ancho,
            'alto': alto,
            'area': area,
            'objective': objective,
            'planilla_tipo': tipo_planilla,
            'razon': razon,
            'tiros_necesarios': tiros_necesarios
        }



    def _compare_layouts(self, layout_width: Optional[dict], 

                        layout_height: Optional[dict]) -> Optional[dict]:

        """Compare two layouts and select the best one."""

        if not layout_width and not layout_height:

            return None

        elif not layout_width:

            return layout_height

        elif not layout_height:

            return layout_width

        

        # Primary criterion: more total tiles

        if layout_width['total_tiles'] > layout_height['total_tiles']:

            return layout_width

        elif layout_height['total_tiles'] > layout_width['total_tiles']:

            return layout_height

        else:

            # Tie-breaker: smaller area

            if layout_width['area'] < layout_height['area']:

                return layout_width

            else:

                return layout_height



    def _apply_optimal_layout(self, layout_optimo: dict, layout_width: Optional[dict],

                            layout_height: Optional[dict], volumen: int,

                            tiros_minimos: int, medianil_x: float, medianil_y: float) -> None:

        """Apply optimal layout and show results."""

        # Apply optimal values

        tiles_x_optimo = layout_optimo['tiles_x']

        tiles_y_optimo = layout_optimo['tiles_y']

        objetivo_optimo = layout_optimo['objective']

        

        self.sb_tiles_x.setValue(tiles_x_optimo)

        self.sb_tiles_y.setValue(tiles_y_optimo)

        

        # Render with optimal layout using nesting engine

        nesting_result = self.nesting_engine.calculate_optimal_nesting(

            tiles_x=tiles_x_optimo,

            tiles_y=tiles_y_optimo,

            paso_y=self.sb_paso_y.value(),

            paso_x=self.sb_paso_x.value(),

            clearance_cm=self.sb_clearance.value(),

            medianil_x=medianil_x,

            medianil_y=medianil_y,

            objective=objetivo_optimo,

            force_recalculate=False

        )

        

        if nesting_result:
            # Clear and draw
            x_min, x_max, y_min, y_max = self._read_bed_limits()
            self._update_bed_limits(x_min, x_max, y_min, y_max)
            self._update_scene_margins()
            self.scene.clear_scene()
            bed_rect = self.scene.draw_bed(x_min, x_max, y_min, y_max)
            self.scene.draw_tiling_pattern(nesting_result, tiles_x_optimo, tiles_y_optimo, medianil_x, medianil_y)
            self._fit_layout_to_view(bed_rect)
        
        medida_x_total = layout_optimo['ancho']
        medida_y_total = layout_optimo['alto']
        tiros_req = layout_optimo.get('tiros_necesarios', self._compute_tiros(layout_optimo['total_tiles']))
        self._update_resultados(
            layout_optimo['total_tiles'], medida_x_total, medida_y_total, tiros_req
        )

        # Prepare and show results message
        mensaje = self._prepare_optimization_message(layout_optimo, layout_width, layout_height, volumen, tiros_minimos)
        QMessageBox.information(self, "OptimizaciÁÂ³n de Layout - Resultado", mensaje)



    def _prepare_optimization_message(self, layout_optimo: dict, layout_width: Optional[dict],
                                     layout_height: Optional[dict], volumen: int, tiros_minimos: int) -> str:
        """Prepare a compact, well spaced rich-text summary of the optimization results."""

        sections: list[str] = []

        if layout_width:
            sections.append(self._format_message_section(
                "Resultado para minimizar ancho",
                [
                    ("Tipo de encastre:", "minimizar ancho"),
                    ("Cantidad de tiles en X:", layout_width['tiles_x']),
                    ("Cantidad de tiles en Y:", layout_width['tiles_y']),
                    ("Planilla:", layout_width['total_tiles']),
                    ("Medida en X de la planilla:", f"{layout_width['ancho']:.2f} cm"),
                    ("Medida en Y de la planilla:", f"{layout_width['alto']:.2f} cm"),
                    ("Área de la planilla:", f"{layout_width['area']:.2f} cm<sup>2</sup>"),
                ]
            ))

        if layout_height:
            sections.append(self._format_message_section(
                "Resultado para minimizar alto",
                [
                    ("Tipo de encastre:", "minimizar alto"),
                    ("Cantidad de tiles en X:", layout_height['tiles_x']),
                    ("Cantidad de tiles en Y:", layout_height['tiles_y']),
                    ("Planilla:", layout_height['total_tiles']),
                    ("Medida en X de la planilla:", f"{layout_height['ancho']:.2f} cm"),
                    ("Medida en Y de la planilla:", f"{layout_height['alto']:.2f} cm"),
                    ("Área de la planilla:", f"{layout_height['area']:.2f} cm<sup>2</sup>"),
                ]
            ))

        tipo_planilla_flag = layout_optimo.get('planilla_tipo', '').lower()
        if tipo_planilla_flag == "minima":
            tipo_planilla_str = "Planilla minima"
        elif tipo_planilla_flag == "maxima":
            tipo_planilla_str = "Planilla maxima"
        elif tipo_planilla_flag == "intermedia":
            tipo_planilla_str = "Planilla intermedia"
        else:
            tipo_planilla = layout_optimo.get('razon', '').split(' - ')[0]
            tipo_planilla_upper = tipo_planilla.upper()
            if "MINIMO" in tipo_planilla_upper or "MÍNIMO" in tipo_planilla:
                tipo_planilla_str = "Planilla minima"
            elif "MAXIMO" in tipo_planilla_upper or "MÁXIMO" in tipo_planilla:
                tipo_planilla_str = "Planilla maxima"
            else:
                tipo_planilla_str = "Planilla intermedia"

        tipo_encastre_elegido = "minimizar ancho" if layout_optimo['objective'] == "width" else "minimizar alto"
        tiros_necesarios = layout_optimo.get(
            'tiros_necesarios',
            self._compute_tiros(layout_optimo['total_tiles'])
        )

        resumen = (
            "<div style='border-top:1px solid #d6d6d6;margin-top:6px;padding-top:8px;'>"
            f"<div><span style='color:#5a5a5a;'>Tipo de encastre elegido:</span> <b>{tipo_encastre_elegido}</b></div>"
            f"<div>{tipo_planilla_str}</div>"
            f"<div>Volumen: {volumen} piezas</div>"
            f"<div>Tiros minimos: {tiros_minimos}</div>"
            f"<div>Tiros necesarios: {tiros_necesarios}</div>"
            "</div>"
        )

        return self._wrap_message_html("".join(sections) + resumen)

    def _fit_layout_to_view(self, bed_rect: QRectF | None) -> None:

        """Adjust the graphics view so the entire layout is visible once per bed change."""

        if bed_rect is None or bed_rect.isNull():

            return

        if self._view_fit_done and self._last_bed_rect and self._last_bed_rect == bed_rect:

            return

        scene_height = bed_rect.height()

        if scene_height <= 0:

            return

        viewport_height = max(1, self.view.viewport().height())

        scale = viewport_height / scene_height

        transform = QTransform()

        transform.scale(scale, scale)

        self.view.setTransform(transform)

        # Align to top-left of scene

        self.view.horizontalScrollBar().setValue(self.view.horizontalScrollBar().minimum())

        self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().minimum())

        self.view.reset_drag_zoom_limits()

        self._view_fit_done = True

        self._last_bed_rect = QRectF(bed_rect)



    def get_volumen(self) -> int:

        """Get current production volume."""

        return self.sb_volumen.value()



    def get_tiros_minimos(self) -> int:

        """Get current minimum shots."""

        return self.sb_tiros_minimos.value()



    def clear_nesting_cache(self) -> None:

        """Clear cached nesting patterns so next render recomputes placements."""

        self.nesting_engine.nesting_cache_width.clear()

        self.nesting_engine.nesting_cache_height.clear()

        self._cache_signatures = {"width": None, "height": None}

        self.logger.debug("Nesting caches cleared")



    def update_params(self, new_params: PlanoParams) -> None:

        """Update box parameters and invalidate derived data."""

        self.params = new_params

        self.nesting_engine.params = self.params

        self.scene.params = self.params

        self.clear_nesting_cache()

        self._view_fit_done = False

        self.logger.info("TileTab parameters updated")



    def _build_cache_signature(self, medianil_x: float, medianil_y: float,

                               paso_y: float, paso_x: float, clearance: float) -> tuple:

        """Compose an immutable signature representing geometry + spacing + search params."""

        p = self.params

        return (

            p.L, p.A, p.h, p.cIzq, p.cDer,

            tuple(p.Tapas),

            tuple(p.CSup),

            tuple(p.Bases),

            tuple(p.CInf),

            medianil_x, medianil_y, paso_y, paso_x, clearance

        )



    def _update_scene_margins(self) -> None:

        """Send current margin values (cm) to the scene so it can draw bbox including them."""

        self.scene.set_margins(

            self.sb_sangria_izquierda.value(),

            self.sb_sangria_derecha.value(),

            self.sb_pinza.value(),

            self.sb_contra_pinza.value()

        )



    def _update_bed_limits(self, x_min: float, x_max: float, y_min: float, y_max: float) -> None:

        """Track bed limits to know when the view needs to be refit."""

        limits = (x_min, x_max, y_min, y_max)

        if self._last_bed_limits != limits:

            self._view_fit_done = False

            self._last_bed_limits = limits



    def _reset_resultados(self) -> None:

        self.lbl_res_planilla.setText("-")

        self.lbl_res_x.setText("-")

        self.lbl_res_y.setText("-")

        self.lbl_res_tiros.setText("-")



    def _apply_margins_to_dims(self, medida_x: float, medida_y: float) -> Tuple[float, float]:

        medida_x += self.sb_sangria_izquierda.value() + self.sb_sangria_derecha.value()

        medida_y += self.sb_pinza.value() + self.sb_contra_pinza.value()

        return medida_x, medida_y



    def _on_nesting_worker_success(self, payload: Dict[str, Any]) -> None:
        ctx = self._worker_context or {}
        engine_args = ctx.get("engine_args", {})
        objective = engine_args.get("objective", "width")
        nesting_result = payload.get("nesting_result")
        if not nesting_result:
            QMessageBox.warning(self, "Nesting", "No se pudo encontrar una solución de nesting óptima.")
            return

        cache_entry = payload.get("cache_entry")
        cache_key = payload.get("cache_key")
        if cache_entry and cache_key:
            target_cache = (
                self.nesting_engine.nesting_cache_width
                if objective == "width" else self.nesting_engine.nesting_cache_height
            )
            target_cache.store(cache_entry, cache_key)

        x_min, x_max = ctx.get("x_limits", (None, None))
        y_min, y_max = ctx.get("y_limits", (None, None))
        if None in (x_min, x_max, y_min, y_max):
            x_min, x_max, y_min, y_max = self._read_bed_limits()

        tiles_x = engine_args.get("tiles_x", 1)
        tiles_y = engine_args.get("tiles_y", 1)
        medianil_x = engine_args.get("medianil_x", 0.0)
        medianil_y = engine_args.get("medianil_y", 0.0)
        paso_y = engine_args.get("paso_y", 0.0)
        paso_x = engine_args.get("paso_x", 0.0)
        clearance = engine_args.get("clearance_cm", 0.0)

        self.scene.clear_scene()
        bed_rect = self.scene.draw_bed(x_min, x_max, y_min, y_max)
        self.scene.draw_tiling_pattern(nesting_result, tiles_x, tiles_y, medianil_x, medianil_y)
        self._yield_ui_events()

        bbox = self.nesting_engine.calculate_global_bbox(tiles_x, tiles_y, medianil_x, medianil_y, objective)
        if not bbox:
            QMessageBox.warning(self, "Nesting", "No se pudo calcular el bounding box del resultado.")
            return

        medida_x_raw = bbox[2] - bbox[0]
        medida_y_raw = bbox[3] - bbox[1]
        medida_x_total, medida_y_total = self._apply_margins_to_dims(medida_x_raw, medida_y_raw)
        self._ensure_layout_within_limits(medida_x_total, medida_y_total, x_min, x_max, y_min, y_max)
        area_total = medida_x_total * medida_y_total
        planilla = max(1, tiles_x * tiles_y)

        section_title = (
            "Resultado para minimizar ancho" if objective == "width" else "Resultado para minimizar alto"
        )
        tipo_encastre = "minimizar ancho" if objective == "width" else "minimizar alto"
        rows = [
            ("Tipo de encastre:", tipo_encastre),
            ("Cantidad de tiles en X:", tiles_x),
            ("Cantidad de tiles en Y:", tiles_y),
            ("Planilla:", planilla),
            ("Medida en X de la planilla:", f"{medida_x_total:.2f} cm"),
            ("Medida en Y de la planilla:", f"{medida_y_total:.2f} cm"),
            ("Área de la planilla:", f"{area_total:.2f} cm<sup>2</sup>"),
        ]
        mensaje = self._wrap_message_html(self._format_message_section(section_title, rows))
        QMessageBox.information(self, "Nesting Completado", mensaje)

        self._update_current_state(medianil_x, medianil_y, tiles_x, tiles_y, paso_y, paso_x, clearance, objective)
        self._fit_layout_to_view(bed_rect)
        self._yield_ui_events()
        tiros_req = self._compute_tiros(planilla)
        self._update_resultados(planilla, medida_x_total, medida_y_total, tiros_req)
        self.logger.info("Nesting optimization completed for objective: %s", objective)

    def _on_nesting_worker_error(self, message: str) -> None:
        QMessageBox.critical(self, "Nesting", message)

    def _on_nesting_worker_success(self, payload: Dict[str, Any]) -> None:
        ctx = self._worker_context or {}
        engine_args = ctx.get("engine_args", {})
        objective = engine_args.get("objective", "width")
        nesting_result = payload.get("nesting_result")
        if not nesting_result:
            QMessageBox.warning(self, "Nesting", "No se pudo encontrar una solución de nesting óptima.")
            return

        cache_entry = payload.get("cache_entry")
        cache_key = payload.get("cache_key")
        ctx_signature = ctx.get("signature")
        if cache_entry and cache_key:
            target_cache = (
                self.nesting_engine.nesting_cache_width
                if objective == "width" else self.nesting_engine.nesting_cache_height
            )
            target_cache.store(cache_entry, cache_key)
            self.logger.debug("Worker delivered cache entry (%s) key=%s", objective, cache_key)
        if ctx_signature:
            self._cache_signatures[objective] = ctx_signature
        start_time = ctx.get("start_time")
        if start_time is not None:
            duration = time.perf_counter() - start_time
            self.logger.info(
                "Nesting (%s) worker completado en %.2f s (firma %s).",
                objective,
                duration,
                ctx_signature
            )

        x_min, x_max = ctx.get("x_limits", (None, None))
        y_min, y_max = ctx.get("y_limits", (None, None))
        if None in (x_min, x_max, y_min, y_max):
            x_min, x_max, y_min, y_max = self._read_bed_limits()

        tiles_x = engine_args.get("tiles_x", 1)
        tiles_y = engine_args.get("tiles_y", 1)
        medianil_x = engine_args.get("medianil_x", 0.0)
        medianil_y = engine_args.get("medianil_y", 0.0)
        paso_y = engine_args.get("paso_y", 0.0)
        paso_x = engine_args.get("paso_x", 0.0)
        clearance = engine_args.get("clearance_cm", 0.0)

        self.scene.clear_scene()
        bed_rect = self.scene.draw_bed(x_min, x_max, y_min, y_max)
        self.scene.draw_tiling_pattern(nesting_result, tiles_x, tiles_y, medianil_x, medianil_y)
        self._yield_ui_events()

        bbox = self.nesting_engine.calculate_global_bbox(tiles_x, tiles_y, medianil_x, medianil_y, objective)
        if not bbox:
            QMessageBox.warning(self, "Nesting", "No se pudo calcular el bounding box del resultado.")
            return

        medida_x_raw = bbox[2] - bbox[0]
        medida_y_raw = bbox[3] - bbox[1]
        medida_x_total, medida_y_total = self._apply_margins_to_dims(medida_x_raw, medida_y_raw)
        self._ensure_layout_within_limits(medida_x_total, medida_y_total, x_min, x_max, y_min, y_max)
        area_total = medida_x_total * medida_y_total
        planilla = max(1, tiles_x * tiles_y)

        section_title = (
            "Resultado para minimizar ancho" if objective == "width" else "Resultado para minimizar alto"
        )
        tipo_encastre = "minimizar ancho" if objective == "width" else "minimizar alto"
        rows = [
            ("Tipo de encastre:", tipo_encastre),
            ("Cantidad de tiles en X:", tiles_x),
            ("Cantidad de tiles en Y:", tiles_y),
            ("Planilla:", planilla),
            ("Medida en X de la planilla:", f"{medida_x_total:.2f} cm"),
            ("Medida en Y de la planilla:", f"{medida_y_total:.2f} cm"),
            ("Área de la planilla:", f"{area_total:.2f} cm<sup>2</sup>"),
        ]
        mensaje = self._wrap_message_html(self._format_message_section(section_title, rows))
        QMessageBox.information(self, "Nesting Completado", mensaje)

        self._cache_signatures[objective] = cache_key
        self._update_current_state(medianil_x, medianil_y, tiles_x, tiles_y, paso_y, paso_x, clearance, objective)
        self._fit_layout_to_view(bed_rect)
        self._yield_ui_events()
        tiros_req = self._compute_tiros(planilla)
        self._update_resultados(planilla, medida_x_total, medida_y_total, tiros_req)
        self.logger.info("Nesting optimization completed for objective: %s", objective)

    def _on_nesting_worker_error(self, message: str) -> None:
        QMessageBox.critical(self, "Nesting", message)

    def _cleanup_worker(self) -> None:
        self._hide_progress_dialog()
        self._active_worker = None
        self._worker_context = {}

    def _start_nesting_worker(
        self,
        engine_args: Dict[str, Any],
        context: Dict[str, Any],
        message: str,
        show_progress: bool = True,
    ) -> None:
        if self._active_worker:
            self.logger.warning("Ya existe un cálculo de nesting en ejecución")
            return
        context["start_time"] = time.perf_counter()
        self._worker_context = context
        worker = NestingWorker(self.params, engine_args)
        worker.result_ready.connect(self._on_nesting_worker_success)
        worker.error.connect(self._on_nesting_worker_error)
        worker.finished.connect(self._cleanup_worker)
        self._active_worker = worker
        if show_progress:
            self._show_progress_dialog(message)
        worker.start()

    def _show_progress_dialog(self, message: str) -> None:
        if self._progress_dialog is None:
            dialog = QProgressDialog(message, None, 0, 0, self)
            dialog.setWindowTitle("Procesando")
            dialog.setCancelButton(None)
            dialog.setWindowModality(Qt.ApplicationModal)
            dialog.setMinimumDuration(0)
            self._progress_dialog = dialog
        else:
            self._progress_dialog.setLabelText(message)
        self._progress_dialog.show()
        QApplication.processEvents()

    def _hide_progress_dialog(self) -> None:
        if self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None
    def _ensure_layout_within_limits(self, medida_x: float, medida_y: float,
                                     x_min: Optional[float] = None, x_max: Optional[float] = None,
                                     y_min: Optional[float] = None, y_max: Optional[float] = None) -> None:
        """
        Validate that the provided dimensions (already including margins)
        stay within the configured Roland bed limits.
        """
        if None in (x_min, x_max, y_min, y_max):
            x_min, x_max, y_min, y_max = self._read_bed_limits()

        eps = 1e-6
        if medida_x < x_min - eps or medida_x > x_max + eps:
            raise ValueError(
                f"El ancho total ({medida_x:.2f} cm) queda fuera de los limites permitidos "
                f"({x_min:.2f}–{x_max:.2f} cm). Ajusta margenes o cantidad de tiles."
            )
        if medida_y < y_min - eps or medida_y > y_max + eps:
            raise ValueError(
                f"El alto total ({medida_y:.2f} cm) queda fuera de los limites permitidos "
                f"({y_min:.2f}–{y_max:.2f} cm). Ajusta margenes o cantidad de tiles."
            )



    def _update_resultados(self, planilla: int, medida_x: float, medida_y: float, tiros: int) -> None:

        self.lbl_res_planilla.setText(str(planilla))

        self.lbl_res_x.setText(f"{medida_x:.2f}")

        self.lbl_res_y.setText(f"{medida_y:.2f}")

        self.lbl_res_tiros.setText(str(tiros))



    def _format_message_section(self, title: str, rows: list[tuple[str, str]]) -> str:

        """Render a compact HTML section with a title and a key/value table."""

        normalized_rows = [(label, str(value)) for label, value in rows]

        table_rows = "".join(

            f"<tr><td style='padding:2px 12px 2px 0;color:#5a5a5a;'>{label}</td>"

            f"<td style='padding:2px 0;font-weight:600;color:#1f1f1f;'>{value}</td></tr>"

            for label, value in normalized_rows

        )

        return (

            "<div style='margin-bottom:14px;'>"

            f"<div style='font-size:11pt;font-weight:600;margin-bottom:4px;'>{title}</div>"

            f"<table style='border-collapse:collapse;font-size:10pt;'>{table_rows}</table>"

            "</div>"

        )



    def _wrap_message_html(self, body: str) -> str:

        """Wrap the provided body inside a styled HTML document for QMessageBox."""

        return (

            "<html>"

            "<body style=\"font-family:'Segoe UI',sans-serif;font-size:10pt;line-height:1.35;\">"

            f"{body}"

            "</body>"

            "</html>"

        )



    def _format_alert_message(self, lines: list[str]) -> str:

        """Create a simple HTML message with consistent spacing."""

        blocks = "".join(

            f"<div style='margin-bottom:6px;color:#2b2b2b;'>{line}</div>"

            for line in lines

        )

        return self._wrap_message_html(blocks)



    def _compute_tiros(self, planilla: int) -> int:

        if planilla <= 0:

            return 0

        volumen = max(0, self.get_volumen())

        tiros = math.ceil(volumen / planilla) if volumen > 0 else 0

        tiros = max(tiros, self.get_tiros_minimos())

        return tiros



    @staticmethod
    def _yield_ui_events() -> None:

        """Allow Qt to process pending events so the UI stays responsive."""

        app = QApplication.instance()

        if app:

            app.processEvents(QEventLoop.AllEvents, 5)


