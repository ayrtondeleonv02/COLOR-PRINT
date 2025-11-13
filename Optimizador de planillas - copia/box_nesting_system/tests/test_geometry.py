"""
Tests for geometry operations and transformations.
"""

import pytest
import math
from typing import List, Tuple

from backend.geometry.polygons import OrthoPoly
from backend.geometry.transformations import (
    cm_to_i, i_to_cm, rotate_point_90cw, rotate_point_180,
    rotate_rect_generic, calculate_polygon_area
)
from backend.geometry.types import Point, RectCM
from backend.utils.constants import SCALE_INT


class TestGeometryTransformations:
    """Test cases for geometric transformations."""
    
    def test_cm_to_i_conversion(self):
        """Test centimeter to integer coordinate conversion."""
        # Test basic conversion
        point_cm = (1.5, 2.5)
        point_i = cm_to_i(point_cm)
        assert point_i == (1500, 2500)
        
        # Test rounding
        point_cm = (1.499, 2.501)
        point_i = cm_to_i(point_cm)
        assert point_i == (1499, 2501)
        
    def test_i_to_cm_conversion(self):
        """Test integer to centimeter coordinate conversion."""
        point_i = (1500, 2500)
        point_cm = i_to_cm(point_i)
        assert point_cm == (1.5, 2.5)
        
    def test_rotation_90_clockwise(self):
        """Test 90 degree clockwise rotation."""
        point = (1.0, 0.0)
        rotated = rotate_point_90cw(point)
        expected = (0.0, -1.0)
        assert math.isclose(rotated[0], expected[0], abs_tol=1e-9)
        assert math.isclose(rotated[1], expected[1], abs_tol=1e-9)
        
    def test_rotation_180(self):
        """Test 180 degree rotation."""
        point = (1.0, 2.0)
        rotated = rotate_point_180(point)
        expected = (-1.0, -2.0)
        assert math.isclose(rotated[0], expected[0], abs_tol=1e-9)
        assert math.isclose(rotated[1], expected[1], abs_tol=1e-9)
        
    def test_rectangle_rotation(self):
        """Test rectangle rotation."""
        rect = (0.0, 0.0, 10.0, 5.0)  # x, y, w, h
        
        # 0 degree rotation
        rotated_0 = rotate_rect_generic(rect, 0)
        assert rotated_0 == (0.0, 0.0, 10.0, 5.0)
        
        # 90 degree rotation
        rotated_90 = rotate_rect_generic(rect, 90)
        assert math.isclose(rotated_90[2], 5.0, abs_tol=1e-9)  # width becomes height
        assert math.isclose(rotated_90[3], 10.0, abs_tol=1e-9) # height becomes width


class TestOrthoPoly:
    """Test cases for OrthoPoly class."""
    
    def test_orthopoly_creation(self):
        """Test orthogonal polygon creation."""
        outer = [(0, 0), (10, 0), (10, 5), (0, 5)]
        poly = OrthoPoly(outer)
        
        assert len(poly.outer) == 4
        assert len(poly.holes) == 0
        assert poly.outer == outer
        
    def test_orthopoly_with_holes(self):
        """Test orthogonal polygon with holes."""
        outer = [(0, 0), (10, 0), (10, 10), (0, 10)]
        holes = [[(2, 2), (8, 2), (8, 8), (2, 8)]]
        
        poly = OrthoPoly(outer, holes)
        
        assert len(poly.outer) == 4
        assert len(poly.holes) == 1
        assert poly.holes[0] == holes[0]
        
    def test_aabb_calculation(self):
        """Test axis-aligned bounding box calculation."""
        outer = [(0, 0), (10, 0), (10, 5), (0, 5)]
        poly = OrthoPoly(outer)
        
        aabb = poly.aabb()
        expected = (0.0, 0.0, 10.0, 5.0)
        
        assert aabb == expected
        
    def test_polygon_translation(self):
        """Test polygon translation."""
        outer = [(0, 0), (10, 0), (10, 5), (0, 5)]
        poly = OrthoPoly(outer)
        
        poly.translate(5.0, 3.0)
        
        expected_outer = [(5.0, 3.0), (15.0, 3.0), (15.0, 8.0), (5.0, 8.0)]
        
        for i, (x, y) in enumerate(poly.outer):
            assert math.isclose(x, expected_outer[i][0], abs_tol=1e-9)
            assert math.isclose(y, expected_outer[i][1], abs_tol=1e-9)
            
    def test_polygon_rotation(self):
        """Test polygon rotation."""
        outer = [(0, 0), (10, 0), (10, 5), (0, 5)]
        poly = OrthoPoly(outer)
        
        # Test 90 degree rotation
        rotated = poly.rotated_copy(90)
        aabb = rotated.aabb()
        
        # After 90° rotation, width becomes height and vice versa
        assert math.isclose(aabb[2] - aabb[0], 5.0, abs_tol=1e-9)  # width
        assert math.isclose(aabb[3] - aabb[1], 10.0, abs_tol=1e-9) # height


class TestPolygonArea:
    """Test cases for polygon area calculations."""
    
    def test_rectangle_area(self):
        """Test area calculation for rectangle."""
        outer = [(0, 0), (10, 0), (10, 5), (0, 5)]
        poly = OrthoPoly(outer)
        
        area = calculate_polygon_area(poly)
        expected_area = 50.0  # 10 * 5
        
        assert math.isclose(area, expected_area, abs_tol=1e-9)
        
    def test_polygon_with_hole_area(self):
        """Test area calculation for polygon with hole."""
        outer = [(0, 0), (10, 0), (10, 10), (0, 10)]
        hole = [(2, 2), (8, 2), (8, 8), (2, 8)]
        poly = OrthoPoly(outer, [hole])
        
        area = calculate_polygon_area(poly)
        outer_area = 100.0  # 10 * 10
        hole_area = 36.0    # 6 * 6
        expected_area = outer_area - hole_area
        
        assert math.isclose(area, expected_area, abs_tol=1e-9)


class TestIntegration:
    """Integration tests for geometry operations."""
    
    def test_round_trip_conversion(self):
        """Test round-trip conversion between cm and integer coordinates."""
        original_point = (1.234, 5.678)
        
        # Convert to integer and back
        int_point = cm_to_i(original_point)
        round_trip_point = i_to_cm(int_point)
        
        # Should be very close to original (within rounding error)
        assert math.isclose(original_point[0], round_trip_point[0], abs_tol=0.001)
        assert math.isclose(original_point[1], round_trip_point[1], abs_tol=0.001)
        
    def test_rotation_preserves_area(self):
        """Test that rotation preserves polygon area."""
        outer = [(0, 0), (10, 0), (10, 5), (0, 5)]
        poly = OrthoPoly(outer)
        
        original_area = calculate_polygon_area(poly)
        
        # Rotate and check area is preserved
        for rotation in [90, 180, 270]:
            rotated = poly.rotated_copy(rotation)
            rotated_area = calculate_polygon_area(rotated)
            
            assert math.isclose(original_area, rotated_area, abs_tol=1e-9)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])