import time

# metrics 엔드포인트 추가 코드
metrics_code = '''
startup_time = time.time()

@app.get("/metrics")
async def get_metrics():
    """시스템 메트릭스 조회"""
    try:
        # psutil이 없으면 기본값 반환
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        return {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2)
            },
            "service": {
                "indexed_files": len(mafm.file_db) if mafm else 0,
                "cache_size": len(mafm.search_cache) if mafm else 0,
                "uptime_seconds": int(time.time() - startup_time),
                "version": "2.3.0"
            }
        }
    except ImportError:
        # psutil이 없으면 서비스 정보만 반환
        return {
            "service": {
                "indexed_files": len(mafm.file_db) if mafm else 0,
                "cache_size": len(mafm.search_cache) if mafm else 0,
                "uptime_seconds": int(time.time() - startup_time),
                "version": "2.3.0"
            },
            "system": "psutil not installed"
        }
'''

# 원본 파일 읽기
with open('simple_api.py', 'r') as f:
    content = f.read()

# startup_time을 import 섹션 뒤에 추가
lines = content.split('\n')
import_end = 0
for i, line in enumerate(lines):
    if line.strip() and not (line.startswith('import') or line.startswith('from')):
        if i > 0 and (lines[i-1].startswith('import') or lines[i-1].startswith('from')):
            import_end = i
            break

# startup_time 추가
lines.insert(import_end, '')
lines.insert(import_end + 1, 'startup_time = time.time()')
lines.insert(import_end + 2, '')

# metrics 엔드포인트를 main 블록 앞에 추가
main_index = -1
for i, line in enumerate(lines):
    if 'if __name__' in line:
        main_index = i
        break

if main_index > -1:
    lines.insert(main_index, '@app.get("/metrics")')
    lines.insert(main_index + 1, 'async def get_metrics():')
    lines.insert(main_index + 2, '    """시스템 메트릭스 조회"""')
    lines.insert(main_index + 3, '    try:')
    lines.insert(main_index + 4, '        import psutil')
    lines.insert(main_index + 5, '        cpu_percent = psutil.cpu_percent(interval=0.1)')
    lines.insert(main_index + 6, '        memory = psutil.virtual_memory()')
    lines.insert(main_index + 7, '        disk = psutil.disk_usage("/")')
    lines.insert(main_index + 8, '        ')
    lines.insert(main_index + 9, '        return {')
    lines.insert(main_index + 10, '            "system": {')
    lines.insert(main_index + 11, '                "cpu_percent": cpu_percent,')
    lines.insert(main_index + 12, '                "memory_percent": memory.percent,')
    lines.insert(main_index + 13, '                "memory_used_gb": round(memory.used / (1024**3), 2),')
    lines.insert(main_index + 14, '                "memory_total_gb": round(memory.total / (1024**3), 2),')
    lines.insert(main_index + 15, '                "disk_percent": disk.percent,')
    lines.insert(main_index + 16, '                "disk_used_gb": round(disk.used / (1024**3), 2),')
    lines.insert(main_index + 17, '                "disk_total_gb": round(disk.total / (1024**3), 2)')
    lines.insert(main_index + 18, '            },')
    lines.insert(main_index + 19, '            "service": {')
    lines.insert(main_index + 20, '                "indexed_files": len(mafm.file_db) if mafm else 0,')
    lines.insert(main_index + 21, '                "cache_size": len(mafm.search_cache) if mafm else 0,')
    lines.insert(main_index + 22, '                "uptime_seconds": int(time.time() - startup_time),')
    lines.insert(main_index + 23, '                "version": "2.3.0"')
    lines.insert(main_index + 24, '            }')
    lines.insert(main_index + 25, '        }')
    lines.insert(main_index + 26, '    except ImportError:')
    lines.insert(main_index + 27, '        return {')
    lines.insert(main_index + 28, '            "service": {')
    lines.insert(main_index + 29, '                "indexed_files": len(mafm.file_db) if mafm else 0,')
    lines.insert(main_index + 30, '                "cache_size": len(mafm.search_cache) if mafm else 0,')
    lines.insert(main_index + 31, '                "uptime_seconds": int(time.time() - startup_time),')
    lines.insert(main_index + 32, '                "version": "2.3.0"')
    lines.insert(main_index + 33, '            },')
    lines.insert(main_index + 34, '            "system": "psutil not installed"')
    lines.insert(main_index + 35, '        }')
    lines.insert(main_index + 36, '')
    lines.insert(main_index + 37, '')

# 수정된 내용 저장
with open('simple_api_fixed.py', 'w') as f:
    f.write('\n'.join(lines))

print("Fixed file saved as simple_api_fixed.py")