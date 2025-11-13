"""
Geometry module for box nesting optimization system.
"""

from .polygons import OrthoPoly
from .transformations import rotate_and_align_top_left, rotate_rect_generic
from .collision import polygons_intersect
from .types import Point, RectCM, BoundingBox
from .render_helpers import vertices_externos_px, build_tile_orthopoly_and_edges_cm

__all__ = [
    'OrthoPoly',
    'rotate_and_align_top_left',
    'rotate_rect_generic', 
    'polygons_intersect',
    'Point',
    'RectCM',
    'BoundingBox',
    'vertices_externos_px',
    'build_tile_orthopoly_and_edges_cm'
]