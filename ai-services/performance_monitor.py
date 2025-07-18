"""
Performance Monitor for Smart File Manager
시스템 성능 모니터링 및 메트릭 수집
"""

import time
import psutil
import threading
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """성능 메트릭 데이터 클래스"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int = 0
    api_requests_per_minute: int = 0
    search_latency_ms: float = 0.0
    indexing_rate_files_per_minute: int = 0

@dataclass
class ApiMetric:
    """API 성능 메트릭"""
    endpoint: str
    method: str
    status_code: int
    duration_ms: float
    timestamp: float
    error_message: Optional[str] = None

class PerformanceMonitor:
    """성능 모니터링 클래스"""
    
    def __init__(self, collection_interval: int = 30, retention_hours: int = 24):
        self.collection_interval = collection_interval
        self.retention_hours = retention_hours
        self.is_running = False
        
        # 메트릭 저장소
        self.system_metrics: deque = deque(maxlen=int(retention_hours * 3600 / collection_interval))
        self.api_metrics: deque = deque(maxlen=10000)  # 최근 10,000개 API 호출
        self.search_metrics: deque = deque(maxlen=1000)  # 최근 1,000개 검색
        
        # 실시간 카운터
        self.api_counter = defaultdict(int)
        self.error_counter = defaultdict(int)
        self.search_times = deque(maxlen=100)
        self.general_counters = defaultdict(int)
        
        # 스레드
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.RLock()
        
        # 초기 네트워크/디스크 상태
        self.last_net_io = psutil.net_io_counters()
        self.last_disk_io = psutil.disk_io_counters()
        self.last_check_time = time.time()
        
        logger.info("Performance monitor initialized")
    
    def start(self):
        """모니터링 시작"""
        if not self.is_running:
            self.is_running = True
            self.monitor_thread = threading.Thread(target=self._monitor_worker, daemon=True)
            self.monitor_thread.start()
            logger.info("Performance monitoring started")
    
    def stop(self):
        """모니터링 중지"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
    
    def _monitor_worker(self):
        """모니터링 워커 스레드"""
        while self.is_running:
            try:
                self._collect_system_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                time.sleep(self.collection_interval)
    
    def _collect_system_metrics(self):
        """시스템 메트릭 수집"""
        try:
            current_time = time.time()
            
            # CPU 및 메모리
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # 디스크
            disk_usage = psutil.disk_usage('/')
            
            # 네트워크 및 디스크 I/O (델타 계산)
            current_net_io = psutil.net_io_counters()
            current_disk_io = psutil.disk_io_counters()
            time_delta = current_time - self.last_check_time
            
            if time_delta > 0:
                net_sent_rate = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / time_delta / 1024 / 1024
                net_recv_rate = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / time_delta / 1024 / 1024
                disk_read_rate = (current_disk_io.read_bytes - self.last_disk_io.read_bytes) / time_delta / 1024 / 1024
                disk_write_rate = (current_disk_io.write_bytes - self.last_disk_io.write_bytes) / time_delta / 1024 / 1024
            else:
                net_sent_rate = net_recv_rate = disk_read_rate = disk_write_rate = 0.0
            
            # API 요청 수 (분당)
            api_requests = sum(self.api_counter.values())
            
            # 평균 검색 지연시간
            avg_search_latency = sum(self.search_times) / len(self.search_times) if self.search_times else 0.0
            
            # 메트릭 객체 생성
            metric = PerformanceMetric(
                timestamp=current_time,
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                disk_usage_percent=disk_usage.percent,
                disk_io_read_mb=disk_read_rate,
                disk_io_write_mb=disk_write_rate,
                network_sent_mb=net_sent_rate,
                network_recv_mb=net_recv_rate,
                api_requests_per_minute=api_requests,
                search_latency_ms=avg_search_latency
            )
            
            with self.lock:
                self.system_metrics.append(metric)
                # 1분마다 API 카운터 리셋
                if int(current_time) % 60 == 0:
                    self.api_counter.clear()
            
            # 상태 업데이트
            self.last_net_io = current_net_io
            self.last_disk_io = current_disk_io
            self.last_check_time = current_time
            
            logger.debug(f"Collected metrics: CPU {cpu_percent}%, Memory {memory.percent}%")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def record_api_call(self, endpoint: str, method: str, status_code: int, 
                       duration_ms: float, error_message: Optional[str] = None):
        """API 호출 기록"""
        try:
            metric = ApiMetric(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                duration_ms=duration_ms,
                timestamp=time.time(),
                error_message=error_message
            )
            
            with self.lock:
                self.api_metrics.append(metric)
                self.api_counter[f"{method} {endpoint}"] += 1
                
                if status_code >= 400:
                    self.error_counter[f"{status_code}"] += 1
            
            logger.debug(f"Recorded API call: {method} {endpoint} - {status_code} ({duration_ms}ms)")
            
        except Exception as e:
            logger.error(f"Error recording API call: {e}")
    
    def increment_counter(self, counter_name: str, value: int = 1):
        """일반 카운터 증가"""
        try:
            with self.lock:
                self.general_counters[counter_name] += value
            logger.debug(f"Incremented counter {counter_name} by {value}")
        except Exception as e:
            logger.error(f"Error incrementing counter {counter_name}: {e}")
    
    def get_counter(self, counter_name: str) -> int:
        """카운터 값 조회"""
        with self.lock:
            return self.general_counters.get(counter_name, 0)
    
    def record_timing(self, operation: str, duration_ms: float):
        """작업 수행 시간 기록"""
        try:
            # API 메트릭에 기록 (status_code는 200으로 가정)
            self.record_api_call(operation, "INTERNAL", 200, duration_ms)
            logger.debug(f"Recorded timing for {operation}: {duration_ms}ms")
        except Exception as e:
            logger.error(f"Error recording timing for {operation}: {e}")
    
    def record_search(self, query: str, result_count: int, duration_ms: float, method: str = "unknown"):
        """검색 성능 기록"""
        try:
            search_metric = {
                "query": query[:100],  # 처음 100자만 저장
                "result_count": result_count,
                "duration_ms": duration_ms,
                "method": method,
                "timestamp": time.time()
            }
            
            with self.lock:
                self.search_metrics.append(search_metric)
                self.search_times.append(duration_ms)
            
            logger.debug(f"Recorded search: {result_count} results in {duration_ms}ms")
            
        except Exception as e:
            logger.error(f"Error recording search metric: {e}")
    
    def get_current_stats(self) -> Dict[str, Any]:
        """현재 시스템 상태 반환"""
        try:
            if not self.system_metrics:
                return {"status": "no_data"}
            
            latest = self.system_metrics[-1]
            
            with self.lock:
                recent_errors = sum(self.error_counter.values())
                total_api_calls = sum(self.api_counter.values())
                avg_search_time = sum(self.search_times) / len(self.search_times) if self.search_times else 0
            
            return {
                "timestamp": latest.timestamp,
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "memory_used_mb": latest.memory_used_mb,
                "disk_usage_percent": latest.disk_usage_percent,
                "api_requests_per_minute": total_api_calls,
                "recent_errors": recent_errors,
                "avg_search_latency_ms": avg_search_time,
                "total_searches": len(self.search_metrics),
                "status": "healthy" if latest.cpu_percent < 80 and latest.memory_percent < 80 else "warning"
            }
            
        except Exception as e:
            logger.error(f"Error getting current stats: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_historical_data(self, hours: int = 1) -> Dict[str, List]:
        """시간별 히스토리 데이터 반환"""
        try:
            cutoff_time = time.time() - (hours * 3600)
            
            with self.lock:
                recent_metrics = [
                    asdict(metric) for metric in self.system_metrics 
                    if metric.timestamp >= cutoff_time
                ]
                
                recent_api_calls = [
                    asdict(metric) for metric in self.api_metrics 
                    if metric.timestamp >= cutoff_time
                ]
                
                recent_searches = [
                    metric for metric in self.search_metrics 
                    if metric["timestamp"] >= cutoff_time
                ]
            
            return {
                "system_metrics": recent_metrics,
                "api_metrics": recent_api_calls,
                "search_metrics": recent_searches
            }
            
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return {"system_metrics": [], "api_metrics": [], "search_metrics": []}
    
    def get_health_status(self) -> Dict[str, Any]:
        """시스템 건강 상태 반환"""
        try:
            current_stats = self.get_current_stats()
            if current_stats.get("status") == "error":
                return {"status": "unhealthy", "details": current_stats}
            
            # 기본적인 건강 상태 체크
            cpu_ok = current_stats.get("cpu_percent", 0) < 90
            memory_ok = current_stats.get("memory_percent", 0) < 90
            
            if cpu_ok and memory_ok:
                return {"status": "healthy", "timestamp": time.time()}
            else:
                return {
                    "status": "warning", 
                    "timestamp": time.time(),
                    "issues": {
                        "high_cpu": not cpu_ok,
                        "high_memory": not memory_ok
                    }
                }
        except Exception as e:
            logger.error(f"Error checking health status: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """성능 요약 리포트"""
        try:
            if not self.system_metrics:
                return {"status": "no_data"}
            
            # 최근 1시간 데이터
            recent_data = self.get_historical_data(1)
            system_metrics = recent_data["system_metrics"]
            api_metrics = recent_data["api_metrics"]
            search_metrics = recent_data["search_metrics"]
            
            if not system_metrics:
                return {"status": "insufficient_data"}
            
            # 시스템 메트릭 통계
            cpu_values = [m["cpu_percent"] for m in system_metrics]
            memory_values = [m["memory_percent"] for m in system_metrics]
            
            # API 성능 통계
            api_durations = [m["duration_ms"] for m in api_metrics]
            error_rate = len([m for m in api_metrics if m["status_code"] >= 400]) / len(api_metrics) if api_metrics else 0
            
            # 검색 성능 통계
            search_durations = [m["duration_ms"] for m in search_metrics]
            
            return {
                "period_hours": 1,
                "system_performance": {
                    "avg_cpu_percent": sum(cpu_values) / len(cpu_values),
                    "max_cpu_percent": max(cpu_values),
                    "avg_memory_percent": sum(memory_values) / len(memory_values),
                    "max_memory_percent": max(memory_values)
                },
                "api_performance": {
                    "total_requests": len(api_metrics),
                    "avg_response_time_ms": sum(api_durations) / len(api_durations) if api_durations else 0,
                    "error_rate_percent": error_rate * 100,
                    "requests_per_minute": len(api_metrics) / 60
                },
                "search_performance": {
                    "total_searches": len(search_metrics),
                    "avg_search_time_ms": sum(search_durations) / len(search_durations) if search_durations else 0,
                    "searches_per_minute": len(search_metrics) / 60
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")
            return {"status": "error", "message": str(e)}
    
    def export_metrics(self, filepath: str, hours: int = 24):
        """메트릭을 파일로 내보내기"""
        try:
            data = self.get_historical_data(hours)
            data["export_timestamp"] = time.time()
            data["export_period_hours"] = hours
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Metrics exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            raise
    
    def cleanup_old_data(self):
        """오래된 데이터 정리"""
        try:
            cutoff_time = time.time() - (self.retention_hours * 3600)
            
            with self.lock:
                # deque는 maxlen으로 자동 관리되지만, 명시적으로 정리
                while (self.api_metrics and 
                       self.api_metrics[0].timestamp < cutoff_time):
                    self.api_metrics.popleft()
                
                # 검색 메트릭 정리
                while (self.search_metrics and 
                       self.search_metrics[0]["timestamp"] < cutoff_time):
                    self.search_metrics.popleft()
            
            logger.debug("Cleaned up old performance data")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary for the dashboard"""
        try:
            # Get current system metrics
            current_metrics = self.get_current_stats()
            
            # Get historical data for the last hour
            historical = self.get_historical_data(hours=1)
            
            # Calculate averages
            system_metrics = historical.get("system_metrics", [])
            if system_metrics:
                avg_cpu = sum(m["cpu_percent"] for m in system_metrics) / len(system_metrics)
                avg_memory = sum(m["memory_percent"] for m in system_metrics) / len(system_metrics)
                avg_disk = sum(m["disk_usage_percent"] for m in system_metrics) / len(system_metrics)
            else:
                avg_cpu = current_metrics.get("cpu_percent", 0)
                avg_memory = current_metrics.get("memory_percent", 0)
                avg_disk = current_metrics.get("disk_usage_percent", 0)
            
            # Structure data to match Dashboard expectations
            return {
                "system_metrics": {
                    "cpu_percent": {
                        "current": current_metrics.get("cpu_percent", 0),
                        "average": round(avg_cpu, 2)
                    },
                    "memory_percent": {
                        "current": current_metrics.get("memory_percent", 0),
                        "average": round(avg_memory, 2)
                    },
                    "disk_usage": {
                        "current": current_metrics.get("disk_usage_percent", 0),
                        "average": round(avg_disk, 2)
                    }
                },
                "api_metrics": {
                    "total_requests": current_metrics.get("api_requests_per_minute", 0),
                    "error_count": current_metrics.get("recent_errors", 0),
                    "avg_latency": current_metrics.get("avg_search_latency_ms", 0)
                },
                "counters": dict(self.general_counters),
                "health": self.get_health_status(),
                "timestamp": current_metrics.get("timestamp", time.time())
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {
                "error": str(e),
                "system_metrics": {
                    "cpu_percent": {"current": 0, "average": 0},
                    "memory_percent": {"current": 0, "average": 0},
                    "disk_usage": {"current": 0, "average": 0}
                },
                "api_metrics": {
                    "total_requests": 0,
                    "error_count": 0,
                    "avg_latency": 0
                },
                "counters": {},
                "health": {"status": "error"}
            }
    
    def get_database_metrics(self) -> Dict[str, Any]:
        """Get database-specific metrics"""
        try:
            # Basic database metrics
            db_stats = {
                "indexed_files": self.get_counter("indexed_files"),
                "failed_files": self.get_counter("failed_files"),
                "total_embeddings": self.get_counter("total_embeddings"),
                "search_requests": self.get_counter("search_requests"),
                "database_size_mb": self.get_counter("database_size_mb")
            }
            
            # Recent activity
            recent_activity = {
                "files_indexed_last_hour": self.get_counter("files_indexed_last_hour"),
                "searches_last_hour": len([s for s in self.search_metrics if s["timestamp"] > time.time() - 3600])
            }
            
            return {
                "stats": db_stats,
                "activity": recent_activity,
                "health": "healthy"
            }
            
        except Exception as e:
            logger.error(f"Error getting database metrics: {e}")
            return {
                "error": str(e),
                "stats": {},
                "activity": {},
                "health": "error"
            }

# 전역 인스턴스
performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """성능 모니터 싱글톤 인스턴스 반환"""
    global performance_monitor
    if performance_monitor is None:
        performance_monitor = PerformanceMonitor()
        performance_monitor.start()
    return performance_monitor

def record_api_performance(endpoint: str, method: str, status_code: int, duration_ms: float):
    """API 성능 기록 헬퍼 함수"""
    monitor = get_performance_monitor()
    monitor.record_api_call(endpoint, method, status_code, duration_ms)

def record_search_performance(query: str, result_count: int, duration_ms: float, method: str = "fts"):
    """검색 성능 기록 헬퍼 함수"""
    monitor = get_performance_monitor()
    monitor.record_search(query, result_count, duration_ms, method)
