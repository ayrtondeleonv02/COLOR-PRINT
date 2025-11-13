"""
Orthogonal polygon class with robust geometric operations.
"""

import pyclipper
import logging
from typing import List, Optional, Tuple, Dict, Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainterPath
from PySide6.QtWidgets import QGraphicsScene

from .types import Point, IPoint, RectCM, BoundingBox, PolygonData
from .utils import cm_to_i, i_to_cm  # Cambiar importación
from backend.utils.constants import SCALE_INT

class OrthoPoly:
    """
    Represents an orthogonal polygon with robust geometric operations.
    
    Outer polygon is CCW (Counter-Clockwise), holes are CW (Clockwise) as recommended.
    
    Attributes:
        outer (List[Point]): Outer boundary in centimeters
        holes (List[List[Point]]): Internal holes in centimeters
    """
    
    def __init__(self, outer: List[Point], holes: Optional[List[List[Point]]] = None):
        """
        Initialize orthogonal polygon.
        
        Args:
            outer: Outer boundary points (CCW)
            holes: Optional list of holes (CW)
        """
        self.outer = outer[:]  # cm
        self.holes = holes[:] if holes else []  # cm

    @staticmethod
    def from_rects_cm(rects_cm: List[RectCM]) -> "OrthoPoly":
        """
        Robust union of rectangles (x,y,w,h in cm) using pyclipper (integer coordinates).
        
        Args:
            rects_cm: List of rectangles as (x, y, w, h)
            
        Returns:
            OrthoPoly: Unified polygon from rectangle union
        """
        paths: List[List[IPoint]] = []
        for x, y, w, h in rects_cm:
            x2, y2 = x + w, y + h
            p = [cm_to_i((x, y)), cm_to_i((x2, y)), cm_to_i((x2, y2)), cm_to_i((x, y2))]
            paths.append(p)

        pc = pyclipper.Pyclipper()
        pc.AddPaths(paths, pyclipper.PT_SUBJECT, True)
        sol = pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO)

        if not sol:
            return OrthoPoly([], [])

        sol = sorted(sol, key=lambda p: abs(pyclipper.Area(p)), reverse=True)
        outer = [i_to_cm(pt) for pt in sol[0]]
        holes = [[i_to_cm(pt) for pt in p] for p in sol[1:]]
        return OrthoPoly(outer, holes)

    def aabb(self) -> BoundingBox:
        """
        Calculate axis-aligned bounding box.
        
        Returns:
            BoundingBox: (min_x, min_y, max_x, max_y)
        """
        xs = [p[0] for p in self.outer]
        ys = [p[1] for p in self.outer]
        return (min(xs), min(ys), max(xs), max(ys))

    def translate(self, dx: float, dy: float) -> None:
        """
        Translate polygon by given offsets.
        
        Args:
            dx: X offset in cm
            dy: Y offset in cm
        """
        self.outer = [(x + dx, y + dy) for x, y in self.outer]
        self.holes = [[(x + dx, y + dy) for x, y in h] for h in self.holes]

    def rotated_copy(self, rot: int) -> "OrthoPoly":
        """
        Create a rotated copy of the polygon.
        
        Args:
            rot: Rotation angle (multiple of 90)
            
        Returns:
            OrthoPoly: Rotated copy
            
        Raises:
            ValueError: If rotation is not multiple of 90
        """
        # Importación local para evitar ciclo
        from .transformations import rotate_point_90cw, rotate_point_180, rotate_point_270cw
        
        rot = rot % 360
        if rot == 0:
            return OrthoPoly(self.outer[:], [h[:] for h in self.holes])
        elif rot == 90:
            return OrthoPoly([rotate_point_90cw(p) for p in self.outer],
                             [[rotate_point_90cw(p) for p in h] for h in self.holes])
        elif rot == 180:
            return OrthoPoly([rotate_point_180(p) for p in self.outer],
                             [[rotate_point_180(p) for p in h] for h in self.holes])
        elif rot == 270:
            return OrthoPoly([rotate_point_270cw(p) for p in self.outer],
                             [[rotate_point_270cw(p) for p in h] for h in self.holes])
        else:
            raise ValueError("Rotation must be multiple of 90 degrees")

    def to_paths_i(self) -> List[List[IPoint]]:
        """
        Convert to integer coordinate paths for pyclipper.
        
        Returns:
            List of paths in integer coordinates
        """
        paths: List[List[IPoint]] = []
        if self.outer:
            paths.append([cm_to_i(p) for p in self.outer])
        for h in self.holes:
            paths.append([cm_to_i(p) for p in h])
        return paths

    def offset_paths_i(self, delta_cm: float) -> List[List[IPoint]]:
        """
        Apply offset (margin) to paths.
        
        Args:
            delta_cm: Offset distance in cm (>0 expands outer, contracts holes)
            
        Returns:
            List of offset paths in integer coordinates
        """
        pco = pyclipper.PyclipperOffset(miter_limit=2.0, arc_tolerance=0.0)
        if self.outer:
            pco.AddPath([cm_to_i(p) for p in self.outer], pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
        for h in self.holes:
            pco.AddPath([cm_to_i(p) for p in h], pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
        return pco.Execute(delta_cm * SCALE_INT)

    def to_qpath(self, px_per_cm: float, fill_rule_odd_even: bool = True) -> QPainterPath:
        """
        Convert to QPainterPath for Qt rendering.
        
        Args:
            px_per_cm: Pixels per centimeter scale
            fill_rule_odd_even: Use odd-even fill rule if True
            
        Returns:
            QPainterPath for rendering
        """
        path = QPainterPath()
        
        def add_loop(loop: List[Point]):
            if not loop:
                return
            x0, y0 = loop[0]
            path.moveTo(x0 * px_per_cm, y0 * px_per_cm)
            for x, y in loop[1:]:
                path.lineTo(x * px_per_cm, y * px_per_cm)
            path.closeSubpath()
            
        add_loop(self.outer)
        for h in self.holes:
            add_loop(h)
            
        path.setFillRule(Qt.OddEvenFill if fill_rule_odd_even else Qt.WindingFill)
        return path

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"OrthoPoly(outer_points={len(self.outer)}, holes={len(self.holes)})"