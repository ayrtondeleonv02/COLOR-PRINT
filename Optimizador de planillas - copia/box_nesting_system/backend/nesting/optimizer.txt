"""
Layout optimization for production planning and constraints.
"""

import math
import logging
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class OptimizationResult:
    """Represents the result of layout optimization."""
    tiles_x: int
    tiles_y: int
    total_tiles: int
    tiros_necesarios: int
    bounding_box: Tuple[float, float, float, float]
    area: float
    efficiency: float
    objective: str
    razon: str
    optimal: bool = True


class LayoutOptimizer:
    """
    Optimizes layout based on production requirements and constraints.
    
    Implements sophisticated algorithms for production optimization
    considering volume, minimum shots, and material efficiency.
    """
    
    def __init__(self):
        """Initialize layout optimizer."""
        self.logger = logging.getLogger(__name__)

    def optimize_production_layout(self, 
                                 scene: Any,
                                 volumen: int,
                                 tiros_minimos: int,
                                 x_min_roland: float,
                                 x_max_roland: float, 
                                 y_min_roland: float,
                                 y_max_roland: float,
                                 medianil_x: float,
                                 medianil_y: float,
                                 objective: str = "width") -> Dict[str, Any]:
        """
        Optimize layout based on production parameters.
        
        Args:
            scene: Tile scene for bounding box calculations
            volumen: Production volume (number of pieces)
            tiros_minimos: Minimum required shots
            x_min_roland: Roland bed minimum X
            x_max_roland: Roland bed maximum X
            y_min_roland: Roland bed minimum Y
            y_max_roland: Roland bed maximum Y
            medianil_x: X separation between tiles
            medianil_y: Y separation between tiles
            objective: Optimization objective
            
        Returns:
            Dictionary with optimization results
        """
        self.logger.info("Starting production layout optimization")
        
        # 1. Calculate layout bounds
        layout_bounds = self._calculate_layout_bounds(
            scene, x_min_roland, x_max_roland, y_min_roland, y_max_roland,
            medianil_x, medianil_y, objective
        )
        
        if not layout_bounds:
            return self._create_error_result("No valid layout bounds found")
            
        tiles_x_min, tiles_y_min, tiles_x_max, tiles_y_max = layout_bounds
        
        # 2. Calculate production metrics
        production_metrics = self._calculate_production_metrics(
            tiles_x_min, tiles_y_min, tiles_x_max, tiles_y_max,
            volumen, tiros_minimos
        )
        
        # 3. Find optimal layout
        optimal_layout = self._find_optimal_layout(
            scene, production_metrics, medianil_x, medianil_y, objective
        )
        
        return optimal_layout

    def _calculate_layout_bounds(self, scene: Any,
                               x_min_roland: float, x_max_roland: float,
                               y_min_roland: float, y_max_roland: float,
                               medianil_x: float, medianil_y: float,
                               objective: str) -> Optional[Tuple[int, int, int, int]]:
        """
        Calculate minimum and maximum layout bounds that fit Roland bed.
        
        Args:
            scene: Tile scene for calculations
            x_min_roland: Bed minimum X
            x_max_roland: Bed maximum X
            y_min_roland: Bed minimum Y
            y_max_roland: Bed maximum Y
            medianil_x: X separation
            medianil_y: Y separation
            objective: Optimization objective
            
        Returns:
            Tuple of (min_x, min_y, max_x, max_y) or None
        """
        try:
            # Find minimum tiles_x that fits in X direction
            tiles_x_min = 1
            while True:
                bbox = scene.calculate_global_bbox(tiles_x_min, 1, medianil_x, medianil_y, objective)
                ancho_total = bbox[2] - bbox[0]
                if ancho_total >= x_min_roland:
                    break
                tiles_x_min += 1
                if tiles_x_min > 100:  # Safety limit
                    return None

            # Find minimum tiles_y that fits in Y direction
            tiles_y_min = 1
            while True:
                bbox = scene.calculate_global_bbox(tiles_x_min, tiles_y_min, medianil_x, medianil_y, objective)
                alto_total = bbox[3] - bbox[1]
                if alto_total >= y_min_roland:
                    break
                tiles_y_min += 1
                if tiles_y_min > 100:  # Safety limit
                    return None

            # Find maximum tiles_x that fits in X direction
            tiles_x_max = tiles_x_min
            while True:
                bbox = scene.calculate_global_bbox(tiles_x_max + 1, 1, medianil_x, medianil_y, objective)
                ancho_total = bbox[2] - bbox[0]
                if ancho_total > x_max_roland:
                    break
                tiles_x_max += 1
                if tiles_x_max > 100:  # Safety limit
                    break

            # Find maximum tiles_y that fits in Y direction
            tiles_y_max = tiles_y_min
            while True:
                bbox = scene.calculate_global_bbox(tiles_x_max, tiles_y_max + 1, medianil_x, medianil_y, objective)
                alto_total = bbox[3] - bbox[1]
                if alto_total > y_max_roland:
                    break
                tiles_y_max += 1
                if tiles_y_max > 100:  # Safety limit
                    break

            return (tiles_x_min, tiles_y_min, tiles_x_max, tiles_y_max)
            
        except Exception as e:
            self.logger.error("Error calculating layout bounds: %s", e)
            return None

    def _calculate_production_metrics(self,
                                    tiles_x_min: int, tiles_y_min: int,
                                    tiles_x_max: int, tiles_y_max: int,
                                    volumen: int, tiros_minimos: int) -> Dict[str, Any]:
        """
        Calculate production metrics for layout bounds.
        
        Args:
            tiles_x_min: Minimum X tiles
            tiles_y_min: Minimum Y tiles
            tiles_x_max: Maximum X tiles
            tiles_y_max: Maximum Y tiles
            volumen: Production volume
            tiros_minimos: Minimum shots
            
        Returns:
            Dictionary with production metrics
        """
        planos_min = tiles_x_min * tiles_y_min
        planos_max = tiles_x_max * tiles_y_max
        
        tiros_con_min = max(1, math.ceil(volumen / planos_min)) if planos_min > 0 else 0
        tiros_con_max = max(1, math.ceil(volumen / planos_max)) if planos_max > 0 else 0
        
        return {
            'tiles_x_min': tiles_x_min,
            'tiles_y_min': tiles_y_min,
            'tiles_x_max': tiles_x_max,
            'tiles_y_max': tiles_y_max,
            'planos_min': planos_min,
            'planos_max': planos_max,
            'tiros_con_min': tiros_con_min,
            'tiros_con_max': tiros_con_max,
            'volumen': volumen,
            'tiros_minimos': tiros_minimos
        }

    def _find_optimal_layout(self, scene: Any, metrics: Dict[str, Any],
                           medianil_x: float, medianil_y: float,
                           objective: str) -> Dict[str, Any]:
        """
        Find optimal layout based on production metrics.
        
        Args:
            scene: Tile scene for calculations
            metrics: Production metrics
            medianil_x: X separation
            medianil_y: Y separation
            objective: Optimization objective
            
        Returns:
            Dictionary with optimal layout
        """
        tiles_x_min = metrics['tiles_x_min']
        tiles_y_min = metrics['tiles_y_min']
        tiles_x_max = metrics['tiles_x_max']
        tiles_y_max = metrics['tiles_y_max']
        tiros_con_min = metrics['tiros_con_min']
        tiros_con_max = metrics['tiros_con_max']
        tiros_minimos = metrics['tiros_minimos']
        volumen = metrics['volumen']

        layout_optimo = None
        razon_decision = ""

        # Strategy 1: Minimum layout satisfies minimum shots
        if tiros_con_min <= tiros_minimos:
            layout_optimo = (tiles_x_min, tiles_y_min)
            razon_decision = f"Layout MÍNIMO - {tiros_con_min} tiros ≤ {tiros_minimos} tiros mínimos"

        # Strategy 2: Maximum layout satisfies minimum shots
        elif tiros_con_max >= tiros_minimos:
            layout_optimo = (tiles_x_max, tiles_y_max)
            razon_decision = f"Layout MÁXIMO - {tiros_con_max} tiros ≥ {tiros_minimos} tiros mínimos"

        # Strategy 3: Find intermediate optimal layout
        else:
            total_tiles_necesario = math.ceil(volumen / tiros_minimos)
            layout_optimo = self._find_intermediate_layout(
                scene, tiles_x_min, tiles_y_min, tiles_x_max, tiles_y_max,
                total_tiles_necesario, medianil_x, medianil_y, objective
            )
            razon_decision = f"Layout INTERMEDIO - {total_tiles_necesario} tiles necesarios"

        if layout_optimo:
            tiles_x, tiles_y = layout_optimo
            return self._create_success_result(
                scene, tiles_x, tiles_y, medianil_x, medianil_y, 
                objective, razon_decision, volumen, tiros_minimos
            )
        else:
            return self._create_error_result("No se pudo encontrar un layout óptimo")

    def _find_intermediate_layout(self, scene: Any,
                                tiles_x_min: int, tiles_y_min: int,
                                tiles_x_max: int, tiles_y_max: int,
                                total_tiles_necesario: int,
                                medianil_x: float, medianil_y: float,
                                objective: str) -> Optional[Tuple[int, int]]:
        """
        Find intermediate layout that matches required tile count.
        
        Args:
            scene: Tile scene for calculations
            tiles_x_min: Minimum X tiles
            tiles_y_min: Minimum Y tiles
            tiles_x_max: Maximum X tiles
            tiles_y_max: Maximum Y tiles
            total_tiles_necesario: Required total tiles
            medianil_x: X separation
            medianil_y: Y separation
            objective: Optimization objective
            
        Returns:
            Optimal tile configuration or None
        """
        factores_posibles = []
        
        for tx in range(tiles_x_min, tiles_x_max + 1):
            for ty in range(tiles_y_min, tiles_y_max + 1):
                if tx * ty == total_tiles_necesario:
                    bbox = scene.calculate_global_bbox(tx, ty, medianil_x, medianil_y, objective)
                    ancho = bbox[2] - bbox[0]
                    alto = bbox[3] - bbox[1]
                    area = ancho * alto
                    factores_posibles.append((tx, ty, area, ancho, alto))
        
        if factores_posibles:
            # Find layout with minimum area
            mejor_factor = min(factores_posibles, key=lambda x: x[2])
            return (mejor_factor[0], mejor_factor[1])
        
        # Fallback: use maximum layout
        return (tiles_x_max, tiles_y_max)

    def _create_success_result(self, scene: Any, tiles_x: int, tiles_y: int,
                             medianil_x: float, medianil_y: float,
                             objective: str, razon: str,
                             volumen: int, tiros_minimos: int) -> Dict[str, Any]:
        """
        Create success result dictionary.
        
        Args:
            scene: Tile scene for calculations
            tiles_x: Optimal X tiles
            tiles_y: Optimal Y tiles
            medianil_x: X separation
            medianil_y: Y separation
            objective: Optimization objective
            razon: Decision reason
            volumen: Production volume
            tiros_minimos: Minimum shots
            
        Returns:
            Success result dictionary
        """
        bbox = scene.calculate_global_bbox(tiles_x, tiles_y, medianil_x, medianil_y, objective)
        ancho = bbox[2] - bbox[0]
        alto = bbox[3] - bbox[1]
        area = ancho * alto
        total_tiles = tiles_x * tiles_y
        tiros_necesarios = max(1, math.ceil(volumen / total_tiles))
        
        return {
            'success': True,
            'tiles_x': tiles_x,
            'tiles_y': tiles_y,
            'total_tiles': total_tiles,
            'ancho': ancho,
            'alto': alto,
            'area': area,
            'objective': objective,
            'razon': razon,
            'volumen': volumen,
            'tiros_minimos': tiros_minimos,
            'tiros_necesarios': tiros_necesarios,
            'bounding_box': bbox
        }

    def _create_error_result(self, message: str) -> Dict[str, Any]:
        """
        Create error result dictionary.
        
        Args:
            message: Error message
            
        Returns:
            Error result dictionary
        """
        return {
            'success': False,
            'error': message,
            'tiles_x': 1,
            'tiles_y': 1,
            'total_tiles': 1,
            'ancho': 0.0,
            'alto': 0.0,
            'area': 0.0
        }

    def compare_layouts(self, layout_a: Dict[str, Any], layout_b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two layouts and select the best one.
        
        Args:
            layout_a: First layout to compare
            layout_b: Second layout to compare
            
        Returns:
            Best layout with comparison metadata
        """
        if not layout_a.get('success', False) and not layout_b.get('success', False):
            return self._create_error_result("Neither layout is valid")
        elif not layout_a.get('success', False):
            return {**layout_b, 'comparison_winner': 'layout_b'}
        elif not layout_b.get('success', False):
            return {**layout_a, 'comparison_winner': 'layout_a'}
        
        # Compare by total tiles (primary criterion)
        if layout_a['total_tiles'] > layout_b['total_tiles']:
            winner = layout_a
            winner_key = 'layout_a'
            reason = "Mayor cantidad de tiles"
        elif layout_b['total_tiles'] > layout_a['total_tiles']:
            winner = layout_b
            winner_key = 'layout_b'
            reason = "Mayor cantidad de tiles"
        else:
            # Tie-breaker: smaller area
            if layout_a['area'] < layout_b['area']:
                winner = layout_a
                winner_key = 'layout_a'
                reason = "Menor área (desempate)"
            else:
                winner = layout_b
                winner_key = 'layout_b'
                reason = "Menor área (desempate)"
        
        return {
            **winner,
            'comparison_winner': winner_key,
            'comparison_reason': reason,
            'layout_a_tiles': layout_a['total_tiles'],
            'layout_b_tiles': layout_b['total_tiles'],
            'layout_a_area': layout_a['area'],
            'layout_b_area': layout_b['area']
        }