"""
Utility functions for coordinate conversions and basic operations.
"""

from backend.utils.constants import SCALE_INT
from .types import Point, IPoint


def cm_to_i(pt: Point) -> IPoint:
    """
    Convert centimeter coordinates to integer coordinates.
    
    Args:
        pt: Point in centimeters
        
    Returns:
        Point in integer coordinates (scaled by SCALE_INT)
    """
    return (int(round(pt[0] * SCALE_INT)), int(round(pt[1] * SCALE_INT)))


def i_to_cm(pt: IPoint) -> Point:
    """
    Convert integer coordinates to centimeter coordinates.
    
    Args:
        pt: Point in integer coordinates
        
    Returns:
        Point in centimeters
    """
    return (pt[0] / SCALE_INT, pt[1] / SCALE_INT)