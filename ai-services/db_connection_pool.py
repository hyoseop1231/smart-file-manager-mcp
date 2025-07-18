"""
Database Connection Pool Manager
데이터베이스 연결 풀 관리 및 최적화
"""

import sqlite3
import threading
import time
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from queue import Queue, Empty
import os

logger = logging.getLogger(__name__)

class ConnectionPool:
    """SQLite 연결 풀 클래스"""
    
    def __init__(self, db_path: str, max_connections: int = 10, 
                 max_idle_time: int = 300, check_interval: int = 60):
        self.db_path = db_path
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self.check_interval = check_interval
        
        self._pool = Queue(maxsize=max_connections)
        self._all_connections = set()
        self._connection_times = {}
        self._lock = threading.RLock()
        self._shutdown = False
        
        # 초기 연결 생성
        self._initialize_pool()
        
        # 정리 스레드 시작
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        
        logger.info(f"Connection pool initialized with {max_connections} max connections")
    
    def _initialize_pool(self):
        """연결 풀 초기화"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # 최소 연결 수만큼 미리 생성
            initial_connections = min(3, self.max_connections)
            for _ in range(initial_connections):
                conn = self._create_connection()
                if conn:
                    self._pool.put(conn)
                    
        except Exception as e:
            logger.error(f"Error initializing connection pool: {e}")
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """새 데이터베이스 연결 생성"""
        try:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30
            )
            
            # SQLite 최적화 설정
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB
            
            # Row factory 설정 - Dictionary-like Row with .get() method support
            def dict_row_factory(cursor, row):
                """Custom row factory that supports both dict-style access and .get() method"""
                columns = [col[0] for col in cursor.description]
                row_dict = dict(zip(columns, row))
                
                class DictRow(dict):
                    def keys(self):
                        return super().keys()
                    
                    def get(self, key, default=None):
                        return super().get(key, default)
                    
                    def __contains__(self, key):
                        return super().__contains__(key)
                
                return DictRow(row_dict)
            
            conn.row_factory = dict_row_factory
            
            with self._lock:
                self._all_connections.add(conn)
                self._connection_times[conn] = time.time()
            
            logger.debug("New database connection created")
            return conn
            
        except Exception as e:
            logger.error(f"Error creating database connection: {e}")
            return None
    
    @contextmanager
    def get_connection(self, timeout: float = 10.0):
        """연결 풀에서 연결 가져오기 (컨텍스트 매니저)"""
        conn = None
        start_time = time.time()
        
        try:
            # 풀에서 연결 가져오기 시도
            try:
                conn = self._pool.get(timeout=timeout)
                logger.debug("Got connection from pool")
            except Empty:
                # 풀이 비어있으면 새 연결 생성
                if len(self._all_connections) < self.max_connections:
                    conn = self._create_connection()
                    if not conn:
                        raise Exception("Failed to create new connection")
                else:
                    raise Exception("Connection pool exhausted")
            
            # 연결 유효성 검사
            if not self._is_connection_valid(conn):
                logger.warning("Invalid connection detected, creating new one")
                self._close_connection(conn)
                conn = self._create_connection()
                if not conn:
                    raise Exception("Failed to create replacement connection")
            
            # 연결 사용 시간 업데이트
            with self._lock:
                self._connection_times[conn] = time.time()
            
            yield conn
            
        except Exception as e:
            logger.error(f"Error in connection management: {e}")
            if conn:
                self._close_connection(conn)
            raise
        finally:
            # 연결을 풀에 반환
            if conn and not self._shutdown:
                try:
                    if self._is_connection_valid(conn):
                        self._pool.put(conn, timeout=1.0)
                        logger.debug("Connection returned to pool")
                    else:
                        self._close_connection(conn)
                except Exception as e:
                    logger.warning(f"Error returning connection to pool: {e}")
                    self._close_connection(conn)
    
    def _is_connection_valid(self, conn: sqlite3.Connection) -> bool:
        """연결 유효성 검사"""
        try:
            conn.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    def _close_connection(self, conn: sqlite3.Connection):
        """연결 닫기"""
        try:
            with self._lock:
                if conn in self._all_connections:
                    self._all_connections.remove(conn)
                if conn in self._connection_times:
                    del self._connection_times[conn]
            
            conn.close()
            logger.debug("Connection closed")
            
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")
    
    def _cleanup_worker(self):
        """유휴 연결 정리 워커"""
        while not self._shutdown:
            try:
                time.sleep(self.check_interval)
                self._cleanup_idle_connections()
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
    
    def _cleanup_idle_connections(self):
        """유휴 연결 정리"""
        current_time = time.time()
        connections_to_close = []
        
        with self._lock:
            for conn, last_used in self._connection_times.items():
                if current_time - last_used > self.max_idle_time:
                    connections_to_close.append(conn)
        
        # 최소 연결 수는 유지
        min_connections = 2
        if len(self._all_connections) - len(connections_to_close) < min_connections:
            connections_to_close = connections_to_close[:-min_connections]
        
        for conn in connections_to_close:
            try:
                # 풀에서 제거 시도 (사용 중이면 스킵)
                temp_queue = Queue()
                found = False
                
                while not self._pool.empty():
                    try:
                        pool_conn = self._pool.get_nowait()
                        if pool_conn == conn:
                            found = True
                            break
                        else:
                            temp_queue.put(pool_conn)
                    except Empty:
                        break
                
                # 임시 큐의 연결들을 다시 풀에 넣기
                while not temp_queue.empty():
                    self._pool.put(temp_queue.get_nowait())
                
                if found:
                    self._close_connection(conn)
                    logger.debug("Closed idle connection")
                    
            except Exception as e:
                logger.warning(f"Error cleaning up idle connection: {e}")
    
    def execute_query(self, query: str, params: tuple = (), fetch_one: bool = False, 
                      fetch_all: bool = True) -> Any:
        """쿼리 실행 헬퍼 메서드"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    conn.commit()
                    return cursor.rowcount
                elif fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
                else:
                    return cursor
                    
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """배치 쿼리 실행"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"Error executing batch query: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """연결 풀 통계"""
        with self._lock:
            return {
                "total_connections": len(self._all_connections),
                "pool_size": self._pool.qsize(),
                "max_connections": self.max_connections,
                "active_connections": len(self._all_connections) - self._pool.qsize(),
                "db_path": self.db_path
            }
    
    def close_all(self):
        """모든 연결 닫기"""
        self._shutdown = True
        
        # 풀의 모든 연결 닫기
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                self._close_connection(conn)
            except Empty:
                break
        
        # 나머지 연결들 닫기
        with self._lock:
            for conn in list(self._all_connections):
                self._close_connection(conn)
        
        logger.info("All database connections closed")

# 전역 연결 풀 인스턴스
_connection_pools: Dict[str, ConnectionPool] = {}
_pools_lock = threading.Lock()

def get_connection_pool(db_path: str, max_connections: int = 10) -> ConnectionPool:
    """연결 풀 싱글톤 팩토리"""
    with _pools_lock:
        if db_path not in _connection_pools:
            _connection_pools[db_path] = ConnectionPool(db_path, max_connections)
        return _connection_pools[db_path]

def close_all_pools():
    """모든 연결 풀 닫기"""
    with _pools_lock:
        for pool in _connection_pools.values():
            pool.close_all()
        _connection_pools.clear()
        logger.info("All connection pools closed")

# 컨텍스트 매니저로 사용할 수 있는 헬퍼
@contextmanager
def get_db_connection(db_path: str):
    """데이터베이스 연결 컨텍스트 매니저"""
    pool = get_connection_pool(db_path)
    with pool.get_connection() as conn:
        yield conn