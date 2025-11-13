"""
Data models for box parameters and configuration.
"""

from typing import List, Tuple, Dict, Any
from dataclasses import dataclass, field


@dataclass
class PlanoParams:
    """
    Parameters for box geometry and rendering.
    
    Represents all configurable parameters for box design and visualization.
    """
    # Base measures (cm)
    L: float = 15.0
    A: float = 10.0
    h: float = 6.0
    cIzq: float = 1.5
    cDer: float = 0.0

    # Arrays per face (cm), indices 0..3
    Tapas: List[float] = field(default_factory=lambda: [0, 3.0, 0, 0])
    CSup: List[float] = field(default_factory=lambda: [1.5, 1.5, 1.5, 0])
    Bases: List[float] = field(default_factory=lambda: [3.0, 2.0, 3.0, 2.0])
    CInf: List[float] = field(default_factory=lambda: [0, 0, 0, 0])

    # Render (px)
    escala: float = 10.0  # px per cm
    x0: float = 100.0    # (only for Editor tab)
    y0: float = 200.0

    def validate(self) -> Tuple[bool, str]:
        """
        Validate parameters for consistency and physical feasibility.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for positive dimensions
        if self.L <= 0:
            return False, "L must be positive"
        if self.A <= 0:
            return False, "A must be positive"
        if self.h <= 0:
            return False, "h must be positive"

        # Check flange dimensions are non-negative
        if any(t < 0 for t in self.Tapas):
            return False, "Tapas cannot be negative"
        if any(c < 0 for c in self.CSup):
            return False, "CSup cannot be negative"
        if any(b < 0 for b in self.Bases):
            return False, "Bases cannot be negative"
        if any(c < 0 for c in self.CInf):
            return False, "CInf cannot be negative"

        # Check array lengths
        if len(self.Tapas) != 4:
            return False, "Tapas must have exactly 4 elements"
        if len(self.CSup) != 4:
            return False, "CSup must have exactly 4 elements"
        if len(self.Bases) != 4:
            return False, "Bases must have exactly 4 elements"
        if len(self.CInf) != 4:
            return False, "CInf must have exactly 4 elements"

        # Check render parameters
        if self.escala <= 0:
            return False, "escala must be positive"
        if self.x0 < 0 or self.y0 < 0:
            return False, "x0 and y0 cannot be negative"

        return True, "Parameters are valid"

    def copy(self) -> 'PlanoParams':
        """Create a deep copy of these parameters."""
        return PlanoParams(
            L=self.L,
            A=self.A,
            h=self.h,
            cIzq=self.cIzq,
            cDer=self.cDer,
            Tapas=self.Tapas.copy(),
            CSup=self.CSup.copy(),
            Bases=self.Bases.copy(),
            CInf=self.CInf.copy(),
            escala=self.escala,
            x0=self.x0,
            y0=self.y0
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary for serialization."""
        return {
            'L': self.L,
            'A': self.A,
            'h': self.h,
            'cIzq': self.cIzq,
            'cDer': self.cDer,
            'Tapas': self.Tapas.copy(),
            'CSup': self.CSup.copy(),
            'Bases': self.Bases.copy(),
            'CInf': self.CInf.copy(),
            'escala': self.escala,
            'x0': self.x0,
            'y0': self.y0
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlanoParams':
        """Create parameters from dictionary."""
        return cls(
            L=data.get('L', 15.0),
            A=data.get('A', 10.0),
            h=data.get('h', 6.0),
            cIzq=data.get('cIzq', 1.5),
            cDer=data.get('cDer', 0.0),
            Tapas=data.get('Tapas', [0, 3.0, 0, 0]),
            CSup=data.get('CSup', [1.5, 1.5, 1.5, 0]),
            Bases=data.get('Bases', [3.0, 2.0, 3.0, 2.0]),
            CInf=data.get('CInf', [0, 0, 0, 0]),
            escala=data.get('escala', 10.0),
            x0=data.get('x0', 100.0),
            y0=data.get('y0', 200.0)
        )

    def __str__(self) -> str:
        """String representation for debugging."""
        return (
            f"PlanoParams(L={self.L}, A={self.A}, h={self.h}, "
            f"cIzq={self.cIzq}, cDer={self.cDer}, "
            f"escala={self.escala})"
        )


def rects_cm_from_params(p: PlanoParams) -> List[Tuple[str, Tuple[float, float, float, float]]]:
    """
    Generate named rectangles from box parameters.
    
    Args:
        p: Box parameters
        
    Returns:
        List of (name, rectangle) tuples where rectangle is (x, y, w, h)
    """
    rects = []
    x0, y0 = 0.0, 0.0
    curX = x0
    
    for i in range(4):
        cara_idx = i + 1
        wPanel = p.L if (cara_idx % 2 == 1) else p.A
        
        rects.append((f'Cara{cara_idx}', (curX, y0, wPanel, p.h)))
        rects.append((f'Tapa{cara_idx}', (curX, y0 - p.Tapas[i], wPanel, p.Tapas[i])))
        rects.append((f'CejaSup{cara_idx}', (curX, y0 - (p.Tapas[i] + p.CSup[i]), wPanel, p.CSup[i])))
        rects.append((f'Base{cara_idx}', (curX, y0 + p.h, wPanel, p.Bases[i])))
        rects.append((f'CejaInf{cara_idx}', (curX, y0 + p.h + p.Bases[i], wPanel, p.CInf[i])))
        
        curX += wPanel
        
    rects.append(('CejaLatIzq', (x0 - p.cIzq, y0, p.cIzq, p.h)))
    rects.append(('CejaLatDer', (curX, y0, p.cDer, p.h)))
    
    return rects


def construir_shapes_px(params: PlanoParams) -> List[Dict[str, Any]]:
    """
    Build shapes in pixel coordinates for rendering.
    
    Args:
        params: Box parameters
        
    Returns:
        List of shape dictionaries for rendering
    """
    shapes = []
    verde = (0, 150, 0)
    rojo1 = (150, 0, 0)
    rojo2 = (200, 0, 0)
    
    x0, y0, s = params.x0, params.y0, params.escala
    L, A, h = params.L, params.A, params.h
    curX = x0
    
    for i in range(4):
        cara_idx = i + 1
        wPanel = L if (cara_idx % 2 == 1) else A
        
        shapes.append({
            'name': f'Cara{cara_idx}',
            'x': curX,
            'y': y0,
            'w': wPanel * s,
            'h': h * s,
            'color': verde
        })
        
        shapes.append({
            'name': f'Tapa{cara_idx}',
            'x': curX,
            'y': y0 - params.Tapas[i] * s,
            'w': wPanel * s,
            'h': params.Tapas[i] * s,
            'color': rojo1
        })
        
        shapes.append({
            'name': f'CejaSup{cara_idx}',
            'x': curX,
            'y': y0 - (params.Tapas[i] + params.CSup[i]) * s,
            'w': wPanel * s,
            'h': params.CSup[i] * s,
            'color': rojo2
        })
        
        shapes.append({
            'name': f'Base{cara_idx}',
            'x': curX,
            'y': y0 + h * s,
            'w': wPanel * s,
            'h': params.Bases[i] * s,
            'color': rojo1
        })
        
        shapes.append({
            'name': f'CejaInf{cara_idx}',
            'x': curX,
            'y': y0 + (h + params.Bases[i]) * s,
            'w': wPanel * s,
            'h': params.CInf[i] * s,
            'color': rojo2
        })
        
        curX += wPanel * s
        
    shapes.append({
        'name': 'CejaLatIzq',
        'x': x0 - params.cIzq * s,
        'y': y0,
        'w': params.cIzq * s,
        'h': h * s,
        'color': rojo2
    })
    
    shapes.append({
        'name': 'CejaLatDer',
        'x': curX,
        'y': y0,
        'w': params.cDer * s,
        'h': h * s,
        'color': rojo2
    })
    
    return shapes