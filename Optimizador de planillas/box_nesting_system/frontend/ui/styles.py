"""
Style definitions for the Box Nesting Optimization System UI.
"""

from typing import Dict, Any
from dataclasses import dataclass

from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt


@dataclass
class ColorScheme:
    """Color scheme for consistent UI styling."""
    
    # Main colors
    PRIMARY: QColor = QColor(41, 128, 185)
    SECONDARY: QColor = QColor(52, 152, 219)
    ACCENT: QColor = QColor(231, 76, 60)
    
    # Background colors
    BACKGROUND_LIGHT: QColor = QColor(252, 252, 252)
    BACKGROUND_DARK: QColor = QColor(24, 24, 28)
    BACKGROUND_NEUTRAL: QColor = QColor(245, 245, 245)
    
    # Text colors
    TEXT_PRIMARY: QColor = QColor(10, 10, 10)
    TEXT_SECONDARY: QColor = QColor(100, 100, 100)
    TEXT_INVERTED: QColor = QColor(255, 255, 255)
    
    # Border colors
    BORDER_LIGHT: QColor = QColor(210, 210, 210)
    BORDER_MEDIUM: QColor = QColor(180, 180, 180)
    BORDER_DARK: QColor = QColor(120, 120, 120)
    
    # Status colors
    SUCCESS: QColor = QColor(39, 174, 96)
    WARNING: QColor = QColor(243, 156, 18)
    ERROR: QColor = QColor(231, 76, 60)
    INFO: QColor = QColor(52, 152, 219)
    
    # Geometric elements
    FACE_COLOR: QColor = QColor(0, 150, 0)
    TAB_COLOR: QColor = QColor(150, 0, 0)
    FLANGE_COLOR: QColor = QColor(200, 0, 0)
    VERTEX_COLOR: QColor = QColor(30, 30, 30)
    
    # Roland bed
    BED_BACKGROUND: QColor = QColor(252, 252, 252)
    BED_OUTLINE: QColor = QColor(70, 150, 255)
    GRID_LINES: QColor = QColor(210, 210, 210)


@dataclass
class FontScheme:
    """Font scheme for consistent typography."""
    
    # Font families
    PRIMARY_FAMILY: str = "Segoe UI"
    MONOSPACE_FAMILY: str = "Consolas"
    TITLE_FAMILY: str = "Segoe UI"
    
    # Font sizes
    EXTRA_SMALL: int = 8
    SMALL: int = 10
    MEDIUM: int = 12
    LARGE: int = 14
    EXTRA_LARGE: int = 16
    TITLE: int = 18
    
    # Font weights
    LIGHT: int = 300
    NORMAL: int = 400
    MEDIUM_WEIGHT: int = 500
    SEMI_BOLD: int = 600
    BOLD: int = 700


@dataclass
class SizeScheme:
    """Size scheme for consistent spacing and dimensions."""
    
    # Spacing
    TINY: int = 2
    SMALL: int = 4
    MEDIUM: int = 8
    LARGE: int = 12
    EXTRA_LARGE: int = 16
    HUGE: int = 24
    
    # Border radii
    BORDER_RADIUS_SMALL: int = 4
    BORDER_RADIUS_MEDIUM: int = 6
    BORDER_RADIUS_LARGE: int = 8
    
    # Control heights
    CONTROL_HEIGHT_SMALL: int = 24
    CONTROL_HEIGHT_MEDIUM: int = 32
    CONTROL_HEIGHT_LARGE: int = 40


