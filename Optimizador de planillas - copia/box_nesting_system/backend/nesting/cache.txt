"""
Caching system for nesting results to improve performance.
"""

import time
import logging
from typing import Any, Optional, Dict, Tuple
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Represents a single cache entry."""
    pattern_data: Any
    cache_key: Any
    timestamp: float
    access_count: int = 0


class NestingCache:
    """
    Advanced caching system for nesting calculation results.
    
    Provides intelligent caching with invalidation and performance tracking.
    """
    
    def __init__(self, max_size: int = 100, validity_period: float = 3600):
        """
        Initialize caching system.
        
        Args:
            max_size: Maximum number of cache entries
            validity_period: Cache validity period in seconds
        """
        self.max_size = max_size
        self.validity_period = validity_period
        self.cache: Dict[Any, CacheEntry] = {}
        self.logger = logging.getLogger(__name__)
        self.hit_count = 0
        self.miss_count = 0
        # Compatibilidad con la interfaz simple usada por el c�digo original
        self.pattern_data = None
        self.cache_key = None

    def clear(self) -> None:
        """Clear all cached data and reset statistics."""
        self.cache.clear()
        self.hit_count = 0
        self.miss_count = 0
        self.pattern_data = None
        self.cache_key = None
        self.logger.debug("Cache cleared")

    def is_valid(self, cache_key: Any) -> bool:
        """
        Check if cache entry is valid for current key.
        
        Args:
            cache_key: Key representing current parameters
            
        Returns:
            True if cache is valid and not expired
        """
        if cache_key not in self.cache:
            self.miss_count += 1
            if self.cache_key == cache_key:
                self.pattern_data = None
                self.cache_key = None
            self.logger.debug("Cache miss (key not found): %s", cache_key)
            return False
            
        entry = self.cache[cache_key]
        current_time = time.time()
        
        # Check if entry has expired
        if current_time - entry.timestamp > self.validity_period:
            del self.cache[cache_key]
            self.miss_count += 1
            if self.cache_key == cache_key:
                self.pattern_data = None
                self.cache_key = None
            self.logger.debug("Cache entry expired for key: %s", cache_key)
            return False
            
        entry.access_count += 1
        self.hit_count += 1
        self.logger.debug("Cache hit for key: %s (access_count=%d)", cache_key, entry.access_count)
        return True

    def get(self, cache_key: Any) -> Optional[Any]:
        """
        Retrieve cached data for key.
        
        Args:
            cache_key: Cache key to retrieve
            
        Returns:
            Cached data or None if not found/invalid
        """
        if not self.is_valid(cache_key):
            return None
            
        return self.cache[cache_key].pattern_data

    def store(self, pattern_data: Any, cache_key: Any) -> None:
        """
        Store pattern data with cache key.
        
        Args:
            pattern_data: Calculated pattern data
            cache_key: Key representing parameters
        """
        # Evict least recently used if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_lru()
            
        entry = CacheEntry(
            pattern_data=pattern_data,
            cache_key=cache_key,
            timestamp=time.time()
        )
        self.cache[cache_key] = entry
        # Mantener compatibilidad con la l�gica que consulta pattern_data directamente
        self.pattern_data = pattern_data
        self.cache_key = cache_key
        self.logger.debug("Stored cache entry for key: %s", cache_key)

    def _evict_lru(self) -> None:
        """Evict least recently used cache entry."""
        if not self.cache:
            return
            
        lru_key = min(self.cache.keys(), 
                     key=lambda k: self.cache[k].access_count)
        del self.cache[lru_key]
        if self.cache_key == lru_key:
            self.pattern_data = None
            self.cache_key = None
        self.logger.debug("Evicted LRU cache entry: %s", lru_key)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.hit_count + self.miss_count
        hit_ratio = self.hit_count / total_requests if total_requests > 0 else 0
        
        return {
            'total_entries': len(self.cache),
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_ratio': hit_ratio,
            'max_size': self.max_size
        }

    def invalidate_pattern(self, pattern: Any) -> None:
        """
        Invalidate cache entries matching pattern.
        
        Args:
            pattern: Pattern to match for invalidation
        """
        keys_to_remove = [
            key for key, entry in self.cache.items()
            if self._matches_pattern(entry.pattern_data, pattern)
        ]
        
        for key in keys_to_remove:
            del self.cache[key]
            if self.cache_key == key:
                self.pattern_data = None
                self.cache_key = None
            
        self.logger.debug("Invalidated %d cache entries for pattern: %s", 
                         len(keys_to_remove), pattern)

    def _matches_pattern(self, data: Any, pattern: Any) -> bool:
        """
        Check if data matches invalidation pattern.
        
        Args:
            data: Cached data
            pattern: Pattern to match
            
        Returns:
            True if data matches pattern
        """
        # Simple pattern matching - can be extended as needed
        if isinstance(pattern, type) and isinstance(data, pattern):
            return True
        if hasattr(data, '__dict__') and hasattr(pattern, '__dict__'):
            return data.__dict__ == pattern.__dict__
        return data == pattern
