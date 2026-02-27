#!/usr/bin/env python3
"""NAS File Indexer - 전체 파일 스캔 및 분석"""
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from collections import defaultdict

BASE_DIR = "/volume1/homes/hyoseop1231"
OUTPUT_FILE = "/volume1/homes/hyoseop1231/00_시스템/file_index.json"
STATS_FILE = "/volume1/homes/hyoseop1231/00_시스템/file_stats.json"

# 무시할 폴더
IGNORE_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.cache', '@eaDir', '#recycle', '.SynologyWorkingDirectory'}

def get_file_info(filepath):
    """파일 정보 수집"""
    try:
        stat = os.stat(filepath)
        return {
            "path": filepath,
            "name": os.path.basename(filepath),
            "ext": os.path.splitext(filepath)[1].lower(),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        }
    except Exception as e:
        return None

def scan_directory(base_dir):
    """디렉토리 스캔"""
    files = []
    stats = {
        "total_files": 0,
        "total_size": 0,
        "by_extension": defaultdict(lambda: {"count": 0, "size": 0}),
        "by_year": defaultdict(lambda: {"count": 0, "size": 0}),
        "by_folder": defaultdict(lambda: {"count": 0, "size": 0}),
        "duplicates": [],
        "large_files": [],  # >100MB
    }
    
    seen_sizes = defaultdict(list)  # 중복 파일 찾기용
    
    print(f"📂 스캔 시작: {base_dir}")
    count = 0
    
    for root, dirs, filenames in os.walk(base_dir):
        # 무시할 폴더 제외
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        # 상대 경로의 첫 번째 폴더
        rel_path = os.path.relpath(root, base_dir)
        top_folder = rel_path.split(os.sep)[0] if rel_path != '.' else '(root)'
        
        for filename in filenames:
            filepath = os.path.join(root, filename)
            info = get_file_info(filepath)
            
            if info:
                files.append(info)
                stats["total_files"] += 1
                stats["total_size"] += info["size"]
                
                # 확장자별
                ext = info["ext"] or "(no ext)"
                stats["by_extension"][ext]["count"] += 1
                stats["by_extension"][ext]["size"] += info["size"]
                
                # 연도별
                year = info["modified"][:4]
                stats["by_year"][year]["count"] += 1
                stats["by_year"][year]["size"] += info["size"]
                
                # 폴더별
                stats["by_folder"][top_folder]["count"] += 1
                stats["by_folder"][top_folder]["size"] += info["size"]
                
                # 대용량 파일 (>100MB)
                if info["size"] > 100 * 1024 * 1024:
                    stats["large_files"].append({
                        "path": filepath,
                        "size_mb": round(info["size"] / 1024 / 1024, 2)
                    })
                
                # 중복 파일 체크 (같은 크기)
                if info["size"] > 1024:  # 1KB 이상만
                    seen_sizes[info["size"]].append(filepath)
                
                count += 1
                if count % 10000 == 0:
                    print(f"  📊 {count:,}개 파일 스캔됨...")
    
    # 중복 후보 (같은 크기 파일들)
    for size, paths in seen_sizes.items():
        if len(paths) > 1:
            stats["duplicates"].append({
                "size": size,
                "count": len(paths),
                "files": paths[:5]  # 최대 5개만
            })
    
    # 정렬
    stats["by_extension"] = dict(sorted(stats["by_extension"].items(), key=lambda x: x[1]["count"], reverse=True)[:30])
    stats["by_year"] = dict(sorted(stats["by_year"].items()))
    stats["by_folder"] = dict(sorted(stats["by_folder"].items(), key=lambda x: x[1]["size"], reverse=True)[:20])
    stats["large_files"] = sorted(stats["large_files"], key=lambda x: x["size_mb"], reverse=True)[:50]
    stats["duplicates"] = sorted(stats["duplicates"], key=lambda x: x["size"] * x["count"], reverse=True)[:100]
    
    return files, stats

def main():
    print("🚀 NAS 파일 인덱싱 시작")
    print(f"📁 대상: {BASE_DIR}")
    print("-" * 50)
    
    start = datetime.now()
    files, stats = scan_directory(BASE_DIR)
    elapsed = (datetime.now() - start).total_seconds()
    
    # 결과 저장
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print("-" * 50)
    print(f"✅ 완료! ({elapsed:.1f}초)")
    print(f"📊 전체 파일: {stats['total_files']:,}개")
    print(f"💾 전체 용량: {stats['total_size'] / 1024 / 1024 / 1024:.2f}GB")
    print(f"📁 대용량 파일: {len(stats['large_files'])}개")
    print(f"🔄 중복 후보: {len(stats['duplicates'])}그룹")
    print(f"\n📝 통계 저장: {STATS_FILE}")
    
    # 주요 통계 출력
    print("\n📊 확장자별 TOP 10:")
    for ext, data in list(stats["by_extension"].items())[:10]:
        print(f"  {ext}: {data['count']:,}개 ({data['size']/1024/1024:.1f}MB)")
    
    print("\n📂 폴더별 용량 TOP 10:")
    for folder, data in list(stats["by_folder"].items())[:10]:
        print(f"  {folder}: {data['size']/1024/1024/1024:.2f}GB ({data['count']:,}개)")

if __name__ == "__main__":
    main()
