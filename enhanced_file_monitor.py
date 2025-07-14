#!/usr/bin/env python3
"""
Enhanced File Monitor with Deletion Tracking
실시간 파일 삭제 및 이동 감지를 위한 강화된 파일 모니터
"""

import os
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, Optional, Callable
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileDeletedEvent, FileMovedEvent

from enhanced_deletion_tracking import deletion_tracker

logger = logging.getLogger(__name__)

class DeletionAwareFileHandler(FileSystemEventHandler):
    """파일 삭제 및 이동을 감지하는 이벤트 핸들러"""
    
    def __init__(self, monitored_paths: Set[str]):
        super().__init__()
        self.monitored_paths = monitored_paths
        self.recent_moves: Dict[str, Dict] = {}  # 최근 이동 추적
        self.move_timeout = 5  # 5초 내에 이동이 완료되지 않으면 삭제로 간주
        
    def on_deleted(self, event):
        """파일 삭제 이벤트 처리"""
        if event.is_directory:
            return
            
        file_path = event.src_path
        logger.info(f"파일 삭제 감지: {file_path}")
        
        # 최근 이동 중인지 확인 (이동의 일부일 수 있음)
        if self._is_recent_move(file_path):
            logger.debug(f"최근 이동의 일부로 판단, 삭제 추적하지 않음: {file_path}")
            return
        
        # 삭제 추적 등록
        try:
            deletion_id = deletion_tracker.track_deletion(
                file_path=file_path,
                reason="file_system_deletion",
                metadata={
                    "detection_method": "watchdog",
                    "timestamp": datetime.now().isoformat(),
                    "event_type": "deleted"
                }
            )
            
            if deletion_id > 0:
                logger.info(f"파일 삭제 추적 완료: {file_path} (ID: {deletion_id})")
            else:
                logger.error(f"파일 삭제 추적 실패: {file_path}")
                
        except Exception as e:
            logger.error(f"파일 삭제 추적 중 오류: {e}")
    
    def on_moved(self, event):
        """파일 이동 이벤트 처리"""
        if event.is_directory:
            return
            
        src_path = event.src_path
        dest_path = event.dest_path
        
        logger.info(f"파일 이동 감지: {src_path} -> {dest_path}")
        
        # 이동 추적 (Archive 판단)
        movement_type = self._determine_movement_type(src_path, dest_path)
        reason = self._determine_movement_reason(src_path, dest_path)
        
        try:
            movement_id = deletion_tracker.track_movement(
                original_path=src_path,
                new_path=dest_path,
                movement_type=movement_type,
                reason=reason
            )
            
            if movement_id > 0:
                logger.info(f"파일 이동 추적 완료: {src_path} -> {dest_path} (ID: {movement_id})")
                
                # 최근 이동으로 기록 (삭제 오탐 방지)
                self.recent_moves[src_path] = {
                    'dest_path': dest_path,
                    'timestamp': time.time(),
                    'movement_id': movement_id
                }
                
                # 이전 이동 기록 정리
                self._cleanup_old_moves()
                
            else:
                logger.error(f"파일 이동 추적 실패: {src_path} -> {dest_path}")
                
        except Exception as e:
            logger.error(f"파일 이동 추적 중 오류: {e}")
    
    def _is_recent_move(self, file_path: str) -> bool:
        """최근 이동 중인 파일인지 확인"""
        current_time = time.time()
        
        for move_path, move_info in self.recent_moves.items():
            if move_path == file_path:
                if current_time - move_info['timestamp'] < self.move_timeout:
                    return True
        
        return False
    
    def _cleanup_old_moves(self):
        """오래된 이동 기록 정리"""
        current_time = time.time()
        expired_moves = []
        
        for move_path, move_info in self.recent_moves.items():
            if current_time - move_info['timestamp'] > self.move_timeout:
                expired_moves.append(move_path)
        
        for move_path in expired_moves:
            del self.recent_moves[move_path]
    
    def _determine_movement_type(self, src_path: str, dest_path: str) -> str:
        """이동 타입 결정"""
        src_path_lower = src_path.lower()
        dest_path_lower = dest_path.lower()
        
        # Archive 폴더로 이동
        if any(keyword in dest_path_lower for keyword in ['archive', '보관', 'backup', '백업']):
            return "archive"
        
        # 휴지통으로 이동
        if any(keyword in dest_path_lower for keyword in ['trash', '휴지통', '.trash']):
            return "trash"
        
        # 임시 폴더로 이동
        if any(keyword in dest_path_lower for keyword in ['temp', '임시', 'tmp']):
            return "temporary"
        
        # 일반 재구성
        return "reorganize"
    
    def _determine_movement_reason(self, src_path: str, dest_path: str) -> str:
        """이동 이유 결정"""
        movement_type = self._determine_movement_type(src_path, dest_path)
        
        if movement_type == "archive":
            return "file_organization_archive"
        elif movement_type == "trash":
            return "user_deletion"
        elif movement_type == "temporary":
            return "temporary_storage"
        else:
            return "file_reorganization"

