"""
Helper functions for rendering and visualization geometry operations.
"""

from typing import List, Dict, Tuple
from backend.models.parameters import PlanoParams
from .polygons import OrthoPoly
from .types import RectCM


def vertices_externos_px(shapes: List[Dict]) -> List[Tuple[float, float]]:
    """
    Calculate external vertices from shapes in pixel coordinates.
    
    Args:
        shapes: List of shape dictionaries
        
    Returns:
        List of (x, y) coordinate tuples
    """
    verts_set = set()
    
    def add(x: float, y: float):
        verts_set.add((round(x), round(y)))
        
    for shp in shapes:
        name = shp['name']
        x, y, w, h = shp['x'], shp['y'], shp['w'], shp['h']
        
        if name == 'Cara1': 
            add(x, y)
            add(x, y + h)
        elif name == 'Cara4': 
            add(x + w, y)
            add(x + w, y + h)
        elif name.startswith('CejaSup') and w > 0: 
            add(x, y)
            add(x + w, y)
        elif name.startswith('CejaInf') and w > 0: 
            add(x, y + h)
            add(x + w, y + h)
        elif name.startswith('CejaLat'):
            add(x, y)
            add(x + w, y)
            add(x + w, y + h)
            add(x, y + h)
            
    return [(float(ix), float(iy)) for (ix, iy) in verts_set]


def build_tile_orthopoly_and_edges_cm(p: PlanoParams) -> Tuple[OrthoPoly, List[Tuple[str, RectCM]]]:
    """
    Build orthogonal polygon and named rectangles from parameters.
    
    Args:
        p: Box parameters
        
    Returns:
        Tuple of (polygon, named_rectangles)
    """
    from backend.models.parameters import rects_cm_from_params
    
    rects = rects_cm_from_params(p)
    rects_only = [r for _, r in rects]
    poly = OrthoPoly.from_rects_cm(rects_only)
    return poly, rects