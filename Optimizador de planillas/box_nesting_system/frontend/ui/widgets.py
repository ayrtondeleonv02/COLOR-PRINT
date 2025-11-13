"""
Custom widgets for the Box Nesting Optimization System.
"""

import logging
import math
from typing import List, Tuple, Optional

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
from PySide6.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsItem
)

from backend.models.parameters import PlanoParams, construir_shapes_px
from backend.geometry.polygons import OrthoPoly
from backend.geometry.render_helpers import vertices_externos_px, build_tile_orthopoly_and_edges_cm
from backend.utils.constants import DEFAULT_COLORS, DEFAULT_CONSTANTS


class ZoomGraphicsView(QGraphicsView):
    """
    Enhanced QGraphicsView with zoom and pan capabilities.
    
    Provides smooth zooming and scrolling for better user experience.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the zoom graphics view."""
        super().__init__(*args, **kwargs)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.logger = logging.getLogger(__name__)
        self._zoom_locked = True

    def wheelEvent(self, event):
        """
        Handle wheel event for zooming.
        
        Args:
            event: Wheel event
        """
        if not self._zoom_locked:
            super().wheelEvent(event)

    def set_zoom_bounds(self, min_width: Optional[float], min_height: Optional[float],
                        max_width: Optional[float], max_height: Optional[float]) -> None:
        """Set zoom bounds in scene units (pixels)."""
        return

    def reset_drag_zoom_limits(self) -> None:
        """Disable manual zoom/pan interactions; view is locked to bed rect."""
        self._zoom_locked = True


class PlanoScene(QGraphicsScene):
    """
    Graphics scene for rendering the plano (editor) view.
    
    Displays box geometry with faces, tabs, and flanges in pixel coordinates.
    """

    def __init__(self):
        """Initialize the plano scene."""
        super().__init__()
        self.setSceneRect(0, 0, 3000, 2000)
        self.logger = logging.getLogger(__name__)

    def render_plano(self, params: PlanoParams) -> None:
        """
        Render the plano with given parameters.
        
        Args:
            params: Box parameters for rendering
        """
        self.clear()
        shapes = construir_shapes_px(params)
        
        # Draw all shapes
        for shp in shapes:
            rect = QRectF(shp['x'], shp['y'], shp['w'], shp['h'])
            
            # Usar los colores definidos en tus constantes
            if shp['name'].startswith('Cara'):
                color = DEFAULT_COLORS.to_qt_color(DEFAULT_COLORS.FACE_COLOR)
            elif shp['name'].startswith('Tapa'):
                color = DEFAULT_COLORS.to_qt_color(DEFAULT_COLORS.TAB_COLOR)
            elif shp['name'].startswith('Ceja'):
                color = DEFAULT_COLORS.to_qt_color(DEFAULT_COLORS.FLANGE_COLOR)
            else:
                color = DEFAULT_COLORS.to_qt_color(DEFAULT_COLORS.ACCENT_COLOR)
                
            self.addRect(rect, QPen(color, 1.5))
            
            # Label only main faces (1..4)
            name = shp['name']
            if name.startswith("Cara"):
                try:
                    cara_idx = int(name.replace("Cara", ""))
                except ValueError:
                    cara_idx = None
                    
                if cara_idx in (1, 2, 3, 4):
                    # Usar fuentes por defecto en lugar de importar DEFAULT_FONTS
                    font = QFont("Segoe UI", 14, QFont.Weight.Bold)
                    item = self.addSimpleText(str(cara_idx), font)
                    item.setBrush(DEFAULT_COLORS.to_qt_color(DEFAULT_COLORS.TEXT_COLOR))
                    br = item.boundingRect()
                    cx = shp['x'] + shp['w'] / 2.0
                    cy = shp['y'] + shp['h'] / 2.0
                    item.setPos(cx - br.width() / 2.0, cy - br.height() / 2.0)

        # Draw external vertices usando tu función existente
        pen_vert = QPen(DEFAULT_COLORS.to_qt_color(DEFAULT_COLORS.VERTEX_COLOR), 1.0)
        lado = 4.0
        for (cx, cy) in vertices_externos_px(shapes):
            self.addEllipse(QRectF(cx - lado/2, cy - lado/2, lado, lado), pen_vert)

    def bounding_box_px(self, params: PlanoParams) -> QRectF:
        """
        Calculate bounding box of all shapes in pixel coordinates.
        
        Args:
            params: Box parameters
            
        Returns:
            Bounding rectangle in pixels
        """
        shapes = construir_shapes_px(params)
        xs = [s['x'] for s in shapes] + [s['x'] + s['w'] for s in shapes]
        ys = [s['y'] for s in shapes] + [s['y'] + s['h'] for s in shapes]
        return QRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


