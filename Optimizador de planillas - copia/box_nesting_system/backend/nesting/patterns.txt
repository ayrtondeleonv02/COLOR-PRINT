"""
Tiling pattern generation and management.
"""

import logging
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

from backend.geometry.polygons import OrthoPoly
from backend.geometry.types import RectCM


@dataclass
class PatternDistances:
    """Stores distances and offsets for tiling patterns."""
    tile2_offset: Tuple[float, float]
    tile3_offset: Tuple[float, float]
    alternating_offset: Tuple[float, float]
    vertical_offset: float
    medianil_x: float
    medianil_y: float
    tile_height: float


class TilingPatternGenerator:
    """
    Generates and manages tiling patterns for nesting.
    
    Handles the complex logic of tile positioning and pattern repetition.
    """
    
    def __init__(self):
        """Initialize pattern generator."""
        self.logger = logging.getLogger(__name__)
        self.pattern_distances: Optional[PatternDistances] = None

    def generate_tiling_pattern(self, 
                              poly1: OrthoPoly, rects1: List[Tuple[str, RectCM]],
                              poly2T: OrthoPoly, rects2T: List[Tuple[str, RectCM]],
                              poly3T: OrthoPoly, rects3T: List[Tuple[str, RectCM]],
                              dx2: float, dy2: float,
                              dx3: float, dy3: float,
                              rot1: int, rot2: int,
                              tiles_x: int, tiles_y: int,
                              medianil_x: float, medianil_y: float,
                              scale: float) -> PatternDistances:
        """
        Generate complete tiling pattern based on relative positions.
        
        Args:
            poly1: First tile polygon template
            rects1: First tile rectangles
            poly2T: Second tile polygon template
            rects2T: Second tile rectangles
            poly3T: Third tile polygon template
            rects3T: Third tile rectangles
            dx2: Second tile X offset
            dy2: Second tile Y offset
            dx3: Third tile X offset
            dy3: Third tile Y offset
            rot1: First tile rotation
            rot2: Second tile rotation
            tiles_x: Number of tiles in X direction
            tiles_y: Number of tiles in Y direction
            medianil_x: X separation between tiles
            medianil_y: Y separation between tiles
            scale: Render scale
            
        Returns:
            Pattern distances for the generated pattern
        """
        minx1, miny1, maxx1, maxy1 = poly1.aabb()
        h1 = maxy1 - miny1
        
        # Calculate vertical offset INCLUDING medianil_y
        vertical_offset = h1 + medianil_y
        
        # Store pattern distances for future use
        self.pattern_distances = PatternDistances(
            tile2_offset=(dx2, dy2),
            tile3_offset=(dx3, dy3),
            alternating_offset=(dx3 - dx2, dy3 - dy2),
            vertical_offset=vertical_offset,
            medianil_x=medianil_x,
            medianil_y=medianil_y,
            tile_height=h1
        )
        
        return self.pattern_distances

    def calculate_tile_positions(self, tiles_x: int, tiles_y: int,
                               pattern_distances: PatternDistances) -> List[Dict[str, Any]]:
        """
        Calculate positions for all tiles in the pattern.
        
        Args:
            tiles_x: Number of tiles in X direction
            tiles_y: Number of tiles in Y direction
            pattern_distances: Pattern distance information
            
        Returns:
            List of tile positions and metadata
        """
        positions = []
        dx2, dy2 = pattern_distances.tile2_offset
        dx3, dy3 = pattern_distances.tile3_offset
        vertical_offset = pattern_distances.vertical_offset
        medianil_x = pattern_distances.medianil_x
        
        for row in range(tiles_y):
            row_offset_y = row * vertical_offset
            
            for col in range(tiles_x):
                tile_info = self._calculate_single_tile_position(
                    col, row, dx2, dy2, dx3, dy3, 
                    medianil_x, row_offset_y
                )
                positions.append(tile_info)
                
        return positions

    def _calculate_single_tile_position(self, col: int, row: int,
                                      dx2: float, dy2: float,
                                      dx3: float, dy3: float,
                                      medianil_x: float, row_offset_y: float) -> Dict[str, Any]:
        """
        Calculate position for a single tile.
        
        Args:
            col: Column index
            row: Row index
            dx2: Second tile X offset
            dy2: Second tile Y offset
            dx3: Third tile X offset
            dy3: Third tile Y offset
            medianil_x: X separation
            row_offset_y: Row Y offset
            
        Returns:
            Tile position information
        """
        if col == 0:
            # Tile 1 (odd) - always first position in each row
            return {
                'col': col,
                'row': row,
                'tile_type': 'odd',
                'tile_index': 1,
                'offset_x': 0.0,
                'offset_y': row_offset_y,
                'is_template': True
            }
        elif col == 1:
            # Tile 2 (even) - second position
            return {
                'col': col,
                'row': row,
                'tile_type': 'even',
                'tile_index': 2,
                'offset_x': dx2 + medianil_x,
                'offset_y': dy2 + row_offset_y,
                'is_template': True
            }
        elif col == 2:
            # Tile 3 (odd) - third position
            return {
                'col': col,
                'row': row,
                'tile_type': 'odd',
                'tile_index': 3,
                'offset_x': dx3 + (2 * medianil_x),
                'offset_y': dy3 + row_offset_y,
                'is_template': True
            }
        else:
            if col % 2 == 1:  # Even tile
                # Position relative to last odd tile + medianil_x
                prev_tile_x = dx3 * ((col-1) // 2) + ((col-1) * medianil_x)
                prev_tile_y = dy3 * ((col-1) // 2)
                offset_x = prev_tile_x + dx2 + medianil_x
                offset_y = prev_tile_y + dy2 + row_offset_y
                
                return {
                    'col': col,
                    'row': row,
                    'tile_type': 'even',
                    'tile_index': 2,
                    'offset_x': offset_x,
                    'offset_y': offset_y,
                    'is_template': False
                }
            else:  # Odd tile
                # Position relative to last even tile + medianil_x
                prev_tile_x = dx2 + dx3 * ((col-2) // 2) + ((col-1) * medianil_x)
                prev_tile_y = dy2 + dy3 * ((col-2) // 2)
                offset_x = prev_tile_x + (dx3 - dx2) + medianil_x
                offset_y = prev_tile_y + (dy3 - dy2) + row_offset_y
                
                return {
                    'col': col,
                    'row': row,
                    'tile_type': 'odd',
                    'tile_index': 3,
                    'offset_x': offset_x,
                    'offset_y': offset_y,
                    'is_template': False
                }

    def validate_pattern(self, tiles_x: int, tiles_y: int,
                       pattern_distances: PatternDistances,
                       bed_width: float, bed_height: float) -> Tuple[bool, str]:
        """
        Validate that pattern fits within bed dimensions.
        
        Args:
            tiles_x: Number of tiles in X direction
            tiles_y: Number of tiles in Y direction
            pattern_distances: Pattern distance information
            bed_width: Bed width in cm
            bed_height: Bed height in cm
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Calculate global bounding box
            positions = self.calculate_tile_positions(tiles_x, tiles_y, pattern_distances)
            
            # This would calculate the actual bounding box
            # For now, use simplified validation
            estimated_width = tiles_x * (pattern_distances.tile_height + pattern_distances.medianil_x)
            estimated_height = tiles_y * (pattern_distances.vertical_offset)
            
            if estimated_width > bed_width:
                return False, f"Pattern width {estimated_width:.2f}cm exceeds bed width {bed_width:.2f}cm"
                
            if estimated_height > bed_height:
                return False, f"Pattern height {estimated_height:.2f}cm exceeds bed height {bed_height:.2f}cm"
                
            return True, "Pattern fits within bed dimensions"
            
        except Exception as e:
            return False, f"Pattern validation error: {str(e)}"

    def calculate_pattern_efficiency(self, tiles_x: int, tiles_y: int,
                                  pattern_distances: PatternDistances,
                                  single_tile_area: float) -> float:
        """
        Calculate pattern efficiency (area utilization).
        
        Args:
            tiles_x: Number of tiles in X direction
            tiles_y: Number of tiles in Y direction
            pattern_distances: Pattern distance information
            single_tile_area: Area of a single tile
            
        Returns:
            Efficiency ratio (0.0 to 1.0)
        """
        try:
            # Calculate total area used by pattern
            total_tiles_area = single_tile_area * tiles_x * tiles_y
            
            # Estimate pattern bounding box area
            estimated_width = tiles_x * (pattern_distances.tile_height + pattern_distances.medianil_x)
            estimated_height = tiles_y * (pattern_distances.vertical_offset)
            pattern_area = estimated_width * estimated_height
            
            if pattern_area <= 0:
                return 0.0
                
            efficiency = total_tiles_area / pattern_area
            return min(efficiency, 1.0)  # Cap at 100%
            
        except Exception as e:
            self.logger.error("Error calculating pattern efficiency: %s", e)
            return 0.0