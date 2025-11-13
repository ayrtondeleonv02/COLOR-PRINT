"""
Collision detection functions for geometric operations.
"""

import pyclipper
from typing import List

from .polygons import OrthoPoly
from .types import Point


def polygons_intersect(polyA: OrthoPoly, polyB: OrthoPoly, clearance_cm: float = 0.0) -> bool:
    """
    Check polygon-polygon collision with clearance support.
    
    Args:
        polyA: First polygon
        polyB: Second polygon  
        clearance_cm: Minimum separation distance (>0)
        
    Returns:
        True if polygons intersect (considering clearance)
    """
    pathsA = polyA.offset_paths_i(clearance_cm) if clearance_cm != 0.0 else polyA.to_paths_i()
    pathsB = polyB.to_paths_i()
    
    if not pathsA or not pathsB:
        return False
        
    pc = pyclipper.Pyclipper()
    pc.AddPaths(pathsA, pyclipper.PT_SUBJECT, True)
    pc.AddPaths(pathsB, pyclipper.PT_CLIP, True)
    inter = pc.Execute(pyclipper.CT_INTERSECTION, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO)
    
    return len(inter) > 0


def calculate_minimum_clearance(polyA: OrthoPoly, polyB: OrthoPoly, max_clearance: float = 10.0) -> float:
    """
    Calculate minimum clearance between two polygons using binary search.
    
    Args:
        polyA: First polygon
        polyB: Second polygon
        max_clearance: Maximum clearance to test
        
    Returns:
        Minimum clearance where polygons don't intersect
    """
    if not polygons_intersect(polyA, polyB, 0.0):
        return 0.0
    
    low, high = 0.0, max_clearance
    tolerance = 0.01
    
    while high - low > tolerance:
        mid = (low + high) / 2
        if polygons_intersect(polyA, polyB, mid):
            low = mid
        else:
            high = mid
            
    return high