class TileScene(QGraphicsScene):
    """
    Graphics scene for rendering nesting patterns on Roland bed.
    
    Purely visual - no nesting logic, only drawing capabilities.
    """

    def __init__(self, params: PlanoParams):
        """
        Initialize tile scene with parameters.
        
        Args:
            params: Box parameters for rendering
        """
        super().__init__()
        self.params = params
        self.setSceneRect(0, 0, 4000, 2500)
        self.logger = logging.getLogger(__name__)
        self.setBackgroundBrush(QColor(255, 255, 255))
        
        # Pattern distances for current layout (set externally)
        self.pattern_distances = None
        self.bed_rect: Optional[QRectF] = None
        self._bbox_item: Optional[QGraphicsRectItem] = None
        self._last_bbox_rect: Optional[QRectF] = None
        self.margin_left = 0.0
        self.margin_right = 0.0
        self.margin_top = 0.0
        self.margin_bottom = 0.0

    def _draw_grid(self, rect: QRectF, paso: float) -> None:
        """
        Draw grid lines for reference.
        
        Args:
            rect: Rectangle to fill with grid
            paso: Grid step in pixels
        """
        pen_grid = QPen(DEFAULT_COLORS.get_grid_lines(), 0.7, Qt.DotLine)
        x = rect.left()
        while x <= rect.right() + 1e-9:
            self.addLine(x, rect.top(), x, rect.bottom(), pen_grid)
            x += paso
        y = rect.top()
        while y <= rect.bottom() + 1e-9:
            self.addLine(rect.left(), y, rect.right(), y, pen_grid)
            y += paso

    def draw_bed(self, x_min_cm: float, x_max_cm: float,
                y_min_cm: float, y_max_cm: float) -> QRectF:
        """
        Draw Roland bed boundaries.
        
        Args:
            x_min_cm: Bed minimum X in cm
            x_max_cm: Bed maximum X in cm
            y_min_cm: Bed minimum Y in cm
            y_max_cm: Bed maximum Y in cm
            
        Returns:
            Bed rectangle in pixels
        """
        s = self.params.escala if self.params.escala != 0 else 1.0
        bed_w = max(0.0, x_max_cm * s)
        bed_h = max(0.0, y_max_cm * s)
        bed_rect = QRectF(0, 0, bed_w, bed_h)

        # Store bed dimensions (no visual rectangle needed)
        bed_pen = QPen(QColor(200, 200, 200), 1.5)
        bed_pen.setCosmetic(True)
        bed_brush = QBrush(DEFAULT_COLORS.get_bed_background())
        self.bed_rect = bed_rect
        self.setSceneRect(bed_rect)
        
        return bed_rect

    def set_margins(self, left: float, right: float, top: float, bottom: float) -> None:
        """Set current margin values (cm)."""
        self.margin_left = max(0.0, left)
        self.margin_right = max(0.0, right)
        self.margin_top = max(0.0, top)
        self.margin_bottom = max(0.0, bottom)

    def _update_bbox_outline(self, minx: float, miny: float, maxx: float, maxy: float) -> None:
        """Draw or refresh the bounding box outline for the current layout."""
        if self._bbox_item:
            try:
                self.removeItem(self._bbox_item)
            except RuntimeError:
                pass
            self._bbox_item = None
        if not math.isfinite(minx) or not math.isfinite(miny) or not math.isfinite(maxx) or not math.isfinite(maxy):
            return
        minx -= self.margin_left
        maxx += self.margin_right
        miny -= self.margin_top
        maxy += self.margin_bottom
        width = max(0.0, maxx - minx)
        height = max(0.0, maxy - miny)
        if width <= 0 or height <= 0:
            return
        s = self.params.escala if self.params.escala != 0 else 1.0
        rect = QRectF(minx * s, miny * s, width * s, height * s)
        pen = QPen(QColor(70, 150, 255), 2.5, Qt.SolidLine)
        pen.setCosmetic(True)
        self._bbox_item = self.addRect(rect, pen, Qt.NoBrush)
        self._last_bbox_rect = QRectF(minx, miny, width, height)

    def draw_tile(self, poly: OrthoPoly, rects: List[Tuple[str, Tuple[float, float, float, float]]], 
                 offset_x: float = 0.0, offset_y: float = 0.0) -> None:
        """
        Draw a single tile at specified offset.
        
        Args:
            poly: Tile polygon
            rects: Tile rectangles with names and dimensions
            offset_x: X offset in cm
            offset_y: Y offset in cm
        """
        s = self.params.escala if self.params.escala != 0 else 1.0
        
        # Create copy for translation
        poly_draw = OrthoPoly(poly.outer[:], [h[:] for h in poly.holes])
        if offset_x or offset_y:
            poly_draw.translate(offset_x, offset_y)
            
        # Draw polygon fill
        path = poly_draw.to_qpath(px_per_cm=s, fill_rule_odd_even=True)
        pen_outline = QPen(DEFAULT_COLORS.get_tile_outline(), 2.0)
        brush_fill = QBrush(DEFAULT_COLORS.get_tile_fill())
        self.addPath(path, pen_outline, brush_fill)
        
        # Draw rectangular contours
        pen_contour = QPen(DEFAULT_COLORS.get_tile_outline(), 2.0)
        for name, (x, y, w, h) in rects:
            self.addRect(
                QRectF((x + offset_x) * s, (y + offset_y) * s, w * s, h * s),
                pen_contour, 
                Qt.NoBrush
            )

    def draw_tiling_pattern(self, pattern_data: dict, tiles_x: int, tiles_y: int,
                          medianil_x: float, medianil_y: float) -> None:
        """
        Draw complete tiling pattern based on pattern data.
        
        Args:
            pattern_data: Dictionary with pattern information from NestingEngine
            tiles_x: Number of tiles in X direction
            tiles_y: Number of tiles in Y direction
            medianil_x: X separation between tiles
            medianil_y: Y separation between tiles
        """
        # Extract pattern data
        poly1 = pattern_data['poly1']
        rects1 = pattern_data['rects1']
        poly2T = pattern_data['poly2T']
        rects2T = pattern_data['rects2T']
        poly3T = pattern_data['poly3T']
        rects3T = pattern_data['rects3T']
        dx2 = pattern_data['dx2']
        dy2 = pattern_data['dy2']
        dx3 = pattern_data['dx3']
        dy3 = pattern_data['dy3']
        
        # Calculate vertical offset
        minx1, miny1, maxx1, maxy1 = poly1.aabb()
        h1 = maxy1 - miny1
        vertical_offset = h1 + medianil_y
        
        # Store pattern distances
        self.pattern_distances = {
            'tile2_offset': (dx2, dy2),
            'tile3_offset': (dx3, dy3),
            'alternating_offset': (dx3 - dx2, dy3 - dy2),
            'vertical_offset': vertical_offset,
            'medianil_x': medianil_x,
            'medianil_y': medianil_y,
            'tile_height': h1
        }

        positions: List[Tuple[OrthoPoly, List[Tuple[str, Tuple[float, float, float, float]]], float, float]] = []

        # Generate all rows (store first)
        for row in range(tiles_y):
            row_offset_y = row * vertical_offset
            for col in range(tiles_x):
                if col == 0:
                    positions.append((poly1, rects1, 0.0, row_offset_y))
                elif col == 1:
                    positions.append((poly2T, rects2T, dx2 + medianil_x, dy2 + row_offset_y))
                elif col == 2:
                    positions.append((poly3T, rects3T, dx3 + (2 * medianil_x), dy3 + row_offset_y))
                else:
                    if col % 2 == 1:  # Even tile
                        prev_tile_x = dx3 * ((col-1) // 2) + ((col-1) * medianil_x)
                        prev_tile_y = dy3 * ((col-1) // 2)
                        positions.append((poly2T, rects2T,
                                          prev_tile_x + dx2 + medianil_x,
                                          prev_tile_y + dy2 + row_offset_y))
                    else:  # Odd tile
                        prev_tile_x = dx2 + dx3 * ((col-2) // 2) + ((col-1) * medianil_x)
                        prev_tile_y = dy2 + dy3 * ((col-2) // 2)
                        positions.append((poly3T, rects3T,
                                          prev_tile_x + (dx3 - dx2) + medianil_x,
                                          prev_tile_y + (dy3 - dy2) + row_offset_y))

        min_layout_x = float('inf')
        min_layout_y = float('inf')
        max_layout_x = float('-inf')
        max_layout_y = float('-inf')

        for poly, _, ox, oy in positions:
            pminx, pminy, pmaxx, pmaxy = poly.aabb()
            min_layout_x = min(min_layout_x, pminx + ox)
            min_layout_y = min(min_layout_y, pminy + oy)
            max_layout_x = max(max_layout_x, pmaxx + ox)
            max_layout_y = max(max_layout_y, pmaxy + oy)

        shift_x = (min_layout_x - self.margin_left) if min_layout_x < float('inf') else 0.0
        shift_y = (min_layout_y - self.margin_top) if min_layout_y < float('inf') else 0.0

        def update_bounds(poly: OrthoPoly, ox: float, oy: float) -> None:
            nonlocal min_layout_x, min_layout_y, max_layout_x, max_layout_y
            pminx, pminy, pmaxx, pmaxy = poly.aabb()
            pminx += ox; pmaxx += ox
            pminy += oy; pmaxy += oy
            min_layout_x = min(min_layout_x, pminx)
            min_layout_y = min(min_layout_y, pminy)
            max_layout_x = max(max_layout_x, pmaxx)
            max_layout_y = max(max_layout_y, pmaxy)

        min_layout_x = float('inf')
        min_layout_y = float('inf')
        max_layout_x = float('-inf')
        max_layout_y = float('-inf')

        for poly, rects, ox, oy in positions:
            adj_x = ox - shift_x
            adj_y = oy - shift_y
            self.draw_tile(poly, rects, adj_x, adj_y)
            update_bounds(poly, adj_x, adj_y)

        if min_layout_x < float('inf'):
            self._update_bbox_outline(min_layout_x, min_layout_y, max_layout_x, max_layout_y)

    def clear_scene(self) -> None:
        """
        Clear all items from the scene.
        """
        self.clear()

    def draw_simple_tile(self) -> None:
        """
        Draw a simple single tile (fallback when no nesting data available).
        """
        from backend.geometry.transformations import rotate_and_align_top_left
        
        poly_base, rects_base = build_tile_orthopoly_and_edges_cm(self.params)
        poly1, rects1 = rotate_and_align_top_left(poly_base, rects_base, rot=90)
        minx, miny, maxx, maxy = poly1.aabb()
        shift_x = minx - self.margin_left
        shift_y = miny - self.margin_top
        self.draw_tile(poly1, rects1, -shift_x, -shift_y)
        self._update_bbox_outline(minx - shift_x, miny - shift_y, maxx - shift_x, maxy - shift_y)

    def get_layout_rect(self) -> Optional[QRectF]:
        """Return the last layout bounding rect in scene coordinates."""
        return self._last_bbox_rect
