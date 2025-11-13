"""
Type definitions for geometric operations.
"""

from typing import List, Tuple, Dict, Any, Optional, Union
from dataclasses import dataclass

# Basic geometric types
Point = Tuple[float, float]
IPoint = Tuple[int, int]
RectCM = Tuple[float, float, float, float]  # x, y, w, h (cm)
BoundingBox = Tuple[float, float, float, float]  # min_x, min_y, max_x, max_y

# Complex type definitions
PolygonData = Tuple[List[Point], List[List[Point]]]  # (outer, holes)

@dataclass
class NestingResult:
    """Result of nesting algorithm calculation."""
    x: float
    y: float
    rotation: int
    rectangles: List[Tuple[str, RectCM]]
    polygon_template: Any  # OrthoPoly type
    global_width: float
    global_height: float
    global_area: float

@dataclass
class PatternData:
    """Data structure for tiling patterns."""
    poly1: Any  # OrthoPoly
    rects1: List[Tuple[str, RectCM]]
    poly2T: Any  # OrthoPoly  
    rects2T: List[Tuple[str, RectCM]]
    poly3T: Any  # OrthoPoly
    rects3T: List[Tuple[str, RectCM]]
    dx2: float
    dy2: float
    dx3: float
    dy3: float
    rot1: int
    rot2: int
    paso_y: float
    paso_x: float
    clearance_cm: float
    objective: str

# Type aliases for clarity
ShapeDict = Dict[str, Any]
NestingCacheKey = Tuple[Any, ...]
SearchDomain = Tuple[Tuple[float, float], Tuple[float, float]]