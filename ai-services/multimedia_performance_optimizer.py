#!/usr/bin/env python3
"""
Multimedia Performance Optimizer for Smart File Manager v4.0
Advanced caching, memory management, and performance optimization
"""

import os
import time
import json
import logging
import hashlib
import threading
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import sqlite3
import psutil
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import weakref
import gc

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    data: Any
    created_at: float
    expires_at: float
    size_bytes: int
    access_count: int = 0
    last_accessed: float = 0


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    processing_time_total: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    active_threads: int = 0
    queue_size: int = 0


class LRUCache:
    """
    Advanced LRU cache with size limits and expiration
    """
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 512):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []
        self.current_memory_bytes = 0
        self.lock = threading.RLock()
        
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            
            # Check expiration
            if time.time() > entry.expires_at:
                self._remove_key(key)
                return None
            
            # Update access info
            entry.access_count += 1
            entry.last_accessed = time.time()
            
            # Move to end (most recently used)
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            
            return entry.data
    
    def put(self, key: str, data: Any, ttl_seconds: int = 3600) -> bool:
        """Put item in cache"""
        with self.lock:
            # Calculate data size
            try:
                size_bytes = len(json.dumps(data, default=str).encode())
            except:
                size_bytes = 1024  # Default estimate
            
            # Check if item is too large
            if size_bytes > self.max_memory_bytes:
                return False
            
            expires_at = time.time() + ttl_seconds
            
            # Remove existing entry if updating
            if key in self.cache:
                self._remove_key(key)
            
            # Ensure we have space
            while (len(self.cache) >= self.max_size or 
                   self.current_memory_bytes + size_bytes > self.max_memory_bytes):
                if not self._evict_lru():
                    break
            
            # Add new entry
            entry = CacheEntry(
                key=key,
                data=data,
                created_at=time.time(),
                expires_at=expires_at,
                size_bytes=size_bytes,
                last_accessed=time.time()
            )
            
            self.cache[key] = entry
            self.access_order.append(key)
            self.current_memory_bytes += size_bytes
            
            return True
    
    def _remove_key(self, key: str):
        """Remove key from cache"""
        if key in self.cache:
            entry = self.cache[key]
            self.current_memory_bytes -= entry.size_bytes
            del self.cache[key]
        
        if key in self.access_order:
            self.access_order.remove(key)
    
    def _evict_lru(self) -> bool:
        """Evict least recently used item"""
        if not self.access_order:
            return False
        
        # Find oldest expired item first
        current_time = time.time()
        for key in self.access_order:
            entry = self.cache[key]
            if current_time > entry.expires_at:
                self._remove_key(key)
                return True
        
        # If no expired items, evict LRU
        lru_key = self.access_order[0]
        self._remove_key(lru_key)
        return True
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
            self.current_memory_bytes = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_accesses = sum(entry.access_count for entry in self.cache.values())
            
            return {
                "entries": len(self.cache),
                "memory_usage_mb": self.current_memory_bytes / (1024 * 1024),
                "memory_limit_mb": self.max_memory_bytes / (1024 * 1024),
                "total_accesses": total_accesses,
                "average_entry_size": (self.current_memory_bytes / len(self.cache)) if self.cache else 0
            }


