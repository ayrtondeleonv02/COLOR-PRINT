"""
Tests for nesting algorithms and optimization.
"""

import pytest
from typing import List, Dict, Any

from backend.nesting.algorithms import NestingAlgorithms
from backend.nesting.cache import NestingCache
from backend.nesting.optimizer import LayoutOptimizer
from backend.geometry.polygons import OrthoPoly
from backend.geometry.types import Point
from backend.models.parameters import PlanoParams
from backend.models.production import ProductionParameters


class TestNestingCache:
    """Test cases for nesting cache functionality."""
    
    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = NestingCache(max_size=10)
        
        assert cache.max_size == 10
        assert len(cache.cache) == 0
        assert cache.hit_count == 0
        assert cache.miss_count == 0
        
    def test_cache_store_and_retrieve(self):
        """Test storing and retrieving from cache."""
        cache = NestingCache()
        test_data = {"key": "value"}
        cache_key = "test_key"
        
        # Store data
        cache.store(test_data, cache_key)
        
        # Retrieve data
        retrieved = cache.get(cache_key)
        
        assert retrieved == test_data
        assert cache.hit_count == 1
        
    def test_cache_invalidation(self):
        """Test cache invalidation."""
        cache = NestingCache()
        test_data = {"key": "value"}
        cache_key = "test_key"
        
        cache.store(test_data, cache_key)
        
        # Initially should be valid
        assert cache.is_valid(cache_key) == True
        
        # Different key should be invalid
        assert cache.is_valid("different_key") == False
        
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = NestingCache(max_size=2)
        
        # Fill cache
        cache.store("data1", "key1")
        cache.store("data2", "key2")
        
        assert len(cache.cache) == 2
        
        # Access key1 to make it more recently used
        cache.get("key1")
        
        # Add third item, should evict key2 (least recently used)
        cache.store("data3", "key3")
        
        assert len(cache.cache) == 2
        assert "key1" in cache.cache
        assert "key3" in cache.cache
        assert "key2" not in cache.cache


class TestNestingAlgorithms:
    """Test cases for nesting algorithms."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.algorithms = NestingAlgorithms()
        self.simple_poly = OrthoPoly([(0, 0), (10, 0), (10, 5), (0, 5)])
        
    def test_search_domain_calculation(self):
        """Test search domain calculation."""
        poly1 = OrthoPoly([(0, 0), (10, 0), (10, 5), (0, 5)])
        w2, h2 = 8.0, 4.0
        
        (x_min, x_max), (y_min, y_max) = self.algorithms._search_domain_without_bed(
            poly1, w2, h2
        )
        
        # X should range from 0 to combined width
        assert x_min == 0.0
        assert x_max == 18.0  # 10 + 8
        
        # Y should allow for placement above and below
        assert y_min == -4.0  # -h2
        assert y_max == 5.0   # h1
        
    def test_template_orientation(self):
        """Test template creation for different orientations."""
        poly = OrthoPoly([(0, 0), (10, 0), (10, 5), (0, 5)])
        rects = [("test", (0, 0, 10, 5))]
        
        # Test 0 degree orientation
        poly_0, rects_0, w0, h0 = self.algorithms._make_template_for_orientation(
            poly, rects, 0
        )
        
        assert w0 == 10.0
        assert h0 == 5.0
        
        # Test 180 degree orientation
        poly_180, rects_180, w180, h180 = self.algorithms._make_template_for_orientation(
            poly, rects, 180
        )
        
        # Dimensions should be the same after rotation
        assert w180 == 10.0
        assert h180 == 5.0


class TestLayoutOptimizer:
    """Test cases for layout optimization."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.optimizer = LayoutOptimizer()
        
    def test_production_metrics_calculation(self):
        """Test production metrics calculation."""
        metrics = {
            'tiles_x_min': 1,
            'tiles_y_min': 1,
            'tiles_x_max': 3,
            'tiles_y_max': 2,
            'planos_min': 1,
            'planos_max': 6,
            'volumen': 10,
            'tiros_minimos': 2
        }
        
        # Mock scene for testing
        class MockScene:
            def calculate_global_bbox(self, *args):
                return (0, 0, 100, 100)
                
        scene = MockScene()
        
        result = self.optimizer.optimize_production_layout(
            scene=scene,
            volumen=10,
            tiros_minimos=2,
            x_min_roland=50,
            x_max_roland=200,
            y_min_roland=50,
            y_max_roland=200,
            medianil_x=0.0,
            medianil_y=0.0,
            objective="width"
        )
        
        assert 'success' in result
        assert 'tiles_x' in result
        assert 'tiles_y' in result
        
    def test_layout_comparison(self):
        """Test layout comparison functionality."""
        layout_a = {
            'success': True,
            'total_tiles': 4,
            'area': 100.0,
            'tiles_x': 2,
            'tiles_y': 2
        }
        
        layout_b = {
            'success': True, 
            'total_tiles': 6,
            'area': 120.0,
            'tiles_x': 3,
            'tiles_y': 2
        }
        
        result = self.optimizer.compare_layouts(layout_a, layout_b)
        
        assert 'comparison_winner' in result
        assert result['total_tiles'] == 6  # layout_b has more tiles