class EnhancedFileMonitor:
    """강화된 파일 모니터 - 삭제 추적 기능 포함"""
    
    def __init__(self, monitored_paths: Optional[Set[str]] = None):
        self.monitored_paths = monitored_paths or {
            "/Users/hyoseop1231/Desktop",
            "/Users/hyoseop1231/Documents"
        }
        
        self.observer = Observer()
        self.event_handler = DeletionAwareFileHandler(self.monitored_paths)
        self.is_monitoring = False
        self._monitor_thread = None
        
        logger.info(f"Enhanced File Monitor 초기화 완료, 모니터링 경로: {self.monitored_paths}")
    
    def start_monitoring(self):
        """파일 모니터링 시작"""
        if self.is_monitoring:
            logger.warning("파일 모니터링이 이미 실행 중입니다")
            return
        
        try:
            # 각 경로에 대해 감시자 등록
            for path in self.monitored_paths:
                if os.path.exists(path):
                    self.observer.schedule(
                        self.event_handler, 
                        path, 
                        recursive=True
                    )
                    logger.info(f"모니터링 경로 등록: {path}")
                else:
                    logger.warning(f"모니터링 경로가 존재하지 않음: {path}")
            
            self.observer.start()
            self.is_monitoring = True
            
            logger.info("Enhanced File Monitor 시작됨")
            
        except Exception as e:
            logger.error(f"파일 모니터링 시작 실패: {e}")
            raise
    
    def stop_monitoring(self):
        """파일 모니터링 중지"""
        if not self.is_monitoring:
            logger.warning("파일 모니터링이 실행되지 않고 있습니다")
            return
        
        try:
            self.observer.stop()
            self.observer.join()
            self.is_monitoring = False
            
            logger.info("Enhanced File Monitor 중지됨")
            
        except Exception as e:
            logger.error(f"파일 모니터링 중지 실패: {e}")
            raise
    
    def add_monitored_path(self, path: str):
        """모니터링 경로 추가"""
        if path not in self.monitored_paths:
            self.monitored_paths.add(path)
            
            if self.is_monitoring and os.path.exists(path):
                self.observer.schedule(
                    self.event_handler,
                    path,
                    recursive=True
                )
                logger.info(f"새 모니터링 경로 추가: {path}")
    
    def remove_monitored_path(self, path: str):
        """모니터링 경로 제거"""
        if path in self.monitored_paths:
            self.monitored_paths.remove(path)
            logger.info(f"모니터링 경로 제거: {path}")
            
            # 실행 중인 감시자에서 제거하려면 재시작 필요
            if self.is_monitoring:
                logger.info("모니터링 재시작이 필요합니다")
    
    def get_monitoring_status(self) -> Dict:
        """모니터링 상태 조회"""
        return {
            "is_monitoring": self.is_monitoring,
            "monitored_paths": list(self.monitored_paths),
            "observer_alive": self.observer.is_alive() if self.is_monitoring else False,
            "recent_moves_count": len(self.event_handler.recent_moves) if hasattr(self.event_handler, 'recent_moves') else 0
        }

# 백그라운드에서 실행할 모니터 인스턴스
class BackgroundMonitorService:
    """백그라운드 모니터링 서비스"""
    
    def __init__(self):
        self.monitor = EnhancedFileMonitor()
        self.service_thread = None
        self.is_running = False
    
    def start_service(self):
        """백그라운드 서비스 시작"""
        if self.is_running:
            logger.warning("백그라운드 모니터링 서비스가 이미 실행 중입니다")
            return
        
        try:
            self.monitor.start_monitoring()
            self.is_running = True
            
            # 백그라운드 스레드에서 실행
            self.service_thread = threading.Thread(
                target=self._run_service,
                daemon=True
            )
            self.service_thread.start()
            
            logger.info("백그라운드 파일 모니터링 서비스 시작")
            
        except Exception as e:
            logger.error(f"백그라운드 서비스 시작 실패: {e}")
            raise
    
    def stop_service(self):
        """백그라운드 서비스 중지"""
        if not self.is_running:
            logger.warning("백그라운드 모니터링 서비스가 실행되지 않고 있습니다")
            return
        
        try:
            self.is_running = False
            self.monitor.stop_monitoring()
            
            if self.service_thread and self.service_thread.is_alive():
                self.service_thread.join(timeout=5)
            
            logger.info("백그라운드 파일 모니터링 서비스 중지")
            
        except Exception as e:
            logger.error(f"백그라운드 서비스 중지 실패: {e}")
    
    def _run_service(self):
        """서비스 실행 루프"""
        while self.is_running:
            try:
                time.sleep(1)  # CPU 사용량 제한
                
                # 주기적으로 모니터 상태 확인
                if not self.monitor.observer.is_alive():
                    logger.warning("파일 모니터 Observer가 중지됨, 재시작 시도")
                    self.monitor.stop_monitoring()
                    self.monitor.start_monitoring()
                    
            except Exception as e:
                logger.error(f"백그라운드 서비스 실행 중 오류: {e}")
                time.sleep(5)  # 오류 발생 시 잠시 대기
    
    def get_service_status(self) -> Dict:
        """서비스 상태 조회"""
        monitor_status = self.monitor.get_monitoring_status()
        
        return {
            "service_running": self.is_running,
            "thread_alive": self.service_thread.is_alive() if self.service_thread else False,
            "monitor_status": monitor_status
        }

# 전역 서비스 인스턴스
background_monitor_service = BackgroundMonitorService()

# 자동 시작 함수
def start_deletion_monitoring():
    """삭제 모니터링 자동 시작"""
    try:
        background_monitor_service.start_service()
        logger.info("삭제 모니터링 자동 시작 완료")
    except Exception as e:
        logger.error(f"삭제 모니터링 자동 시작 실패: {e}")

def stop_deletion_monitoring():
    """삭제 모니터링 중지"""
    try:
        background_monitor_service.stop_service()
        logger.info("삭제 모니터링 중지 완료")
    except Exception as e:
        logger.error(f"삭제 모니터링 중지 실패: {e}")

# 모듈 임포트 시 자동 시작 (선택사항)
if __name__ == "__main__":
    start_deletion_monitoring()
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        stop_deletion_monitoring()
        print("삭제 모니터링 서비스 종료")

__all__ = [
    'EnhancedFileMonitor', 
    'BackgroundMonitorService',
    'background_monitor_service',
    'start_deletion_monitoring',
    'stop_deletion_monitoring'
]