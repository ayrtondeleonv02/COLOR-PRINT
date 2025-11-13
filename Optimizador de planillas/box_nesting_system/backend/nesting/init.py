"""
Nesting algorithms and optimization for box layout.
"""

from .algorithms import NestingAlgorithms
from .cache import NestingCache
from .optimizer import LayoutOptimizer
from .patterns import TilingPatternGenerator
from .engine import NestingEngine  # NUEVO

__all__ = [
    'NestingAlgorithms',
    'NestingCache', 
    'LayoutOptimizer',
    'TilingPatternGenerator',
    'NestingEngine'  # NUEVO
]