"""
Plano (Editor) tab implementation for box parameter editing and visualization.
"""

import logging
from typing import List, Dict, Any
import unicodedata

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QFont, QPen
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QDoubleSpinBox,
    QPushButton, QLabel, QGroupBox, QGridLayout, QComboBox
)

from backend.models.parameters import PlanoParams, construir_shapes_px
from backend.models.templates import get_template
from .widgets import ZoomGraphicsView, PlanoScene


class PlanoTab(QWidget):
    """
    Editor tab for box parameter editing and visualization.
    
    Provides interactive editing of box dimensions and real-time visualization.
    
    Attributes:
        params (PlanoParams): Current box parameters
        scene (PlanoScene): Graphics scene for rendering
        view (ZoomGraphicsView): View for scene navigation
    """
    
    RENDER_ESCALA = 10.0
    RENDER_X0 = 100.0
    RENDER_Y0 = 200.0

    def __init__(self, params: PlanoParams):
        """
        Initialize plano tab with parameters.
        
        Args:
            params: Box parameters to edit and visualize
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.params = params
        self.params.escala = self.RENDER_ESCALA
        self.params.x0 = self.RENDER_X0
        self.params.y0 = self.RENDER_Y0
        self._template_name = "Personalizado"
        self._template_definitions = self._build_templates()
        self._applying_template = False
        
        self._setup_ui()
        self._connect_signals()
        
        # Initial render
        self.redibujar()
        
        self.logger.info("PlanoTab initialized successfully")

    def _setup_ui(self) -> None:
        """Setup user interface components."""
        # Create main layout
        layout = QHBoxLayout(self)
        
        # Create control panel
        control_panel = self._build_control_panel()
        layout.addWidget(control_panel, 0)
        
        # Create graphics view
        self.scene = PlanoScene()
        self.view = ZoomGraphicsView(self.scene)
        self.view.setBackgroundBrush(QColor(245, 245, 245))
        layout.addWidget(self.view, 1)

    def _build_control_panel(self) -> QWidget:
        """
        Build the control panel with parameter editors.
        
        Returns:
            Configured control panel widget
        """
        panel = QWidget()
        panel.setMaximumWidth(400)
        layout = QVBoxLayout(panel)
        
        # Template selector
        template_label = QLabel("Plantilla de caja:")
        self.cb_template = QComboBox()
        self.cb_template.addItems(["Personalizado", "Fondo automático", "Avion", "Francesa"])
        self.cb_template.currentTextChanged.connect(self._on_template_changed)
        layout.addWidget(template_label)
        layout.addWidget(self.cb_template)

        # Base measures group
        base_group = QGroupBox("Medidas base (cm)")
        base_form = QFormLayout(base_group)
        
        self.sb_L = self._create_spinbox(self.params.L, 0.1, 1000.0, 0.5)
        self.sb_A = self._create_spinbox(self.params.A, 0.1, 1000.0, 0.5)
        self.sb_h = self._create_spinbox(self.params.h, 0.1, 1000.0, 0.5)
        self.sb_cIzq = self._create_spinbox(self.params.cIzq, 0.0, 1000.0, 0.1)
        self.sb_cDer = self._create_spinbox(self.params.cDer, 0.0, 1000.0, 0.1)
        
        base_form.addRow("L (caras 1 y 3):", self.sb_L)
        base_form.addRow("A (caras 2 y 4):", self.sb_A)
        base_form.addRow("h (alto):", self.sb_h)
        base_form.addRow("Ceja lateral izq:", self.sb_cIzq)
        base_form.addRow("Ceja lateral der:", self.sb_cDer)
        
        # Per-face parameters group
        face_group = QGroupBox("Tapas / Cejas por cara (cm)")
        face_grid = QGridLayout(face_group)
        self.face_group = face_group

        headers = ["", "Cara 1", "Cara 2", "Cara 3", "Cara 4"]
        for col, header in enumerate(headers):
            label = QLabel(f"<b>{header}</b>")
            face_grid.addWidget(label, 0, col, alignment=Qt.AlignCenter)

        self.sb_Tapas = []
        self.sb_CSup = []
        self.sb_Bases = []
        self.sb_CInf = []

        rows = [
            ("Ceja Sup", self.params.CSup, self.sb_CSup),
            ("Tapa", self.params.Tapas, self.sb_Tapas),
            ("Base", self.params.Bases, self.sb_Bases),
            ("Ceja Inf", self.params.CInf, self.sb_CInf),
        ]

        for row_index, (label_text, values, target_list) in enumerate(rows, start=1):
            face_grid.addWidget(QLabel(f"<b>{label_text}</b>"), row_index, 0, alignment=Qt.AlignLeft)
            for cara in range(4):
                spin = self._create_spinbox(values[cara], 0.0, 100.0, 0.1)
                target_list.append(spin)
                face_grid.addWidget(spin, row_index, cara + 1)
        
        # Action buttons
        btn_redibujar = QPushButton("Redibujar")
        btn_redibujar.clicked.connect(self.redibujar)
        
        btn_reset_view = QPushButton("Reset vista")
        btn_reset_view.clicked.connect(self.reset_view)
        
        btn_open_tile = QPushButton("Abrir Tile (cama Roland)")
        btn_open_tile.clicked.connect(self.abrir_tile_tab)
        
        # Add all to layout
        layout.addWidget(base_group)
        layout.addWidget(face_group)
        layout.addWidget(btn_redibujar)
        layout.addWidget(btn_reset_view)
        layout.addWidget(btn_open_tile)
        layout.addStretch(1)
        self._set_face_group_enabled(self._is_custom_template())
        
        return panel

    def _create_spinbox(self, value: float, min_val: float, max_val: float, step: float) -> QDoubleSpinBox:
        """
        Create a standardized double spinbox.
        
        Args:
            value: Initial value
            min_val: Minimum value
            max_val: Maximum value
            step: Step size
            
        Returns:
            Configured QDoubleSpinBox
        """
        spinbox = QDoubleSpinBox()
        spinbox.setDecimals(2)
        spinbox.setRange(min_val, max_val)
        spinbox.setSingleStep(step)
        spinbox.setValue(value)
        return spinbox

    def _connect_signals(self) -> None:
        """Connect signal handlers for automatic updates."""
        # Connect value change signals for real-time updates
        spinboxes = [
            self.sb_L, self.sb_A, self.sb_h, self.sb_cIzq, self.sb_cDer
        ]
        
        for spinbox in spinboxes:
            spinbox.valueChanged.connect(self._on_parameter_changed)
        
        # Connect face parameter spinboxes
        for i in range(4):
            self.sb_Tapas[i].valueChanged.connect(self._on_parameter_changed)
            self.sb_CSup[i].valueChanged.connect(self._on_parameter_changed)
            self.sb_Bases[i].valueChanged.connect(self._on_parameter_changed)
            self.sb_CInf[i].valueChanged.connect(self._on_parameter_changed)

    def _on_parameter_changed(self) -> None:
        """
        Handle parameter changes with automatic update.
        
        This provides real-time feedback as users adjust parameters.
        """
        self.sync_params()
        if not self._is_custom_template():
            self._apply_template(self._template_name)
            return
        self.redibujar()

    def sync_params(self) -> None:
        """Synchronize UI values with parameters object."""
        self.params.L = self.sb_L.value()
        self.params.A = self.sb_A.value()
        self.params.h = self.sb_h.value()
        self.params.cIzq = self.sb_cIzq.value()
        self.params.cDer = self.sb_cDer.value()
        
        for i in range(4):
            self.params.Tapas[i] = self.sb_Tapas[i].value()
            self.params.CSup[i] = self.sb_CSup[i].value()
            self.params.Bases[i] = self.sb_Bases[i].value()
            self.params.CInf[i] = self.sb_CInf[i].value()
        
        self.params.escala = self.RENDER_ESCALA
        self.params.x0 = self.RENDER_X0
        self.params.y0 = self.RENDER_Y0
        
        self.logger.debug("Parameters synchronized")

    def redibujar(self) -> None:
        """Redraw the plano with current parameters."""
        try:
            self.scene.render_plano(self.params)
            bbox = self.scene.bounding_box_px(self.params)
            self.view.resetTransform()
            self.view.fitInView(bbox, Qt.KeepAspectRatio)
            
            self.logger.debug("Plano redrawn successfully")
            
        except Exception as e:
            self.logger.error("Error redrawing plano: %s", e, exc_info=True)

    def reset_view(self) -> None:
        """Reset view to default position and scale."""
        self.view.resetTransform()
        self.view.centerOn(QPointF(self.params.x0, self.params.y0))
        self.logger.debug("View reset to default")

    def abrir_tile_tab(self) -> None:
        """Request to open the Tile tab from parent window."""
        try:
            # Ensure parameters are synced
            self.sync_params()
            
            # Emit signal or call parent method
            if hasattr(self.parent(), 'abrir_tile_tab'):
                self.parent().abrir_tile_tab()
            elif hasattr(self.window(), 'abrir_tile_tab'):
                self.window().abrir_tile_tab()
            else:
                self.logger.warning("Could not find method to open tile tab")
                
        except Exception as e:
            self.logger.error("Error opening tile tab: %s", e, exc_info=True)

    def get_current_params(self) -> PlanoParams:
        """
        Get current parameters (synced from UI).
        
        Returns:
            Current PlanoParams object
        """
        self.sync_params()
        return self.params.copy()

    def load_params(self, params: PlanoParams) -> None:
        """
        Load parameters into UI.
        
        Args:
            params: Parameters to load
        """
        self.params = params.copy()
        self.params.escala = self.RENDER_ESCALA
        self.params.x0 = self.RENDER_X0
        self.params.y0 = self.RENDER_Y0
        self.params.cDer = 0.0
        self._update_ui_from_params()
        self.redibujar()

    def _update_ui_from_params(self) -> None:
        """Update UI elements from current parameters."""
        # Block signals to prevent recursive updates
        self.sb_L.blockSignals(True)
        self.sb_A.blockSignals(True)
        self.sb_h.blockSignals(True)
        self.sb_cIzq.blockSignals(True)
        self.sb_cDer.blockSignals(True)
        
        self.sb_L.setValue(self.params.L)
        self.sb_A.setValue(self.params.A)
        self.sb_h.setValue(self.params.h)
        self.sb_cIzq.setValue(self.params.cIzq)
        self.sb_cDer.setValue(self.params.cDer)
        
        for i in range(4):
            self.sb_Tapas[i].blockSignals(True)
            self.sb_CSup[i].blockSignals(True)
            self.sb_Bases[i].blockSignals(True)
            self.sb_CInf[i].blockSignals(True)
            
            self.sb_Tapas[i].setValue(self.params.Tapas[i])
            self.sb_CSup[i].setValue(self.params.CSup[i])
            self.sb_Bases[i].setValue(self.params.Bases[i])
            self.sb_CInf[i].setValue(self.params.CInf[i])
            
            self.sb_Tapas[i].blockSignals(False)
            self.sb_CSup[i].blockSignals(False)
            self.sb_Bases[i].blockSignals(False)
            self.sb_CInf[i].blockSignals(False)
        
        # Restore signals
        self.sb_L.blockSignals(False)
        self.sb_A.blockSignals(False)
        self.sb_h.blockSignals(False)
        self.sb_cIzq.blockSignals(False)
        self.sb_cDer.blockSignals(False)

    def validate_parameters(self) -> bool:
        """
        Validate current parameters.
        
        Returns:
            True if parameters are valid
        """
        is_valid, message = self.params.validate()
        if not is_valid:
            self.logger.warning("Parameter validation failed: %s", message)
        return is_valid

    def export_to_svg(self, filename: str) -> bool:
        """
        Export current plano to SVG file.
        
        Args:
            filename: Output SVG filename
            
        Returns:
            True if export successful
        """
        try:
            # This would implement SVG export functionality
            # For now, just log the request
            self.logger.info("Export to SVG requested: %s", filename)
            return True
            
        except Exception as e:
            self.logger.error("Error exporting to SVG: %s", e, exc_info=True)
            return False

    def show_bounding_box(self) -> None:
        """Display bounding box information."""
        try:
            bbox = self.scene.bounding_box_px(self.params)
            width_cm = bbox.width() / self.params.escala
            height_cm = bbox.height() / self.params.escala
            
            self.logger.info(
                "Bounding box: %.2f x %.2f cm (%.2f x %.2f px)",
                width_cm, height_cm, bbox.width(), bbox.height()
            )
            
        except Exception as e:
            self.logger.error("Error calculating bounding box: %s", e)

    # Template helpers

    def _on_template_changed(self, template_name: str) -> None:
        self._template_name = template_name
        is_custom = self._is_custom_template()
        self._set_face_group_enabled(is_custom)
        if not is_custom:
            self._apply_template(template_name)
        else:
            self.redibujar()

    def _apply_template(self, template_name: str) -> None:
        key = self._normalize_template_name(template_name)
        definition = self._template_definitions.get(key)
        if not definition or self._applying_template:
            return
        self._applying_template = True
        try:
            values = definition(self.params)
            self.params.Tapas = values.get("Tapas", self.params.Tapas)
            self.params.CSup = values.get("CejaSup", self.params.CSup)
            self.params.Bases = values.get("Bases", self.params.Bases)
            self.params.CInf = values.get("CejaInf", self.params.CInf)
            if "cDer" in values:
                self.params.cDer = values["cDer"]
            self._update_ui_from_params()
            self.redibujar()
        finally:
            self._applying_template = False

    def _set_face_group_enabled(self, enabled: bool) -> None:
        self.face_group.setVisible(enabled)
        for spin_list in (self.sb_Tapas, self.sb_CSup, self.sb_Bases, self.sb_CInf):
            for spin in spin_list:
                spin.setEnabled(enabled)

    def _is_custom_template(self) -> bool:
        return self._normalize_template_name(self._template_name) == "personalizado"

    def _normalize_template_name(self, name: str) -> str:
        normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
        return normalized.strip().lower()

    def _build_templates(self) -> Dict[str, Any]:
        return {key: get_template(key.lower()).builder for key in ["personalizado", "fondo automatico", "avion", "francesa"]}
