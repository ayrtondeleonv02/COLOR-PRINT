"""
Validation functions for the Box Nesting Optimization System.
"""

import math
from typing import Tuple, Optional
from backend.models.parameters import PlanoParams
from backend.models.production import ProductionParameters


def validate_bed_limits(x_min: float, x_max: float, y_min: float, y_max: float, 
                       margins: Optional[dict] = None) -> Tuple[bool, str]:
    """
    Validate bed limits with optional margins.
    
    Args:
        x_min: Minimum X coordinate
        x_max: Maximum X coordinate
        y_min: Minimum Y coordinate
        y_max: Maximum Y coordinate
        margins: Optional margin dictionary
        
    Returns:
        Tuple of (is_valid, message)
    """
    if x_min >= x_max:
        return False, "X minimum must be less than X maximum"
    if y_min >= y_max:
        return False, "Y minimum must be less than Y maximum"
    if x_min < 0 or y_min < 0:
        return False, "Coordinates cannot be negative"
        
    # Apply margins if provided
    if margins:
        sangria_izquierda = margins.get('sangria_izquierda', 0.0)
        sangria_derecha = margins.get('sangria_derecha', 0.0)
        pinza = margins.get('pinza', 0.0)
        contra_pinza = margins.get('contra_pinza', 0.0)
        
        x_min_eff = x_min + sangria_izquierda
        x_max_eff = x_max - sangria_derecha
        y_min_eff = y_min + pinza
        y_max_eff = y_max - contra_pinza
        
        if x_min_eff >= x_max_eff:
            return False, "Effective X range invalid after applying margins"
        if y_min_eff >= y_max_eff:
            return False, "Effective Y range invalid after applying margins"
            
    return True, "Bed limits are valid"


def validate_tile_counts(tiles_x: int, tiles_y: int, 
                        max_x: int = 100, max_y: int = 100) -> Tuple[bool, str]:
    """
    Validate tile counts.
    
    Args:
        tiles_x: Number of tiles in X direction
        tiles_y: Number of tiles in Y direction
        max_x: Maximum allowed tiles in X
        max_y: Maximum allowed tiles in Y
        
    Returns:
        Tuple of (is_valid, message)
    """
    if tiles_x < 1:
        return False, "Must have at least 1 tile in X direction"
    if tiles_y < 1:
        return False, "Must have at least 1 tile in Y direction"
    if tiles_x > max_x:
        return False, f"Too many tiles in X direction (max: {max_x})"
    if tiles_y > max_y:
        return False, f"Too many tiles in Y direction (max: {max_y})"
        
    return True, "Tile counts are valid"


def validate_production_parameters(volumen: int, tiros_minimos: int) -> Tuple[bool, str]:
    """
    Validate production parameters.
    
    Args:
        volumen: Production volume
        tiros_minimos: Minimum shots
        
    Returns:
        Tuple of (is_valid, message)
    """
    if volumen < 0:
        return False, "Volume cannot be negative"
    if tiros_minimos < 0:
        return False, "Minimum shots cannot be negative"
    if volumen == 0 and tiros_minimos > 0:
        return False, "Cannot have minimum shots with zero volume"
        
    return True, "Production parameters are valid"


def validate_plano_params(params: PlanoParams) -> Tuple[bool, str]:
    """
    Validate plano parameters using the built-in method.
    
    Args:
        params: PlanoParams instance
        
    Returns:
        Tuple of (is_valid, message)
    """
    return params.validate()


def validate_nesting_parameters(paso_x: float, paso_y: float, 
                               clearance: float) -> Tuple[bool, str]:
    """
    Validate nesting algorithm parameters.
    
    Args:
        paso_x: X search step
        paso_y: Y search step
        clearance: Clearance between tiles
        
    Returns:
        Tuple of (is_valid, message)
    """
    if paso_x <= 0 or paso_y <= 0:
        return False, "Search steps must be positive"
    if clearance < 0:
        return False, "Clearance cannot be negative"
    if paso_x > 10.0 or paso_y > 10.0:
        return False, "Search steps too large (max: 10.0)"
        
    return True, "Nesting parameters are valid"