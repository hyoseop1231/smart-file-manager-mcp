#!/usr/bin/env python3
"""
Enhanced Deletion Tracking Module for Smart File Manager
추가 기능: 삭제된 파일 추적 및 히스토리 관리
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class DeletionTracker:
    """삭제된 파일 추적 및 관리 클래스"""
    
    def __init__(self, db_path: str = "/data/file_index.db"):
        self.db_path = db_path
        self.init_deletion_tables()
    
    def init_deletion_tables(self):
        """삭제 추적을 위한 데이터베이스 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 삭제된 파일 히스토리 테이블
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS deleted_files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        original_path TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        file_size INTEGER,
                        file_type TEXT,
                        category TEXT,
                        deletion_reason TEXT,
                        deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        deleted_by TEXT DEFAULT 'system',
                        backup_path TEXT,
                        recovery_possible BOOLEAN DEFAULT 1,
                        metadata TEXT  -- JSON 형태로 추가 메타데이터 저장
                    )
                """)
                
                # 파일 이동 히스토리 테이블 (Archive 이동 추적)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS file_movements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        original_path TEXT NOT NULL,
                        new_path TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        movement_type TEXT, -- 'archive', 'reorganize', 'backup'
                        moved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        moved_by TEXT DEFAULT 'system',
                        reason TEXT,
                        file_size INTEGER,
                        metadata TEXT
                    )
                """)
                
                # 파일 복구 로그 테이블
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS recovery_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        deleted_file_id INTEGER,
                        recovery_path TEXT,
                        recovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        recovered_by TEXT,
                        recovery_status TEXT, -- 'success', 'failed', 'partial'
                        notes TEXT,
                        FOREIGN KEY (deleted_file_id) REFERENCES deleted_files (id)
                    )
                """)
                
                # 인덱스 생성
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_deleted_files_path ON deleted_files(original_path)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_deleted_files_date ON deleted_files(deleted_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_movements_date ON file_movements(moved_at)")
                
                conn.commit()
                logger.info("삭제 추적 테이블 초기화 완료")
                
        except Exception as e:
            logger.error(f"삭제 추적 테이블 초기화 실패: {e}")
    
    def track_deletion(self, 
                      file_path: str, 
                      reason: str = "user_action",
                      backup_path: Optional[str] = None,
                      metadata: Optional[Dict] = None) -> int:
        """파일 삭제 추적"""
        try:
            file_info = self._get_file_info(file_path)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO deleted_files 
                    (original_path, filename, file_size, file_type, category, 
                     deletion_reason, backup_path, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_path,
                    file_info['filename'],
                    file_info['size'],
                    file_info['type'],
                    file_info['category'],
                    reason,
                    backup_path,
                    json.dumps(metadata) if metadata else None
                ))
                
                deletion_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"파일 삭제 추적 완료: {file_path} (ID: {deletion_id})")
                return deletion_id
                
        except Exception as e:
            logger.error(f"파일 삭제 추적 실패: {e}")
            return -1
    
    def track_movement(self,
                      original_path: str,
                      new_path: str,
                      movement_type: str = "archive",
                      reason: str = "organization") -> int:
        """파일 이동 추적 (Archive 등)"""
        try:
            file_info = self._get_file_info(original_path)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO file_movements
                    (original_path, new_path, filename, movement_type, reason, file_size)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    original_path,
                    new_path,
                    file_info['filename'],
                    movement_type,
                    reason,
                    file_info['size']
                ))
                
                movement_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"파일 이동 추적 완료: {original_path} -> {new_path}")
                return movement_id
                
        except Exception as e:
            logger.error(f"파일 이동 추적 실패: {e}")
            return -1
    
    def get_recent_deletions(self, limit: int = 10) -> List[Dict]:
        """최근 삭제된 파일 목록 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, original_path, filename, file_size, file_type, 
                           deletion_reason, deleted_at, backup_path, recovery_possible
                    FROM deleted_files 
                    ORDER BY deleted_at DESC 
                    LIMIT ?
                """, (limit,))
                
                results = cursor.fetchall()
                
                deleted_files = []
                for row in results:
                    deleted_files.append({
                        'id': row[0],
                        'original_path': row[1],
                        'filename': row[2],
                        'file_size': row[3],
                        'file_type': row[4],
                        'deletion_reason': row[5],
                        'deleted_at': row[6],
                        'backup_path': row[7],
                        'recovery_possible': bool(row[8])
                    })
                
                return deleted_files
                
        except Exception as e:
            logger.error(f"최근 삭제 파일 조회 실패: {e}")
            return []
    
    def get_recent_movements(self, limit: int = 10) -> List[Dict]:
        """최근 파일 이동 목록 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, original_path, new_path, filename, movement_type,
                           moved_at, reason, file_size
                    FROM file_movements 
                    ORDER BY moved_at DESC 
                    LIMIT ?
                """, (limit,))
                
                results = cursor.fetchall()
                
                movements = []
                for row in results:
                    movements.append({
                        'id': row[0],
                        'original_path': row[1],
                        'new_path': row[2],
                        'filename': row[3],
                        'movement_type': row[4],
                        'moved_at': row[5],
                        'reason': row[6],
                        'file_size': row[7]
                    })
                
                return movements
                
        except Exception as e:
            logger.error(f"최근 파일 이동 조회 실패: {e}")
            return []
    
    def search_deleted_files(self, 
                           query: str = "", 
                           days_back: int = 30) -> List[Dict]:
        """삭제된 파일 검색"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 날짜 조건
                cutoff_date = datetime.now() - timedelta(days=days_back)
                
                if query:
                    cursor.execute("""
                        SELECT id, original_path, filename, file_size, file_type,
                               deletion_reason, deleted_at, backup_path, recovery_possible
                        FROM deleted_files 
                        WHERE (filename LIKE ? OR original_path LIKE ?)
                          AND deleted_at >= ?
                        ORDER BY deleted_at DESC
                    """, (f"%{query}%", f"%{query}%", cutoff_date.isoformat()))
                else:
                    cursor.execute("""
                        SELECT id, original_path, filename, file_size, file_type,
                               deletion_reason, deleted_at, backup_path, recovery_possible
                        FROM deleted_files 
                        WHERE deleted_at >= ?
                        ORDER BY deleted_at DESC
                    """, (cutoff_date.isoformat(),))
                
                results = cursor.fetchall()
                
                deleted_files = []
                for row in results:
                    deleted_files.append({
                        'id': row[0],
                        'original_path': row[1],
                        'filename': row[2],
                        'file_size': row[3],
                        'file_type': row[4],
                        'deletion_reason': row[5],
                        'deleted_at': row[6],
                        'backup_path': row[7],
                        'recovery_possible': bool(row[8])
                    })
                
                return deleted_files
                
        except Exception as e:
            logger.error(f"삭제된 파일 검색 실패: {e}")
            return []
    
    def get_deletion_stats(self) -> Dict[str, Any]:
        """삭제 통계 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 총 삭제 파일 수
                cursor.execute("SELECT COUNT(*) FROM deleted_files")
                total_deleted = cursor.fetchone()[0]
                
                # 오늘 삭제된 파일 수
                today = datetime.now().date().isoformat()
                cursor.execute("""
                    SELECT COUNT(*) FROM deleted_files 
                    WHERE DATE(deleted_at) = ?
                """, (today,))
                today_deleted = cursor.fetchone()[0]
                
                # 복구 가능한 파일 수
                cursor.execute("""
                    SELECT COUNT(*) FROM deleted_files 
                    WHERE recovery_possible = 1
                """, )
                recoverable = cursor.fetchone()[0]
                
                # 카테고리별 삭제 통계
                cursor.execute("""
                    SELECT category, COUNT(*) 
                    FROM deleted_files 
                    GROUP BY category
                """)
                category_stats = dict(cursor.fetchall())
                
                # 파일 이동 통계
                cursor.execute("SELECT COUNT(*) FROM file_movements")
                total_movements = cursor.fetchone()[0]
                
                return {
                    'total_deleted_files': total_deleted,
                    'deleted_today': today_deleted,
                    'recoverable_files': recoverable,
                    'category_breakdown': category_stats,
                    'total_file_movements': total_movements
                }
                
        except Exception as e:
            logger.error(f"삭제 통계 조회 실패: {e}")
            return {}
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """파일 정보 추출"""
        try:
            path_obj = Path(file_path)
            
            # 파일이 존재하지 않을 수도 있음 (이미 삭제됨)
            size = 0
            if path_obj.exists():
                size = path_obj.stat().st_size
            
            return {
                'filename': path_obj.name,
                'size': size,
                'type': path_obj.suffix.lower(),
                'category': self._categorize_file(path_obj.suffix.lower())
            }
            
        except Exception as e:
            logger.error(f"파일 정보 추출 실패: {e}")
            return {
                'filename': Path(file_path).name,
                'size': 0,
                'type': '',
                'category': 'unknown'
            }
    
    def _categorize_file(self, extension: str) -> str:
        """파일 확장자 기반 카테고리 분류"""
        categories = {
            'document': ['.pdf', '.doc', '.docx', '.txt', '.md', '.rtf', '.odt'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
            'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg'],
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
            'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php'],
            'data': ['.csv', '.json', '.xml', '.sql', '.log']
        }
        
        for category, extensions in categories.items():
            if extension in extensions:
                return category
        
        return 'other'

# 전역 인스턴스
deletion_tracker = DeletionTracker()