class MultimediaPerformanceOptimizer:
    """
    Advanced performance optimizer for multimedia processing
    """
    
    def __init__(self, 
                 cache_dir: str = "/tmp/multimedia_cache",
                 max_workers: int = 4,
                 enable_gpu: bool = True):
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_workers = max_workers
        self.enable_gpu = enable_gpu
        
        # Initialize caches for different types of data
        self.ai_analysis_cache = LRUCache(max_size=1000, max_memory_mb=256)
        self.thumbnail_cache = LRUCache(max_size=2000, max_memory_mb=128)
        self.metadata_cache = LRUCache(max_size=5000, max_memory_mb=64)
        self.stt_cache = LRUCache(max_size=500, max_memory_mb=512)
        
        # Performance tracking
        self.metrics = PerformanceMetrics()
        self.start_time = time.time()
        
        # Thread pools for different types of processing
        self.io_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.cpu_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.gpu_executor = ThreadPoolExecutor(max_workers=2) if enable_gpu else None
        
        # Processing queues
        self.priority_queue = []
        self.batch_queue = []
        self.queue_lock = threading.Lock()
        
        # Model memory management
        self.loaded_models = weakref.WeakValueDictionary()
        self.model_usage = {}
        
        # Background monitoring
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_performance, daemon=True)
        self.monitor_thread.start()
        
        logger.info("✅ Multimedia Performance Optimizer initialized")
    
    def cache_ai_analysis(self, file_path: str, analysis_type: str, data: Any, ttl: int = 7200) -> bool:
        """Cache AI analysis results"""
        cache_key = f"ai_analysis:{self._get_file_cache_key(file_path)}:{analysis_type}"
        return self.ai_analysis_cache.put(cache_key, data, ttl)
    
    def get_ai_analysis(self, file_path: str, analysis_type: str) -> Optional[Any]:
        """Get cached AI analysis results"""
        cache_key = f"ai_analysis:{self._get_file_cache_key(file_path)}:{analysis_type}"
        result = self.ai_analysis_cache.get(cache_key)
        
        if result:
            self.metrics.cache_hits += 1
        else:
            self.metrics.cache_misses += 1
        
        return result
    
    def cache_thumbnail(self, file_path: str, thumbnail_data: bytes, size: str = "medium") -> bool:
        """Cache thumbnail data"""
        cache_key = f"thumbnail:{self._get_file_cache_key(file_path)}:{size}"
        return self.thumbnail_cache.put(cache_key, thumbnail_data, 86400)  # 24 hours
    
    def get_thumbnail(self, file_path: str, size: str = "medium") -> Optional[bytes]:
        """Get cached thumbnail"""
        cache_key = f"thumbnail:{self._get_file_cache_key(file_path)}:{size}"
        return self.thumbnail_cache.get(cache_key)
    
    def cache_stt_result(self, audio_file: str, language: str, text: str, confidence: float) -> bool:
        """Cache speech-to-text results"""
        cache_key = f"stt:{self._get_file_cache_key(audio_file)}:{language}"
        data = {"text": text, "confidence": confidence, "timestamp": time.time()}
        return self.stt_cache.put(cache_key, data, 604800)  # 7 days
    
    def get_stt_result(self, audio_file: str, language: str) -> Optional[Dict[str, Any]]:
        """Get cached STT results"""
        cache_key = f"stt:{self._get_file_cache_key(audio_file)}:{language}"
        return self.stt_cache.get(cache_key)
    
    def cache_metadata(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """Cache file metadata"""
        cache_key = f"metadata:{self._get_file_cache_key(file_path)}"
        return self.metadata_cache.put(cache_key, metadata, 3600)  # 1 hour
    
    def get_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get cached metadata"""
        cache_key = f"metadata:{self._get_file_cache_key(file_path)}"
        return self.metadata_cache.get(cache_key)
    
    def _get_file_cache_key(self, file_path: str) -> str:
        """Generate cache key for file"""
        try:
            stat = os.stat(file_path)
            content = f"{file_path}:{stat.st_mtime}:{stat.st_size}"
            return hashlib.md5(content.encode()).hexdigest()
        except:
            return hashlib.md5(file_path.encode()).hexdigest()
    
    async def process_with_optimization(self, 
                                      task_func: Callable,
                                      *args, 
                                      priority: str = "normal",
                                      cache_key: Optional[str] = None,
                                      cache_ttl: int = 3600,
                                      **kwargs) -> Any:
        """
        Process task with automatic optimization and caching
        """
        start_time = time.time()
        self.metrics.total_requests += 1
        
        # Check cache first
        if cache_key:
            cached_result = self._get_from_any_cache(cache_key)
            if cached_result is not None:
                self.metrics.cache_hits += 1
                return cached_result
        
        # Select appropriate executor
        if hasattr(task_func, '__name__'):
            func_name = task_func.__name__
            if 'ai_' in func_name or 'vision' in func_name:
                executor = self.gpu_executor if self.gpu_executor else self.cpu_executor
            elif 'io' in func_name or 'file' in func_name:
                executor = self.io_executor
            else:
                executor = self.cpu_executor
        else:
            executor = self.cpu_executor
        
        # Execute task
        try:
            if asyncio.iscoroutinefunction(task_func):
                result = await task_func(*args, **kwargs)
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(executor, task_func, *args, **kwargs)
            
            # Cache result
            if cache_key and result is not None:
                self._put_to_appropriate_cache(cache_key, result, cache_ttl)
            
            # Update metrics
            processing_time = time.time() - start_time
            self.metrics.processing_time_total += processing_time
            
            return result
            
        except Exception as e:
            logger.error(f"Task processing failed: {e}")
            raise
    
    def _get_from_any_cache(self, cache_key: str) -> Optional[Any]:
        """Get from appropriate cache based on key prefix"""
        if cache_key.startswith("ai_"):
            return self.ai_analysis_cache.get(cache_key)
        elif cache_key.startswith("thumbnail"):
            return self.thumbnail_cache.get(cache_key)
        elif cache_key.startswith("stt"):
            return self.stt_cache.get(cache_key)
        elif cache_key.startswith("metadata"):
            return self.metadata_cache.get(cache_key)
        return None
    
    def _put_to_appropriate_cache(self, cache_key: str, data: Any, ttl: int):
        """Put to appropriate cache based on key prefix"""
        if cache_key.startswith("ai_"):
            self.ai_analysis_cache.put(cache_key, data, ttl)
        elif cache_key.startswith("thumbnail"):
            self.thumbnail_cache.put(cache_key, data, ttl)
        elif cache_key.startswith("stt"):
            self.stt_cache.put(cache_key, data, ttl)
        elif cache_key.startswith("metadata"):
            self.metadata_cache.put(cache_key, data, ttl)
    
    def optimize_memory_usage(self):
        """Optimize memory usage by cleaning up unused resources"""
        try:
            # Force garbage collection
            gc.collect()
            
            # Clean expired cache entries
            current_time = time.time()
            
            for cache in [self.ai_analysis_cache, self.thumbnail_cache, 
                         self.metadata_cache, self.stt_cache]:
                with cache.lock:
                    expired_keys = []
                    for key, entry in cache.cache.items():
                        if current_time > entry.expires_at:
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        cache._remove_key(key)
            
            # Unload unused AI models (simplified - depends on implementation)
            current_time = time.time()
            unused_models = []
            
            for model_name, last_used in self.model_usage.items():
                if current_time - last_used > 3600:  # 1 hour
                    unused_models.append(model_name)
            
            for model_name in unused_models:
                if model_name in self.loaded_models:
                    del self.loaded_models[model_name]
                del self.model_usage[model_name]
            
            logger.info(f"Memory optimization complete. Freed {len(unused_models)} models")
            
        except Exception as e:
            logger.warning(f"Memory optimization failed: {e}")
    
    def _monitor_performance(self):
        """Background performance monitoring"""
        while self.monitoring_active:
            try:
                # Update system metrics
                self.metrics.memory_usage_mb = psutil.virtual_memory().used / (1024 * 1024)
                self.metrics.cpu_usage_percent = psutil.cpu_percent(interval=1)
                self.metrics.active_threads = threading.active_count()
                
                # Optimize memory if usage is high
                if psutil.virtual_memory().percent > 80:
                    self.optimize_memory_usage()
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.warning(f"Performance monitoring error: {e}")
                time.sleep(60)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        uptime = time.time() - self.start_time
        
        cache_stats = {
            "ai_analysis": self.ai_analysis_cache.get_stats(),
            "thumbnails": self.thumbnail_cache.get_stats(),
            "metadata": self.metadata_cache.get_stats(),
            "stt": self.stt_cache.get_stats()
        }
        
        return {
            "uptime_seconds": uptime,
            "metrics": asdict(self.metrics),
            "cache_statistics": cache_stats,
            "system_resources": {
                "memory_usage_mb": self.metrics.memory_usage_mb,
                "cpu_usage_percent": self.metrics.cpu_usage_percent,
                "active_threads": self.metrics.active_threads
            },
            "processing_efficiency": {
                "cache_hit_rate": (self.metrics.cache_hits / 
                                 max(self.metrics.cache_hits + self.metrics.cache_misses, 1)),
                "average_processing_time": (self.metrics.processing_time_total / 
                                          max(self.metrics.total_requests, 1)),
                "requests_per_second": self.metrics.total_requests / max(uptime, 1)
            }
        }
    
    def clear_all_caches(self):
        """Clear all caches"""
        self.ai_analysis_cache.clear()
        self.thumbnail_cache.clear()
        self.metadata_cache.clear()
        self.stt_cache.clear()
        
        logger.info("All caches cleared")
    
    def shutdown(self):
        """Shutdown optimizer and cleanup resources"""
        self.monitoring_active = False
        
        # Shutdown executors
        self.io_executor.shutdown(wait=True)
        self.cpu_executor.shutdown(wait=True)
        if self.gpu_executor:
            self.gpu_executor.shutdown(wait=True)
        
        # Clear caches
        self.clear_all_caches()
        
        logger.info("Performance optimizer shutdown complete")


# Global optimizer instance
_performance_optimizer = None


def get_performance_optimizer() -> MultimediaPerformanceOptimizer:
    """Get global performance optimizer instance"""
    global _performance_optimizer
    
    if _performance_optimizer is None:
        cache_dir = os.environ.get("MULTIMEDIA_CACHE_PATH", "/tmp/multimedia_cache")
        max_workers = int(os.environ.get("WORKER_PROCESSES", 4))
        enable_gpu = os.environ.get("ENABLE_GPU", "true").lower() == "true"
        
        _performance_optimizer = MultimediaPerformanceOptimizer(
            cache_dir=cache_dir,
            max_workers=max_workers,
            enable_gpu=enable_gpu
        )
    
    return _performance_optimizer


def test_performance_optimizer():
    """Test performance optimizer functionality"""
    optimizer = MultimediaPerformanceOptimizer()
    
    print("⚡ Performance Optimizer Test")
    print("=" * 40)
    
    # Test caching
    test_data = {"test": "data", "number": 42}
    
    # AI analysis cache
    print("Testing AI analysis cache...")
    success = optimizer.cache_ai_analysis("/test/file.jpg", "image", test_data)
    print(f"   Cache put: {'✅' if success else '❌'}")
    
    retrieved = optimizer.get_ai_analysis("/test/file.jpg", "image")
    print(f"   Cache get: {'✅' if retrieved == test_data else '❌'}")
    
    # Performance stats
    print("\n📊 Performance Statistics:")
    stats = optimizer.get_performance_stats()
    
    for category, data in stats.items():
        if isinstance(data, dict):
            print(f"   {category}:")
            for key, value in data.items():
                if isinstance(value, float):
                    print(f"      {key}: {value:.3f}")
                else:
                    print(f"      {key}: {value}")
        else:
            print(f"   {category}: {data}")
    
    # Cleanup
    optimizer.shutdown()
    print("\n✅ Performance optimizer test complete")


if __name__ == "__main__":
    test_performance_optimizer()