class UIStyles:
    """
    Centralized UI style definitions.
    
    Provides consistent styling across the application.
    """
    
    def __init__(self):
        """Initialize with default schemes."""
        self.colors = ColorScheme()
        self.fonts = FontScheme()
        self.sizes = SizeScheme()
    
    def get_stylesheet(self, widget_type: str = "default") -> str:
        """
        Get stylesheet for specific widget type.
        
        Args:
            widget_type: Type of widget to style
            
        Returns:
            CSS stylesheet string
        """
        base_styles = f"""
        QWidget {{
            background-color: {self.colors.BACKGROUND_LIGHT.name()};
            color: {self.colors.TEXT_PRIMARY.name()};
            font-family: {self.fonts.PRIMARY_FAMILY};
            font-size: {self.fonts.MEDIUM}px;
        }}
        
        QGroupBox {{
            font-weight: {self.fonts.SEMI_BOLD};
            font-size: {self.fonts.LARGE}px;
            border: 1px solid {self.colors.BORDER_MEDIUM.name()};
            border-radius: {self.sizes.BORDER_RADIUS_MEDIUM}px;
            margin-top: {self.sizes.MEDIUM}px;
            padding-top: {self.sizes.MEDIUM}px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: {self.sizes.LARGE}px;
            padding: 0 {self.sizes.SMALL}px 0 {self.sizes.SMALL}px;
            color: {self.colors.PRIMARY.name()};
        }}
        
        QPushButton {{
            background-color: {self.colors.PRIMARY.name()};
            color: {self.colors.TEXT_INVERTED.name()};
            border: none;
            border-radius: {self.sizes.BORDER_RADIUS_MEDIUM}px;
            padding: {self.sizes.SMALL}px {self.sizes.LARGE}px;
            font-weight: {self.fonts.MEDIUM_WEIGHT};
            min-height: {self.sizes.CONTROL_HEIGHT_MEDIUM}px;
        }}
        
        QPushButton:hover {{
            background-color: {self.colors.SECONDARY.name()};
        }}
        
        QPushButton:pressed {{
            background-color: {self.colors.PRIMARY.name()};
        }}
        
        QPushButton:disabled {{
            background-color: {self.colors.BORDER_LIGHT.name()};
            color: {self.colors.TEXT_SECONDARY.name()};
        }}
        
        QDoubleSpinBox, QSpinBox {{
            border: 1px solid {self.colors.BORDER_MEDIUM.name()};
            border-radius: {self.sizes.BORDER_RADIUS_SMALL}px;
            padding: {self.sizes.SMALL}px;
            min-height: {self.sizes.CONTROL_HEIGHT_MEDIUM}px;
            background-color: white;
        }}
        
        QDoubleSpinBox:focus, QSpinBox:focus {{
            border-color: {self.colors.PRIMARY.name()};
        }}
        
        QLabel {{
            color: {self.colors.TEXT_PRIMARY.name()};
            font-size: {self.fonts.MEDIUM}px;
        }}
        
        QTabWidget::pane {{
            border: 1px solid {self.colors.BORDER_MEDIUM.name()};
            background-color: {self.colors.BACKGROUND_LIGHT.name()};
        }}
        
        QTabBar::tab {{
            background-color: {self.colors.BACKGROUND_NEUTRAL.name()};
            color: {self.colors.TEXT_PRIMARY.name()};
            padding: {self.sizes.MEDIUM}px {self.sizes.LARGE}px;
            margin-right: {self.sizes.TINY}px;
            border-top-left-radius: {self.sizes.BORDER_RADIUS_SMALL}px;
            border-top-right-radius: {self.sizes.BORDER_RADIUS_SMALL}px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {self.colors.PRIMARY.name()};
            color: {self.colors.TEXT_INVERTED.name()};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {self.colors.SECONDARY.name()};
            color: {self.colors.TEXT_INVERTED.name()};
        }}
        """
        
        if widget_type == "plano":
            return base_styles + f"""
            QGraphicsView {{
                background-color: {self.colors.BACKGROUND_NEUTRAL.name()};
                border: 1px solid {self.colors.BORDER_MEDIUM.name()};
                border-radius: {self.sizes.BORDER_RADIUS_MEDIUM}px;
            }}
            """
        
        elif widget_type == "tile":
            return base_styles + f"""
            QGraphicsView {{
                background-color: {self.colors.BACKGROUND_DARK.name()};
                border: 1px solid {self.colors.BORDER_MEDIUM.name()};
                border-radius: {self.sizes.BORDER_RADIUS_MEDIUM}px;
            }}
            """
        
        return base_styles
    
    def get_font(self, font_type: str = "default") -> QFont:
        """
        Get font for specific use case.
        
        Args:
            font_type: Type of font to retrieve
            
        Returns:
            Configured QFont
        """
        font = QFont()
        
        if font_type == "title":
            font.setFamily(self.fonts.TITLE_FAMILY)
            font.setPointSize(self.fonts.TITLE)
            font.setWeight(self.fonts.BOLD)
        elif font_type == "heading":
            font.setFamily(self.fonts.PRIMARY_FAMILY)
            font.setPointSize(self.fonts.EXTRA_LARGE)
            font.setWeight(self.fonts.SEMI_BOLD)
        elif font_type == "subheading":
            font.setFamily(self.fonts.PRIMARY_FAMILY)
            font.setPointSize(self.fonts.LARGE)
            font.setWeight(self.fonts.MEDIUM_WEIGHT)
        elif font_type == "monospace":
            font.setFamily(self.fonts.MONOSPACE_FAMILY)
            font.setPointSize(self.fonts.MEDIUM)
        elif font_type == "small":
            font.setFamily(self.fonts.PRIMARY_FAMILY)
            font.setPointSize(self.fonts.SMALL)
        else:  # default
            font.setFamily(self.fonts.PRIMARY_FAMILY)
            font.setPointSize(self.fonts.MEDIUM)
            font.setWeight(self.fonts.NORMAL)
            
        return font


# Global style instance
STYLES = UIStyles()