#!/usr/bin/env python3
"""
Enhanced File Processor with parallel processing capabilities
병렬 처리를 통한 파일 인덱싱 속도 향상
"""

import os
import time
import logging
import asyncio
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import queue
import threading

from indexer import FileIndexer
from db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class EnhancedFileProcessor:
    """고성능 병렬 파일 처리기"""
    
    def __init__(self, db_path: str, embeddings_path: str, metadata_path: str, 
                 worker_processes: int = None, batch_size: int = 10, 
                 max_file_size_mb: int = 100):
        """
        Args:
            worker_processes: 병렬 처리 워커 수 (None이면 CPU 코어 수 사용)
            batch_size: 배치당 파일 수
            max_file_size_mb: 처리할 최대 파일 크기 (MB)
        """
        self.db_path = db_path
        self.embeddings_path = embeddings_path
        self.metadata_path = metadata_path
        
        # 설정값 초기화
        self.worker_processes = worker_processes or min(multiprocessing.cpu_count(), 5)
        self.batch_size = batch_size
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        
        # 컴포넌트 초기화
        self.db_manager = DatabaseManager(db_path)
        self.file_indexer = FileIndexer(db_path, embeddings_path, metadata_path)
        
        # 통계 추적
        self.stats = {
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None,
            'processing_times': []
        }
        
        # 스레드 안전 큐
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        logger.info(f"Enhanced File Processor initialized with {self.worker_processes} workers")
    
    def should_process_file(self, file_path: str) -> bool:
        """파일 처리 여부 결정"""
        try:
            if not os.path.exists(file_path):
                return False
                
            # 파일 크기 확인
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size_bytes:
                logger.debug(f"Skipping large file: {file_path} ({file_size / 1024 / 1024:.1f} MB)")
                return False
            
            # 특정 파일 형식 제외
            excluded_extensions = {'.exe', '.dll', '.so', '.dylib', '.app', '.dmg', '.pkg'}
            file_ext = Path(file_path).suffix.lower()
            if file_ext in excluded_extensions:
                return False
                
            return True
            
        except Exception as e:
            logger.warning(f"Error checking file {file_path}: {e}")
            return False
    
    def process_file_batch(self, file_paths: List[str]) -> Dict[str, Any]:
        """파일 배치 처리"""
        results = {
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        for file_path in file_paths:
            try:
                if not self.should_process_file(file_path):
                    results['skipped'] += 1
                    continue
                
                # 파일 인덱싱
                start_time = time.time()
                self.file_indexer.index_file(file_path)
                process_time = time.time() - start_time
                
                results['processed'] += 1
                self.stats['processing_times'].append(process_time)
                
                logger.debug(f"Processed {file_path} in {process_time:.2f}s")
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'file': file_path,
                    'error': str(e)
                })
                logger.error(f"Failed to process {file_path}: {e}")
        
        return results
    
    def worker_thread(self, worker_id: int):
        """워커 스레드 실행"""
        logger.info(f"Worker {worker_id} started")
        
        while True:
            try:
                # 작업 큐에서 배치 가져오기
                batch = self.task_queue.get(timeout=1)
                if batch is None:  # 종료 신호
                    break
                
                # 배치 처리
                results = self.process_file_batch(batch)
                self.result_queue.put(results)
                
                # 통계 업데이트
                with threading.Lock():
                    self.stats['processed'] += results['processed']
                    self.stats['failed'] += results['failed']
                    self.stats['skipped'] += results['skipped']
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
        
        logger.info(f"Worker {worker_id} stopped")
    
    def process_files_parallel(self, file_paths: List[str]) -> Dict[str, Any]:
        """병렬 파일 처리 메인 함수"""
        logger.info(f"Starting parallel processing of {len(file_paths)} files")
        
        self.stats['start_time'] = time.time()
        self.stats['processed'] = 0
        self.stats['failed'] = 0
        self.stats['skipped'] = 0
        
        # 파일을 배치로 나누기
        batches = [file_paths[i:i + self.batch_size] 
                   for i in range(0, len(file_paths), self.batch_size)]
        
        # 작업 큐에 배치 추가
        for batch in batches:
            self.task_queue.put(batch)
        
        # 워커 스레드 시작
        workers = []
        for i in range(self.worker_processes):
            worker = threading.Thread(
                target=self.worker_thread,
                args=(i,),
                daemon=True
            )
            worker.start()
            workers.append(worker)
        
        # 진행 상황 모니터링
        total_batches = len(batches)
        processed_batches = 0
        
        while processed_batches < total_batches:
            try:
                result = self.result_queue.get(timeout=1)
                processed_batches += 1
                
                # 진행률 출력
                progress = (processed_batches / total_batches) * 100
                elapsed = time.time() - self.stats['start_time']
                rate = self.stats['processed'] / elapsed if elapsed > 0 else 0
                
                logger.info(f"Progress: {progress:.1f}% | "
                           f"Processed: {self.stats['processed']} | "
                           f"Rate: {rate:.1f} files/sec")
                
            except queue.Empty:
                continue
        
        # 워커 종료
        for _ in range(self.worker_processes):
            self.task_queue.put(None)
        
        for worker in workers:
            worker.join()
        
        # 최종 통계
        total_time = time.time() - self.stats['start_time']
        avg_time = sum(self.stats['processing_times']) / len(self.stats['processing_times']) \
                   if self.stats['processing_times'] else 0
        
        return {
            'total_files': len(file_paths),
            'processed': self.stats['processed'],
            'failed': self.stats['failed'],
            'skipped': self.stats['skipped'],
            'total_time': total_time,
            'average_time_per_file': avg_time,
            'files_per_second': self.stats['processed'] / total_time if total_time > 0 else 0
        }
    
    async def process_files_async(self, file_paths: List[str]) -> Dict[str, Any]:
        """비동기 파일 처리 (대안)"""
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=self.worker_processes) as executor:
            # 파일을 배치로 나누기
            batches = [file_paths[i:i + self.batch_size] 
                       for i in range(0, len(file_paths), self.batch_size)]
            
            # 비동기 태스크 생성
            tasks = []
            for batch in batches:
                task = loop.run_in_executor(executor, self.process_file_batch, batch)
                tasks.append(task)
            
            # 모든 태스크 완료 대기
            results = await asyncio.gather(*tasks)
            
            # 결과 집계
            total_processed = sum(r['processed'] for r in results)
            total_failed = sum(r['failed'] for r in results)
            total_skipped = sum(r['skipped'] for r in results)
            
            return {
                'total_files': len(file_paths),
                'processed': total_processed,
                'failed': total_failed,
                'skipped': total_skipped
            }