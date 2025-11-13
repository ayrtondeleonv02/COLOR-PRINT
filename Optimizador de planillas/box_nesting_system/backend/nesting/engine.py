"""
Motor principal de nesting que coordina algoritmos, caché y patrones.
Reconstruye la funcionalidad exacta del código original.
"""

import math
import time
import logging
from typing import Dict, Any, Optional, Tuple, List

from PySide6.QtCore import QEventLoop
from PySide6.QtWidgets import QApplication

from backend.geometry.polygons import OrthoPoly
from backend.geometry.render_helpers import build_tile_orthopoly_and_edges_cm  # CORREGIDO
from backend.geometry.transformations import rotate_and_align_top_left, rotate_rect_generic
from backend.geometry.collision import polygons_intersect
from backend.geometry.types import RectCM
from backend.utils.constants import DEFAULT_CONSTANTS

from .algorithms import NestingAlgorithms
from .cache import NestingCache
from .patterns import TilingPatternGenerator


def _pump_ui_events() -> None:
    """Allow Qt to process pending events if the application is running."""
    app = QApplication.instance()
    if app:
        app.processEvents(QEventLoop.AllEvents, 5)


class NestingEngine:
    """
    Motor principal que coordina todo el proceso de nesting.
    Replica exactamente la funcionalidad del código original de TileScene.
    """
    
    def __init__(self, params):
        self.params = params
        self.algorithms = NestingAlgorithms()
        self.pattern_generator = TilingPatternGenerator()
        
        # Caché separado por objetivo (igual que original)
        self.nesting_cache_width = NestingCache()
        self.nesting_cache_height = NestingCache()
        self.last_cache_key_width = None
        self.last_cache_key_height = None
        
        self.logger = logging.getLogger(__name__)

    def _generate_cache_key(self, paso_y, paso_x, clearance_cm, objective):
        """Genera clave única para caché (igual que original)."""
        p = self.params
        key_parts = [
            p.L, p.A, p.h, p.cIzq, p.cDer,
            tuple(p.Tapas),
            tuple(p.CSup),
            tuple(p.Bases), 
            tuple(p.CInf),
            paso_y, paso_x, clearance_cm, objective
        ]
        return tuple(key_parts)

    def _store_nesting_result(self, paso_y, paso_x, clearance_cm, objective,
                            poly1, rects1, poly2T, rects2T, poly3T, rects3T,
                            dx2, dy2, dx3, dy3, rot1, rot2):
        """Almacena resultado en caché (igual que original)."""
        self.logger.debug(
            "Caching nesting result (objective=%s, paso_y=%.3f, paso_x=%.3f, clearance=%.3f)",
            objective, paso_y, paso_x, clearance_cm
        )
        pattern_data = {
            'poly1': OrthoPoly(poly1.outer[:], [h[:] for h in poly1.holes]),
            'rects1': [(name, (x, y, w, h)) for name, (x, y, w, h) in rects1],
            'poly2T': OrthoPoly(poly2T.outer[:], [h[:] for h in poly2T.holes]),
            'rects2T': [(name, (x, y, w, h)) for name, (x, y, w, h) in rects2T],
            'poly3T': OrthoPoly(poly3T.outer[:], [h[:] for h in poly3T.holes]),
            'rects3T': [(name, (x, y, w, h)) for name, (x, y, w, h) in rects3T],
            'dx2': dx2, 'dy2': dy2,
            'dx3': dx3, 'dy3': dy3,
            'rot1': rot1, 'rot2': rot2,
            'paso_y': paso_y, 'paso_x': paso_x,
            'clearance_cm': clearance_cm, 'objective': objective
        }
        
        cache_key = self._generate_cache_key(paso_y, paso_x, clearance_cm, objective)
        
        if objective == "width":
            self.nesting_cache_width.store(pattern_data, cache_key)
            self.last_cache_key_width = cache_key
            self.logger.debug("Stored cache entry for width key: %s", cache_key)
        else:
            self.nesting_cache_height.store(pattern_data, cache_key)
            self.last_cache_key_height = cache_key
            self.logger.debug("Stored cache entry for height key: %s", cache_key)

    def _render_from_cache(self, tiles_x, tiles_y, medianil_x, medianil_y, objective):
        """Renderiza desde caché (igual que original)."""
        if objective == "width":
            cache = self.nesting_cache_width
            last_key = self.last_cache_key_width
        else:
            cache = self.nesting_cache_height
            last_key = self.last_cache_key_height
            
        if not cache.pattern_data:
            self.logger.debug("Cache miss for %s: no pattern_data available", objective)
            return False
            
        pattern_data = cache.pattern_data
        required_keys = ('paso_y', 'paso_x', 'clearance_cm', 'objective')
        if any(key not in pattern_data for key in required_keys):
            self.logger.warning("Cache entry missing metadata (%s), forcing recalculation", objective)
            return False
        
        # Verificar si el caché es válido
        current_key = self._generate_cache_key(
            pattern_data['paso_y'],
            pattern_data['paso_x'], 
            pattern_data['clearance_cm'],
            pattern_data['objective']
        )
        
        if not cache.is_valid(current_key):
            self.logger.debug("Cache invalid (objective=%s, key=%s)", objective, current_key)
            return False

        self.logger.info(
            "Cache hit (objective=%s, key=%s) - reusing nesting result",
            objective, current_key
        )
            
        return pattern_data

    def calculate_optimal_nesting(self, 
                                tiles_x: int = 1, 
                                tiles_y: int = 1,
                                paso_y: float = 0.5, 
                                paso_x: float = 0.1,
                                clearance_cm: float = 0.0,
                                medianil_x: float = 0.0,
                                medianil_y: float = 0.0,
                                objective: str = "width",
                                force_recalculate: bool = False):
        """
        Calcula nesting óptimo - réplica exacta de la lógica original.
        """
        start_time = time.perf_counter()
        # Verificar caché primero
        if not force_recalculate:
            cached_data = self._render_from_cache(tiles_x, tiles_y, medianil_x, medianil_y, objective)
            if cached_data:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                self.logger.info(
                    "calculate_optimal_nesting served from cache (objective=%s, tiles=%dx%d) en %.2f ms",
                    objective, tiles_x, tiles_y, elapsed_ms
                )
                return cached_data

        # Cálculo completo (igual que original)
        _pump_ui_events()
        poly_base, rects_base = build_tile_orthopoly_and_edges_cm(self.params)
        global_best = None
        global_key = (float("inf"), float("inf"), float("inf"))

        for rot1 in (90, 270):  # Probamos ambas orientaciones principales
            _pump_ui_events()
            poly1, rects1 = rotate_and_align_top_left(poly_base, rects_base, rot=rot1)
            
            # Buscar mejor posición para segundo tile
            candidate_2tiles = self.algorithms.best_place_second_tile(
                poly1, rects1,
                paso_y=paso_y, paso_x=paso_x,
                clearance_cm=clearance_cm,
                objective=objective
            )
            
            if candidate_2tiles is None:
                continue

            best_x, best_y, rot2, rects2T, poly2T, gwidth12, gheight12, garea12 = candidate_2tiles
            _pump_ui_events()

            poly2 = OrthoPoly(poly2T.outer[:], [h[:] for h in poly2T.holes])
            poly2.translate(best_x, best_y)

            # Buscar mejor posición para tercer tile
            candidate_3tiles = self.algorithms.best_place_third_tile(
                poly1, poly2, rects1, rects2T, rot1,
                paso_y=paso_y, paso_x=paso_x, 
                clearance_cm=clearance_cm,
                objective=objective,
                params=self.params
            )
            
            if candidate_3tiles is None:
                continue

            x3, y3, rects3T, poly3T, gwidth, gheight, garea = candidate_3tiles
            _pump_ui_events()

            # Evaluar según objetivo
            if objective == "width":
                key = (gwidth, gheight, garea)
            elif objective == "height":
                key = (gheight, gwidth, garea)
            else:
                key = (garea, gwidth, gheight)

            # Comparar con mejor solución actual
            eps = DEFAULT_CONSTANTS.EPSILON

            better = False
            if key[0] < global_key[0] - eps:
                better = True
            elif abs(key[0] - global_key[0]) <= eps:
                if key[1] < global_key[1] - eps:
                    better = True
                elif abs(key[1] - global_key[1]) <= eps:
                    if key[2] < global_key[2] - eps:
                        better = True

            if better:
                _pump_ui_events()
                global_key = key
                global_best = (rot1, poly1, rects1, 
                              best_x, best_y, rot2, rects2T, poly2T,
                              x3, y3, rects3T, poly3T, 
                              gwidth, gheight, garea)

        if global_best is None:
            return None

        # Extraer resultados
        (rot1, poly1, rects1, 
         best_x, best_y, rot2, rects2T, poly2T,
         x3, y3, rects3T, poly3T, 
         gwidth, gheight, garea) = global_best
        _pump_ui_events()

        # Almacenar en caché
        self._store_nesting_result(
            paso_y, paso_x, clearance_cm, objective,
            poly1, rects1, poly2T, rects2T, poly3T, rects3T,
            best_x, best_y, x3, y3, rot1, rot2
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        self.logger.info(
            "calculate_optimal_nesting recalculated (objective=%s, tiles=%dx%d, force=%s) en %.2f ms",
            objective, tiles_x, tiles_y, force_recalculate, elapsed_ms
        )

        return {
            'poly1': poly1, 'rects1': rects1,
            'poly2T': poly2T, 'rects2T': rects2T,
            'poly3T': poly3T, 'rects3T': rects3T,
            'dx2': best_x, 'dy2': best_y,
            'dx3': x3, 'dy3': y3,
            'rot1': rot1, 'rot2': rot2,
            'bounding_box': (gwidth, gheight, garea),
            'tiles_x': tiles_x,
            'tiles_y': tiles_y,
            'medianil_x': medianil_x,
            'medianil_y': medianil_y
        }

    def generate_tiling_pattern(self, nesting_result, scale: float):
        """
        Genera el patrón de tiling completo.
        """
        return self.pattern_generator.generate_tiling_pattern(
            nesting_result['poly1'], nesting_result['rects1'],
            nesting_result['poly2T'], nesting_result['rects2T'],
            nesting_result['poly3T'], nesting_result['rects3T'],
            nesting_result['dx2'], nesting_result['dy2'],
            nesting_result['dx3'], nesting_result['dy3'],
            nesting_result['rot1'], nesting_result['rot2'],
            nesting_result['tiles_x'], nesting_result['tiles_y'],
            nesting_result['medianil_x'], nesting_result['medianil_y'],
            scale
        )

    def calculate_global_bbox(self, tiles_x: int, tiles_y: int, 
                            medianil_x: float, medianil_y: float, 
                            objective: str = "width") -> Tuple[float, float, float, float]:
        """
        Calcula bounding box global - réplica exacta de lógica original.
        """
        # Seleccionar caché correcto
        if objective == "width":
            cache = self.nesting_cache_width
        else:
            cache = self.nesting_cache_height
            
        if not cache.pattern_data:
            # Fallback a un tile simple
            poly_base, _ = build_tile_orthopoly_and_edges_cm(self.params)
            poly1, _ = rotate_and_align_top_left(poly_base, [], rot=90)
            minx, miny, maxx, maxy = poly1.aabb()
            return (minx, miny, maxx, maxy)
        
        pattern_data = cache.pattern_data
        poly1 = pattern_data['poly1']
        poly2T = pattern_data['poly2T']
        poly3T = pattern_data['poly3T']
        dx2 = pattern_data['dx2']
        dy2 = pattern_data['dy2']
        dx3 = pattern_data['dx3']
        dy3 = pattern_data['dy3']
        
        minx1, miny1, maxx1, maxy1 = poly1.aabb()
        h1 = maxy1 - miny1
        
        # Calcular desplazamiento vertical INCLUYENDO MEDIANIL_Y
        vertical_offset = h1 + medianil_y
        
        # Inicializar bounding box global
        global_minx = float('inf')
        global_miny = float('inf')
        global_maxx = float('-inf')
        global_maxy = float('-inf')
        
        # Generar todas las filas (igual que original)
        for row in range(tiles_y):
            row_offset_y = row * vertical_offset
            
            for col in range(tiles_x):
                if col == 0:
                    current_poly = poly1
                    offset_x = 0.0
                    offset_y = row_offset_y
                elif col == 1:
                    current_poly = poly2T
                    offset_x = dx2 + medianil_x
                    offset_y = dy2 + row_offset_y
                elif col == 2:
                    current_poly = poly3T
                    offset_x = dx3 + (2 * medianil_x)
                    offset_y = dy3 + row_offset_y
                else:
                    if col % 2 == 1:  # Tile par
                        prev_tile_x = dx3 * ((col-1) // 2) + ((col-1) * medianil_x)
                        prev_tile_y = dy3 * ((col-1) // 2)
                        offset_x = prev_tile_x + dx2 + medianil_x
                        offset_y = prev_tile_y + dy2 + row_offset_y
                        current_poly = poly2T
                    else:  # Tile impar
                        prev_tile_x = dx2 + dx3 * ((col-2) // 2) + ((col-1) * medianil_x)
                        prev_tile_y = dy2 + dy3 * ((col-2) // 2)
                        offset_x = prev_tile_x + (dx3 - dx2) + medianil_x
                        offset_y = prev_tile_y + (dy3 - dy2) + row_offset_y
                        current_poly = poly3T
                
                # Calcular bounding box del tile actual
                minx, miny, maxx, maxy = current_poly.aabb()
                minx += offset_x
                miny += offset_y
                maxx += offset_x
                maxy += offset_y
                
                # Actualizar bounding box global
                global_minx = min(global_minx, minx)
                global_miny = min(global_miny, miny)
                global_maxx = max(global_maxx, maxx)
                global_maxy = max(global_maxy, maxy)
        
        return (global_minx, global_miny, global_maxx, global_maxy)
