"""
Production planning and optimization models.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class OptimizationObjective(Enum):
    """Optimization objectives for nesting."""
    MINIMIZE_WIDTH = "width"
    MINIMIZE_HEIGHT = "height"
    MINIMIZE_AREA = "area"
    MAXIMIZE_EFFICIENCY = "efficiency"


class LayoutStrategy(Enum):
    """Layout selection strategies."""
    MINIMUM_LAYOUT = "minimum"
    MAXIMUM_LAYOUT = "maximum"
    INTERMEDIATE_LAYOUT = "intermediate"
    CUSTOM_LAYOUT = "custom"


@dataclass
class ProductionParameters:
    """Parameters for production planning and optimization."""
    
    # Production requirements
    volumen: int = 0  # Total pieces required
    tiros_minimos: int = 0  # Minimum number of shots
    max_tiros: Optional[int] = None  # Maximum number of shots (optional)
    
    # Material constraints
    material_width: Optional[float] = None  # Available material width
    material_height: Optional[float] = None  # Available material height
    material_cost_per_cm2: Optional[float] = None  # Material cost
    
    # Time constraints
    tiempo_por_tiro: float = 1.0  # Time per shot in hours
    tiempo_maximo: Optional[float] = None  # Maximum available time
    
    # Optimization preferences
    objetivo: OptimizationObjective = OptimizationObjective.MINIMIZE_WIDTH
    estrategia: LayoutStrategy = LayoutStrategy.INTERMEDIATE_LAYOUT
    priorizar_velocidad: bool = False  # Prioritize speed over material usage
    
    def validate(self) -> Tuple[bool, str]:
        """
        Validate production parameters.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.volumen < 0:
            return False, "Volume cannot be negative"
        if self.tiros_minimos < 0:
            return False, "Minimum shots cannot be negative"
        if self.tiempo_por_tiro <= 0:
            return False, "Time per shot must be positive"
            
        if self.max_tiros is not None and self.max_tiros <= 0:
            return False, "Maximum shots must be positive if specified"
        if self.tiempo_maximo is not None and self.tiempo_maximo <= 0:
            return False, "Maximum time must be positive if specified"
        if self.material_cost_per_cm2 is not None and self.material_cost_per_cm2 < 0:
            return False, "Material cost cannot be negative"
            
        return True, "Production parameters are valid"

    def calculate_production_metrics(self, tiles_per_shot: int, 
                                   area_per_shot: float) -> Dict[str, Any]:
        """
        Calculate production metrics based on layout.
        
        Args:
            tiles_per_shot: Number of tiles per shot
            area_per_shot: Area used per shot
            
        Returns:
            Dictionary with production metrics
        """
        if tiles_per_shot <= 0:
            return {
                'tiros_necesarios': 0,
                'tiempo_total': 0.0,
                'area_total': 0.0,
                'costo_total': 0.0,
                'efficiency': 0.0
            }
            
        tiros_necesarios = max(1, (self.volumen + tiles_per_shot - 1) // tiles_per_shot)
        
        # Apply minimum/maximum shot constraints
        if self.tiros_minimos > 0:
            tiros_necesarios = max(tiros_necesarios, self.tiros_minimos)
        if self.max_tiros is not None:
            tiros_necesarios = min(tiros_necesarios, self.max_tiros)
            
        tiempo_total = tiros_necesarios * self.tiempo_por_tiro
        area_total = tiros_necesarios * area_per_shot
        
        costo_total = 0.0
        if self.material_cost_per_cm2 is not None:
            costo_total = area_total * self.material_cost_per_cm2
            
        # Calculate time efficiency
        tiempo_efficiency = 1.0
        if self.tiempo_maximo is not None and self.tiempo_maximo > 0:
            tiempo_efficiency = min(1.0, self.tiempo_maximo / tiempo_total)
            
        return {
            'tiros_necesarios': tiros_necesarios,
            'tiempo_total': tiempo_total,
            'area_total': area_total,
            'costo_total': costo_total,
            'tiempo_efficiency': tiempo_efficiency,
            'tiles_per_shot': tiles_per_shot,
            'area_per_shot': area_per_shot
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'volumen': self.volumen,
            'tiros_minimos': self.tiros_minimos,
            'max_tiros': self.max_tiros,
            'material_width': self.material_width,
            'material_height': self.material_height,
            'material_cost_per_cm2': self.material_cost_per_cm2,
            'tiempo_por_tiro': self.tiempo_por_tiro,
            'tiempo_maximo': self.tiempo_maximo,
            'objetivo': self.objetivo.value,
            'estrategia': self.estrategia.value,
            'priorizar_velocidad': self.priorizar_velocidad
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProductionParameters':
        """Create from dictionary."""
        return cls(
            volumen=data.get('volumen', 0),
            tiros_minimos=data.get('tiros_minimos', 0),
            max_tiros=data.get('max_tiros'),
            material_width=data.get('material_width'),
            material_height=data.get('material_height'),
            material_cost_per_cm2=data.get('material_cost_per_cm2'),
            tiempo_por_tiro=data.get('tiempo_por_tiro', 1.0),
            tiempo_maximo=data.get('tiempo_maximo'),
            objetivo=OptimizationObjective(data.get('objetivo', 'width')),
            estrategia=LayoutStrategy(data.get('estrategia', 'intermediate')),
            priorizar_velocidad=data.get('priorizar_velocidad', False)
        )


@dataclass
class OptimizationConstraints:
    """Constraints for layout optimization."""
    
    # Bed constraints
    bed_width: float
    bed_height: float
    
    # Tile constraints
    max_tiles_x: int = 100
    max_tiles_y: int = 100
    min_tiles_x: int = 1
    min_tiles_y: int = 1
    
    # Separation constraints
    min_medianil_x: float = 0.0
    max_medianil_x: float = 10.0
    min_medianil_y: float = 0.0
    max_medianil_y: float = 10.0
    
    # Clearance constraints
    min_clearance: float = 0.0
    max_clearance: float = 5.0
    
    # Search constraints
    max_search_iterations: int = 1000
    search_tolerance: float = 0.01
    
    def validate(self) -> Tuple[bool, str]:
        """Validate optimization constraints."""
        if self.bed_width <= 0 or self.bed_height <= 0:
            return False, "Bed dimensions must be positive"
        if self.max_tiles_x < self.min_tiles_x:
            return False, "Max tiles X must be >= min tiles X"
        if self.max_tiles_y < self.min_tiles_y:
            return False, "Max tiles Y must be >= min tiles Y"
        if self.max_medianil_x < self.min_medianil_x:
            return False, "Max medianil X must be >= min medianil X"
        if self.max_medianil_y < self.min_medianil_y:
            return False, "Max medianil Y must be >= min medianil Y"
        if self.max_clearance < self.min_clearance:
            return False, "Max clearance must be >= min clearance"
            
        return True, "Constraints are valid"