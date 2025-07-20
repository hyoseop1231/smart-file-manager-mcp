#!/usr/bin/env python3
"""
Smart File Manager - 디스크 정리 유틸리티
프로덕션 환경에서 디스크 공간 관리를 위한 스크립트
"""

import os
import sys
import shutil
import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path


def get_size(path):
    """디렉토리 또는 파일의 크기를 바이트로 반환"""
    if os.path.isfile(path):
        return os.path.getsize(path)
    
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            fp = os.path.join(dirpath, filename)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total


def format_bytes(size):
    """바이트를 인간이 읽기 쉬운 형식으로 변환"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def check_disk_usage():
    """현재 디스크 사용률 확인"""
    total, used, free = shutil.disk_usage("/")
    usage_percent = (used / total) * 100
    
    print(f"디스크 사용 현황:")
    print(f"  총 용량: {format_bytes(total)}")
    print(f"  사용 중: {format_bytes(used)} ({usage_percent:.1f}%)")
    print(f"  여유 공간: {format_bytes(free)}")
    print()
    
    return usage_percent


def clean_old_thumbnails(days=30):
    """오래된 썸네일 정리"""
    thumbnail_dirs = [
        "/data/thumbnails",
        "/data/video_thumbnails"
    ]
    
    total_cleaned = 0
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for thumb_dir in thumbnail_dirs:
        if not os.path.exists(thumb_dir):
            continue
            
        print(f"썸네일 정리 중: {thumb_dir}")
        
        for root, dirs, files in os.walk(thumb_dir):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    if datetime.fromtimestamp(os.path.getmtime(filepath)) < cutoff_date:
                        size = os.path.getsize(filepath)
                        os.remove(filepath)
                        total_cleaned += size
                except Exception as e:
                    print(f"  - 오류 발생: {filepath}: {e}")
    
    print(f"  - 정리된 썸네일: {format_bytes(total_cleaned)}")
    return total_cleaned


def clean_temp_files():
    """임시 파일 정리"""
    temp_patterns = [
        "*.tmp",
        "*.temp",
        "*.cache",
        "~*",
        ".DS_Store"
    ]
    
    temp_dirs = [
        "/tmp",
        "/data/temp",
        "/app/temp"
    ]
    
    total_cleaned = 0
    
    for temp_dir in temp_dirs:
        if not os.path.exists(temp_dir):
            continue
            
        print(f"임시 파일 정리 중: {temp_dir}")
        
        for pattern in temp_patterns:
            for filepath in Path(temp_dir).rglob(pattern):
                try:
                    size = filepath.stat().st_size
                    filepath.unlink()
                    total_cleaned += size
                except Exception as e:
                    print(f"  - 오류 발생: {filepath}: {e}")
    
    print(f"  - 정리된 임시 파일: {format_bytes(total_cleaned)}")
    return total_cleaned


def vacuum_database(db_path="/data/db/file-index.db"):
    """SQLite 데이터베이스 최적화"""
    if not os.path.exists(db_path):
        print(f"데이터베이스를 찾을 수 없음: {db_path}")
        return 0
    
    print(f"데이터베이스 최적화 중: {db_path}")
    
    original_size = os.path.getsize(db_path)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("VACUUM")
        conn.close()
        
        new_size = os.path.getsize(db_path)
        saved = original_size - new_size
        
        print(f"  - 원본 크기: {format_bytes(original_size)}")
        print(f"  - 최적화 후: {format_bytes(new_size)}")
        print(f"  - 절약된 공간: {format_bytes(saved)}")
        
        return saved
    except Exception as e:
        print(f"  - 오류 발생: {e}")
        return 0


def clean_orphaned_embeddings(db_path="/data/db/file-index.db", embeddings_path="/data/embeddings"):
    """고아 임베딩 파일 정리"""
    if not os.path.exists(embeddings_path):
        return 0
        
    print(f"고아 임베딩 파일 정리 중...")
    
    # DB에서 유효한 파일 ID 목록 가져오기
    valid_ids = set()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM file_index")
        valid_ids = {str(row[0]) for row in cursor.fetchall()}
        conn.close()
    except Exception as e:
        print(f"  - DB 읽기 오류: {e}")
        return 0
    
    total_cleaned = 0
    
    # 임베딩 파일 확인
    for root, dirs, files in os.walk(embeddings_path):
        for file in files:
            if file.endswith('.npy'):
                file_id = file.replace('.npy', '')
                if file_id not in valid_ids:
                    filepath = os.path.join(root, file)
                    try:
                        size = os.path.getsize(filepath)
                        os.remove(filepath)
                        total_cleaned += size
                    except Exception as e:
                        print(f"  - 오류 발생: {filepath}: {e}")
    
    print(f"  - 정리된 고아 임베딩: {format_bytes(total_cleaned)}")
    return total_cleaned


def main():
    parser = argparse.ArgumentParser(description="Smart File Manager 디스크 정리 유틸리티")
    parser.add_argument("--dry-run", action="store_true", help="실제로 삭제하지 않고 시뮬레이션만 수행")
    parser.add_argument("--thumbnail-days", type=int, default=30, help="이 일수보다 오래된 썸네일 삭제 (기본값: 30)")
    parser.add_argument("--all", action="store_true", help="모든 정리 작업 수행")
    parser.add_argument("--thumbnails", action="store_true", help="썸네일만 정리")
    parser.add_argument("--temp", action="store_true", help="임시 파일만 정리")
    parser.add_argument("--vacuum", action="store_true", help="데이터베이스만 최적화")
    parser.add_argument("--embeddings", action="store_true", help="고아 임베딩만 정리")
    
    args = parser.parse_args()
    
    # 현재 디스크 사용률 확인
    usage_percent = check_disk_usage()
    
    if usage_percent > 90:
        print("⚠️  경고: 디스크 사용률이 90%를 초과했습니다!")
    elif usage_percent > 80:
        print("⚠️  주의: 디스크 사용률이 80%를 초과했습니다.")
    
    print()
    
    # 정리 작업 수행
    total_cleaned = 0
    
    if args.all or args.thumbnails:
        cleaned = clean_old_thumbnails(args.thumbnail_days)
        total_cleaned += cleaned
        print()
    
    if args.all or args.temp:
        cleaned = clean_temp_files()
        total_cleaned += cleaned
        print()
    
    if args.all or args.vacuum:
        cleaned = vacuum_database()
        total_cleaned += cleaned
        print()
    
    if args.all or args.embeddings:
        cleaned = clean_orphaned_embeddings()
        total_cleaned += cleaned
        print()
    
    # 결과 요약
    print("=" * 50)
    print(f"총 정리된 공간: {format_bytes(total_cleaned)}")
    
    # 정리 후 디스크 사용률
    new_usage = check_disk_usage()
    print(f"\n사용률 변화: {usage_percent:.1f}% → {new_usage:.1f}%")


if __name__ == "__main__":
    main()