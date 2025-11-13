"""
Main application window with tab management.
"""

import sys
import logging
import time
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QFormLayout, QDoubleSpinBox, QPushButton, QLabel, QGraphicsScene,
    QGraphicsView, QGroupBox, QGridLayout, QTabWidget, QMessageBox, QSpinBox,
    QProgressDialog
)

from backend.models.parameters import PlanoParams
from .plano_tab import PlanoTab
from .tile_tab import TileTab


class MainWindow(QMainWindow):
    """
    Main application window with tabbed interface.
    
    Attributes:
        params (PlanoParams): Current box parameters
        tabs (QTabWidget): Tab container
        plano_tab (PlanoTab): Editor tab
        tile_tab (Optional[TileTab]): Nesting tab (created on demand)
    """
    
    def __init__(self):
        """Initialize main window with default parameters."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.params = PlanoParams()
        self.tile_tab: Optional[TileTab] = None
        self.progress_weights = {
            "sync": 0.2,
            "update": 0.2,
            "render": 0.6,
        }
        
        self._setup_ui()
        self._connect_signals()
        
        self.logger.info("MainWindow initialized successfully")

    def _setup_ui(self) -> None:
        """Setup user interface components."""
        self.setWindowTitle("Box Nesting Optimization System - PySide6")
        self.resize(1300, 900)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create editor tab
        self.plano_tab = PlanoTab(self.params)
        self.tabs.addTab(self.plano_tab, "Plano (Editor)")
        
        # Set central widget
        self.setCentralWidget(self.tabs)

    def _connect_signals(self) -> None:
        """Connect signal handlers."""
        # Connect plano tab signals if needed
        pass

    def abrir_tile_tab(self) -> None:
        """
        Open or refresh the Tile tab with current parameters.
        
        Clears cache when reopening with new parameters.
        """
        self.logger.info("Abrir Tile: inicio del flujo")
        progress = None
        animation_timer = None
        try:
            step_start = time.perf_counter()
            progress = QProgressDialog("Sincronizando parámetros...", None, 0, 100, self)
            progress.setWindowTitle("Cargando")
            progress.setWindowModality(Qt.ApplicationModal)
            progress.setCancelButton(None)
            progress.setAutoClose(False)
            progress.setAutoReset(False)
            progress.show()
            QApplication.processEvents()
            self.logger.debug("Abrir Tile: diálogo de progreso creado en %.2f ms", (time.perf_counter() - step_start) * 1000)

            weights = self.progress_weights.copy()
            weights_total = sum(weights.values()) or 1.0
            sync_weight = max(0.01, weights["sync"] / weights_total)
            update_weight = max(0.01, weights["update"] / weights_total)
            render_weight = max(0.01, weights["render"] / weights_total)
            self.logger.debug(
                "Abrir Tile: pesos actuales sync=%.3f update=%.3f render=%.3f (total=%.3f)",
                sync_weight, update_weight, render_weight, weights_total
            )

            display_sync = sync_weight
            display_update = update_weight
            display_render = render_weight * 3.0  # triple emphasis on heavy step
            display_total = display_sync + display_update + display_render

            sync_cut = sync_weight
            update_cut = sync_weight + update_weight  # render covers the rest

            progress_state = {"current": 0, "target": 0}

            def normalize_ratio(ratio: float) -> float:
                ratio = max(0.0, min(1.0, ratio))
                if ratio <= sync_cut:
                    proportion = (ratio / sync_cut) if sync_cut else 0.0
                    return (display_sync / display_total) * proportion
                if ratio <= update_cut:
                    proportion = ((ratio - sync_cut) / (update_cut - sync_cut)) if (update_cut - sync_cut) else 0.0
                    return (display_sync / display_total) + (display_update / display_total) * proportion
                proportion = ((ratio - update_cut) / (1.0 - update_cut)) if (1.0 - update_cut) else 0.0
                return ((display_sync + display_update) / display_total) + (display_render / display_total) * proportion

            def set_target_ratio(ratio: float) -> None:
                normalized = normalize_ratio(max(0.0, min(1.0, ratio)))
                target_value = int(progress.maximum() * normalized)
                if target_value > progress_state["target"]:
                    progress_state["target"] = min(progress.maximum(), target_value)

            def _spin():
                if progress is None:
                    return
                if progress_state["current"] < progress_state["target"]:
                    progress_state["current"] += 1
                    progress.setValue(progress_state["current"])

            animation_timer = QTimer(progress)
            animation_timer.timeout.connect(_spin)
            animation_timer.start(40)
            set_target_ratio(0.02)

            progress.setLabelText("Sincronizando parámetros del editor...")
            QApplication.processEvents()
            sync_start = time.perf_counter()
            self.plano_tab.sync_params()
            sync_duration = time.perf_counter() - sync_start
            set_target_ratio(sync_cut)
            self.logger.info(
                "Abrir Tile: sincronización completada en %.2f s (params L=%.2f A=%.2f h=%.2f)",
                sync_duration,
                getattr(self.params, "L", 0.0),
                getattr(self.params, "A", 0.0),
                getattr(self.params, "h", 0.0),
            )

            progress.setLabelText("Actualizando pestaña Tile...")
            QApplication.processEvents()
            update_start = time.perf_counter()
            created_tile_tab = False
            if self.tile_tab is None:
                self.logger.debug("Abrir Tile: creando nueva instancia de TileTab")
                self.tile_tab = TileTab(self.params)
                self.tabs.addTab(self.tile_tab, "Tile (Cama Roland)")
                created_tile_tab = True
            else:
                self.logger.debug("Abrir Tile: actualizando TileTab existente")
                self.tile_tab.update_params(self.params)
            update_duration = time.perf_counter() - update_start
            set_target_ratio(update_cut)
            self.logger.info(
                "Abrir Tile: TileTab %s en %.2f s (cache firmas width=%s height=%s)",
                "creado" if created_tile_tab else "actualizado",
                update_duration,
                getattr(self.tile_tab, "_cache_signatures", {}).get("width") if self.tile_tab else None,
                getattr(self.tile_tab, "_cache_signatures", {}).get("height") if self.tile_tab else None,
            )

            progress.setLabelText("Renderizando layout...")
            QApplication.processEvents()
            render_start = time.perf_counter()
            self.logger.debug(
                "Abrir Tile: invocando render(force_recalculate=False) con tiles=%dx%d medianil=(%.2f, %.2f)",
                int(self.tile_tab.sb_tiles_x.value()) if self.tile_tab else -1,
                int(self.tile_tab.sb_tiles_y.value()) if self.tile_tab else -1,
                self.tile_tab.sb_medianil_x.value() if self.tile_tab else 0.0,
                self.tile_tab.sb_medianil_y.value() if self.tile_tab else 0.0,
            )
            self.tile_tab.render(force_recalculate=False)
            self.tabs.setCurrentWidget(self.tile_tab)
            render_duration = time.perf_counter() - render_start
            set_target_ratio(1.0)
            self.logger.info("Abrir Tile: render inicial completado en %.2f s", render_duration)

            if animation_timer is not None:
                # Allow timer to catch up to the final target smoothly
                deadline = time.perf_counter() + 3.0  # safety timeout
                while progress_state["current"] < progress_state["target"] and time.perf_counter() < deadline:
                    QApplication.processEvents()
                    time.sleep(0.01)
                animation_timer.stop()
            progress.setValue(progress_state["current"])
            QApplication.processEvents()

            total_duration = sync_duration + update_duration + render_duration
            self.logger.info(
                "Tile tab opened successfully (total %.2f s: sync=%.2fs, update=%.2fs, render=%.2fs)",
                total_duration, sync_duration, update_duration, render_duration
            )

            if total_duration > 0:
                new_weights = {
                    "sync": sync_duration / total_duration,
                    "update": update_duration / total_duration,
                    "render": render_duration / total_duration,
                }
                smoothing = 0.7
                for key in self.progress_weights:
                    self.progress_weights[key] = (
                        smoothing * self.progress_weights[key] + (1 - smoothing) * new_weights[key]
                    )
            
        except Exception as e:
            self.logger.error(f"Failed to open tile tab: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"No se pudo abrir la pestaña Tile: {e}")
        finally:
            if animation_timer is not None:
                animation_timer.stop()
            if progress is not None:
                progress.close()

    def closeEvent(self, event):
        """Handle application close event."""
        self.logger.info("Application closing")
        super().closeEvent(event)
