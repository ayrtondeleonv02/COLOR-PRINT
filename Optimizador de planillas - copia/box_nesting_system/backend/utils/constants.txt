"""
Constants and configuration for the Box Nesting Optimization System.
"""

from typing import Tuple
from dataclasses import dataclass
from enum import Enum


# Scale conversion constant
SCALE_INT = 1000  # 1 cm => 1000 integer units (reduce float errors)


class NestingObjective(Enum):
    """Nesting optimization objectives."""
    MINIMIZE_WIDTH = "width"
    MINIMIZE_HEIGHT = "height" 
    MINIMIZE_AREA = "area"
    MAXIMIZE_EFFICIENCY = "efficiency"


@dataclass
class ColorScheme:
    """Color scheme for consistent UI styling."""
    
    # Main colors
    BED_BACKGROUND: Tuple[int, int, int] = (252, 252, 252)
    BED_OUTLINE: Tuple[int, int, int] = (70, 150, 255)
    GRID_LINES: Tuple[int, int, int] = (210, 210, 210)
    
    # Geometric elements
    FACE_COLOR: Tuple[int, int, int] = (0, 150, 0)
    TAB_COLOR: Tuple[int, int, int] = (150, 0, 0)
    FLANGE_COLOR: Tuple[int, int, int] = (200, 0, 0)
    VERTEX_COLOR: Tuple[int, int, int] = (30, 30, 30)
    
    # UI elements
    SCENE_BACKGROUND: Tuple[int, int, int] = (24, 24, 28)
    TEXT_COLOR: Tuple[int, int, int] = (10, 10, 10)
    ACCENT_COLOR: Tuple[int, int, int] = (255, 40, 40)
    
    # Status colors
    SUCCESS_COLOR: Tuple[int, int, int] = (0, 150, 0)
    WARNING_COLOR: Tuple[int, int, int] = (255, 165, 0)
    ERROR_COLOR: Tuple[int, int, int] = (220, 0, 0)
    
    def to_qt_color(self, color_tuple: Tuple[int, int, int]):
        """Convert RGB tuple to QColor."""
        from PySide6.QtGui import QColor
        return QColor(*color_tuple)
    
    # Añadir métodos de conveniencia
    def get_bed_background(self):
        """Get bed background color as QColor."""
        return self.to_qt_color(self.BED_BACKGROUND)
    
    def get_bed_outline(self):
        """Get bed outline color as QColor."""
        return self.to_qt_color(self.BED_OUTLINE)
    
    def get_grid_lines(self):
        """Get grid lines color as QColor."""
        return self.to_qt_color(self.GRID_LINES)
    
    def get_accent_color(self):
        """Get accent color as QColor."""
        return self.to_qt_color(self.ACCENT_COLOR)
    
    def get_tile_fill(self):
        """Get tile fill color as QColor."""
        return self.to_qt_color((230, 230, 230))  # Añadir este color
    
    def get_tile_outline(self):
        """Get tile outline color as QColor."""
        return self.to_qt_color(self.ACCENT_COLOR)


@dataclass 
class FontScheme:
    """Font configuration for UI elements."""
    
    PRIMARY_FAMILY: str = "Segoe UI"
    MONOSPACE_FAMILY: str = "Consolas"
    
    # Sizes
    SMALL: int = 8
    MEDIUM: int = 10
    LARGE: int = 12
    XLARGE: int = 14
    TITLE: int = 16
    
    # Weights
    LIGHT: int = 300
    NORMAL: int = 400
    MEDIUM_WEIGHT: int = 500
    BOLD: int = 700


@dataclass
class NestingConstants:
    """Constants for nesting configuration and algorithms."""
    
    # Geometry
    DEFAULT_ROTATIONS: Tuple[int, ...] = (0, 90, 180, 270)
    VALID_OBJECTIVES: Tuple[str, ...] = ("width", "height", "area")
    
    # Search parameters
    DEFAULT_PASO_Y: float = 0.5
    DEFAULT_PASO_X: float = 0.1
    MIN_PASO: float = 0.05
    MAX_PASO: float = 10.0
    
    # Performance limits
    MAX_TILES_X: int = 100
    MAX_TILES_Y: int = 100
    MAX_SEARCH_ITERATIONS: int = 10000
    CACHE_VALIDITY_SECONDS: float = 3600.0
    
    # Roland bed defaults (cm)
    ROLAND_X_MAX: float = 73.0
    ROLAND_Y_MAX: float = 103.0
    ROLAND_X_MIN: float = 38.0
    ROLAND_Y_MIN: float = 48.0
    
    # Default margins (cm)
    DEFAULT_SANGRIA_IZQUIERDA: float = 0.0
    DEFAULT_SANGRIA_DERECHA: float = 0.0
    DEFAULT_PINZA: float = 0.0
    DEFAULT_CONTRA_PINZA: float = 0.0
    
    # Default separations
    DEFAULT_MEDIANIL_X: float = 0.0
    DEFAULT_MEDIANIL_Y: float = 0.0
    DEFAULT_CLEARANCE: float = 0.0
    
    # Rendering defaults
    DEFAULT_ESCALA: float = 10.0
    DEFAULT_X0: float = 100.0
    DEFAULT_Y0: float = 200.0
    
    # Numerical tolerances
    EPSILON: float = 1e-9
    FLOAT_TOLERANCE: float = 1e-6


# Default configuration instances
DEFAULT_COLORS = ColorScheme()
DEFAULT_FONTS = FontScheme()
DEFAULT_CONSTANTS = NestingConstants()