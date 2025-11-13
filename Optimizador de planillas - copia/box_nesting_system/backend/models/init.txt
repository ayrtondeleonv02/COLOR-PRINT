"""
Data models for the Box Nesting Optimization System.
"""

from .parameters import PlanoParams, rects_cm_from_params, construir_shapes_px
from .production import ProductionParameters, OptimizationConstraints

__all__ = [
    'PlanoParams',
    'rects_cm_from_params', 
    'construir_shapes_px',
    'ProductionParameters',
    'OptimizationConstraints'
]