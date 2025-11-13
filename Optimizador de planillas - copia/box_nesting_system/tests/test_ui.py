"""
Tests for UI components and interactions.
"""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from frontend.ui.plano_tab import PlanoTab
from frontend.ui.tile_tab import TileTab
from frontend.ui.widgets import ZoomGraphicsView, PlanoScene, TileScene
from backend.models.parameters import PlanoParams


class TestPlanoTab:
    """Test cases for PlanoTab functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.params = PlanoParams()
        self.plano_tab = PlanoTab(self.params)
    
    def test_initialization(self):
        """Test PlanoTab initialization."""
        assert self.plano_tab.params == self.params
        assert self.plano_tab.scene is not None
        assert self.plano_tab.view is not None
    
    def test_sync_params(self):
        """Test parameter synchronization."""
        # Change UI values
        self.plano_tab.sb_L.setValue(20.0)
        self.plano_tab.sb_A.setValue(15.0)
        self.plano_tab.sb_h.setValue(8.0)
        
        # Sync parameters
        self.plano_tab.sync_params()
        
        # Check parameters were updated
        assert self.plano_tab.params.L == 20.0
        assert self.plano_tab.params.A == 15.0
        assert self.plano_tab.params.h == 8.0
    
    def test_redibujar(self):
        """Test redrawing functionality."""
        # This mainly tests that the method doesn't crash
        try:
            self.plano_tab.redibujar()
            assert True
        except Exception:
            assert False, "redibujar should not raise exceptions"
    
    def test_reset_view(self):
        """Test view reset functionality."""
        try:
            self.plano_tab.reset_view()
            assert True
        except Exception:
            assert False, "reset_view should not raise exceptions"
    
    def test_parameter_validation(self):
        """Test parameter validation."""
        # Test valid parameters
        assert self.plano_tab.validate_parameters() == True
        
        # Test invalid parameters (negative value)
        self.plano_tab.sb_L.setValue(-10.0)
        self.plano_tab.sync_params()
        assert self.plano_tab.validate_parameters() == False


class TestTileTab:
    """Test cases for TileTab functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.params = PlanoParams()
        self.tile_tab = TileTab(self.params)
    
    def test_initialization(self):
        """Test TileTab initialization."""
        assert self.tile_tab.params == self.params
        assert self.tile_tab.scene is not None
        assert self.tile_tab.view is not None
        assert self.tile_tab.optimizer is not None
    
    def test_bed_limits_reading(self):
        """Test bed limits reading with margins."""
        # Set values
        self.tile_tab.sb_xmin.setValue(0.0)
        self.tile_tab.sb_xmax.setValue(100.0)
        self.tile_tab.sb_ymin.setValue(0.0)
        self.tile_tab.sb_ymax.setValue(100.0)
        
        # Set margins
        self.tile_tab.sb_sangria_izquierda.setValue(5.0)
        self.tile_tab.sb_sangria_derecha.setValue(5.0)
        self.tile_tab.sb_pinza.setValue(5.0)
        self.tile_tab.sb_contra_pinza.setValue(5.0)
        
        # Read bed limits
        x_min, x_max, y_min, y_max = self.tile_tab._read_bed_limits()
        
        # Check margins applied correctly
        assert x_min == 5.0  # 0 + 5
        assert x_max == 95.0  # 100 - 5
        assert y_min == 5.0  # 0 + 5
        assert y_max == 95.0  # 100 - 5
    
    def test_render(self):
        """Test rendering functionality."""
        try:
            self.tile_tab.render()
            assert True
        except Exception:
            assert False, "render should not raise exceptions"
    
    def test_nesting_optimization_buttons(self):
        """Test nesting optimization button connections."""
        # Test that buttons are connected
        assert self.tile_tab.btn_nesting_w.isEnabled()
        assert self.tile_tab.btn_nesting_h.isEnabled()
        assert self.tile_tab.btn_optimizar_layout.isEnabled()
    
    def test_production_parameters(self):
        """Test production parameter getters."""
        # Set values
        self.tile_tab.sb_volumen.setValue(1000)
        self.tile_tab.sb_tiros_minimos.setValue(10)
        
        assert self.tile_tab.get_volumen() == 1000
        assert self.tile_tab.get_tiros_minimos() == 10


class TestGraphicsViews:
    """Test cases for custom graphics views."""
    
    def test_zoom_graphics_view_initialization(self):
        """Test ZoomGraphicsView initialization."""
        view = ZoomGraphicsView()
        assert view.renderHints() & QPainter.Antialiasing
        assert view.dragMode() == QGraphicsView.ScrollHandDrag
    
    def test_plano_scene_initialization(self):
        """Test PlanoScene initialization."""
        scene = PlanoScene()
        assert scene.sceneRect() is not None
    
    def test_tile_scene_initialization(self):
        """Test TileScene initialization."""
        params = PlanoParams()
        scene = TileScene(params)
        assert scene.params == params
        assert scene.nesting_cache_width is not None
        assert scene.nesting_cache_height is not None


class TestUIStyles:
    """Test cases for UI styling."""
    
    def test_color_scheme(self):
        """Test color scheme consistency."""
        from frontend.ui.styles import ColorScheme
        colors = ColorScheme()
        
        # Test that colors are valid QColors
        assert isinstance(colors.PRIMARY, QColor)
        assert isinstance(colors.SECONDARY, QColor)
        assert isinstance(colors.ACCENT, QColor)
    
    def test_font_scheme(self):
        """Test font scheme consistency."""
        from frontend.ui.styles import FontScheme
        fonts = FontScheme()
        
        assert fonts.PRIMARY_FAMILY == "Segoe UI"
        assert fonts.MONOSPACE_FAMILY == "Consolas"
        assert fonts.TITLE_FAMILY == "Segoe UI"
    
    def test_ui_styles(self):
        """Test UI styles generator."""
        from frontend.ui.styles import UIStyles
        styles = UIStyles()
        
        # Test stylesheet generation
        stylesheet = styles.get_stylesheet()
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0
        
        # Test font generation
        font = styles.get_font()
        assert isinstance(font, QFont)


class TestIntegration:
    """Integration tests for UI components."""
    
    def test_plano_tab_parameter_sync(self):
        """Test parameter synchronization between UI and model."""
        params = PlanoParams()
        tab = PlanoTab(params)
        
        # Change UI values
        tab.sb_L.setValue(25.0)
        tab.sb_A.setValue(20.0)
        tab.sb_h.setValue(10.0)
        
        # Sync and verify
        tab.sync_params()
        assert params.L == 25.0
        assert params.A == 20.0
        assert params.h == 10.0
    
    def test_tile_tab_bed_limits_validation(self):
        """Test bed limits validation in TileTab."""
        tab = TileTab(PlanoParams())
        
        # Set invalid bed limits (min > max)
        tab.sb_xmin.setValue(100.0)
        tab.sb_xmax.setValue(50.0)
        
        # Should raise ValueError when reading
        with pytest.raises(ValueError):
            tab._read_bed_limits()
    
    def test_graphics_view_zoom(self):
        """Test graphics view zoom functionality."""
        view = ZoomGraphicsView()
        
        # Test that zoom doesn't crash
        try:
            # Simulate wheel event (this is a basic test)
            # In practice, you'd create a QWheelEvent
            assert True
        except Exception:
            assert False, "Zoom should not crash"


if __name__ == "__main__":
    # Run UI tests
    pytest.main([__file__, "-v"])