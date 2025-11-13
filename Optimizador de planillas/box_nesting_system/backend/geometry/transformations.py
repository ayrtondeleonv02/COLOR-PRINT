"""
Geometric transformation functions for coordinate systems and rotations.
"""

import math
from typing import List, Tuple, TYPE_CHECKING

from .types import Point, IPoint, RectCM, BoundingBox
from .utils import cm_to_i, i_to_cm  # Cambiar importación

# Para evitar importaciones circulares
if TYPE_CHECKING:
    from .polygons import OrthoPoly


def rotate_point_90cw(pt: Point) -> Point:
    """
    Rotate point 90° clockwise around origin.
    
    Args:
        pt: Input point
        
    Returns:
        Rotated point
    """
    x, y = pt
    return (y, -x)


def rotate_point_180(pt: Point) -> Point:
    """
    Rotate point 180° around origin.
    
    Args:
        pt: Input point
        
    Returns:
        Rotated point
    """
    x, y = pt
    return (-x, -y)


def rotate_point_270cw(pt: Point) -> Point:
    """
    Rotate point 270° clockwise (90° counter-clockwise) around origin.
    
    Args:
        pt: Input point
        
    Returns:
        Rotated point
    """
    x, y = pt
    return (-y, x)


def rotate_rect_generic(r: RectCM, rot: int) -> RectCM:
    """
    Rotate axis-aligned rectangle by 0/90/180/270 and return resulting AABB.
    
    Args:
        r: Rectangle as (x, y, w, h)
        rot: Rotation angle (multiple of 90)
        
    Returns:
        Rotated rectangle as AABB
        
    Raises:
        ValueError: If rotation is not multiple of 90
    """
    x, y, w, h = r
    corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    rot = rot % 360
    
    if rot == 0:
        rc = corners
    elif rot == 90:
        rc = [rotate_point_90cw(p) for p in corners]
    elif rot == 180:
        rc = [rotate_point_180(p) for p in corners]
    elif rot == 270:
        rc = [rotate_point_270cw(p) for p in corners]
    else:
        raise ValueError("Rotation must be multiple of 90.")
        
    xs = [p[0] for p in rc]
    ys = [p[1] for p in rc]
    minx, miny, maxx, maxy = min(xs), min(ys), max(xs), max(ys)
    return (minx, miny, maxx - minx, maxy - miny)


def rotate_and_align_top_left(poly: 'OrthoPoly', rects: List[Tuple[str, RectCM]], rot: int) -> Tuple['OrthoPoly', List[Tuple[str, RectCM]]]:
    """
    Rotate polygon and rectangles and align AABB to (0,0).
    
    Args:
        poly: Input polygon
        rects: Named rectangles
        rot: Rotation angle (multiple of 90)
        
    Returns:
        Tuple of (rotated_polygon, rotated_rectangles)
    """
    # Importación local para evitar ciclo
    from .polygons import OrthoPoly
    
    poly_r = poly.rotated_copy(rot)
    minx, miny, maxx, maxy = poly_r.aabb()
    poly_r.translate(-minx, -miny)

    new_rects: List[Tuple[str, RectCM]] = []
    for name, r in rects:
        rr = rotate_rect_generic(r, rot)
        new_rects.append((name, (rr[0] - minx, rr[1] - miny, rr[2], rr[3])))
        
    return poly_r, new_rects


def calculate_polygon_area(poly: 'OrthoPoly') -> float:
    """
    Calculate area of orthogonal polygon using shoelace formula.
    
    Args:
        poly: Input polygon
        
    Returns:
        Area in square centimeters
    """
    # Importación local para evitar ciclo
    from .polygons import OrthoPoly
    
    def polygon_area(vertices: List[Point]) -> float:
        n = len(vertices)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += vertices[i][0] * vertices[j][1]
            area -= vertices[j][0] * vertices[i][1]
        return abs(area) / 2.0
    
    area = polygon_area(poly.outer)
    for hole in poly.holes:
        area -= polygon_area(hole)
        
    return area