class TestProductionParameters:
    """Test cases for production parameters."""
    
    def test_production_parameters_validation(self):
        """Test production parameters validation."""
        params = ProductionParameters(
            volumen=1000,
            tiros_minimos=5,
            tiempo_por_tiro=1.0
        )
        
        is_valid, message = params.validate()
        assert is_valid == True
        assert message == "Production parameters are valid"
        
    def test_invalid_production_parameters(self):
        """Test invalid production parameters."""
        params = ProductionParameters(
            volumen=-100,  # Invalid: negative volume
            tiros_minimos=5,
            tiempo_por_tiro=0.0  # Invalid: zero time
        )
        
        is_valid, message = params.validate()
        assert is_valid == False
        assert "negative" in message or "positive" in message
        
    def test_production_metrics(self):
        """Test production metrics calculation."""
        params = ProductionParameters(
            volumen=100,
            tiros_minimos=2,
            tiempo_por_tiro=0.5,
            material_cost_per_cm2=0.01
        )
        
        metrics = params.calculate_production_metrics(
            tiles_per_shot=10,
            area_per_shot=1000.0
        )
        
        assert metrics['tiros_necesarios'] == 10  # ceil(100/10)
        assert metrics['tiempo_total'] == 5.0    # 10 * 0.5
        assert metrics['area_total'] == 10000.0  # 10 * 1000
        assert metrics['costo_total'] == 100.0   # 10000 * 0.01


class TestIntegration:
    """Integration tests for nesting system."""
    
    def test_end_to_end_optimization(self):
        """Test complete optimization workflow."""
        # Create mock components
        algorithms = NestingAlgorithms()
        optimizer = LayoutOptimizer()
        
        # Mock scene with basic functionality
        class MockScene:
            def calculate_global_bbox(self, tiles_x, tiles_y, medianil_x, medianil_y, objective):
                # Simple mock: bbox grows linearly with tiles
                width = tiles_x * (10 + medianil_x)
                height = tiles_y * (5 + medianil_y)
                return (0, 0, width, height)
                
        scene = MockScene()
        
        # Test optimization
        result = optimizer.optimize_production_layout(
            scene=scene,
            volumen=100,
            tiros_minimos=5,
            x_min_roland=10,
            x_max_roland=100,
            y_min_roland=10, 
            y_max_roland=100,
            medianil_x=1.0,
            medianil_y=1.0,
            objective="width"
        )
        
        # Basic result validation
        assert 'success' in result
        assert 'tiles_x' in result
        assert 'tiles_y' in result
        assert 'tiros_necesarios' in result
        
        if result['success']:
            assert result['tiles_x'] >= 1
            assert result['tiles_y'] >= 1
            assert result['tiros_necesarios'] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])