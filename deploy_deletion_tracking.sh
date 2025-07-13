#!/bin/bash

# Enhanced Smart File Manager - Deletion Tracking 배포 스크립트
# 삭제 추적 기능을 기존 smart-file-manager에 통합

set -e  # 오류 발생 시 스크립트 중단

echo "🚀 Smart File Manager 삭제 추적 기능 배포 시작..."

# 변수 설정
CONTAINER_NAME="smart-file-manager"
MCP_CONTAINER_NAME="smart-file-mcp-server"
BACKUP_DIR="/Users/hyoseop1231/Desktop/05_Tools_도구_🛠️/smart-file-manager/backup_$(date +%Y%m%d_%H%M%S)"
SOURCE_DIR="/Users/hyoseop1231/Desktop/05_Tools_도구_🛠️/smart-file-manager"

# 백업 디렉토리 생성
echo "📦 기존 설정 백업 중..."
mkdir -p "$BACKUP_DIR"

# 컨테이너가 실행 중인지 확인
if docker ps | grep -q "$CONTAINER_NAME"; then
    echo "✅ Smart File Manager 컨테이너 발견: $CONTAINER_NAME"
    
    # 기존 설정 백업
    docker cp "$CONTAINER_NAME:/app/enhanced_api.py" "$BACKUP_DIR/enhanced_api.py.backup" 2>/dev/null || echo "⚠️  enhanced_api.py 백업 실패 (파일이 없을 수 있음)"
    
else
    echo "❌ Smart File Manager 컨테이너를 찾을 수 없습니다: $CONTAINER_NAME"
    echo "   컨테이너 목록:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    exit 1
fi

# 새 모듈들 컨테이너에 복사
echo "📁 새 모듈들을 컨테이너에 복사 중..."

# 삭제 추적 모듈 복사
docker cp "$SOURCE_DIR/enhanced_deletion_tracking.py" "$CONTAINER_NAME:/app/"
echo "✅ enhanced_deletion_tracking.py 복사 완료"

# API 엔드포인트 모듈 복사
docker cp "$SOURCE_DIR/deletion_api_endpoints.py" "$CONTAINER_NAME:/app/"
echo "✅ deletion_api_endpoints.py 복사 완료"

# 파일 모니터 모듈 복사
docker cp "$SOURCE_DIR/enhanced_file_monitor.py" "$CONTAINER_NAME:/app/"
echo "✅ enhanced_file_monitor.py 복사 완료"

# 필요한 패키지 설치
echo "📦 필요한 Python 패키지 설치 중..."
docker exec "$CONTAINER_NAME" pip install watchdog || echo "⚠️  watchdog 설치 실패 (이미 설치되어 있을 수 있음)"

# API 통합 패치 적용
echo "🔧 기존 API에 새 엔드포인트 통합 중..."

# enhanced_api.py에 새 라우터 추가
docker exec "$CONTAINER_NAME" python3 -c "
import sys
sys.path.append('/app')

# API 파일 읽기
with open('/app/enhanced_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 새로운 import 추가
if 'from deletion_api_endpoints import deletion_router' not in content:
    # import 섹션 찾기
    import_pos = content.find('from vector_api_endpoints import router as vector_router')
    if import_pos != -1:
        # vector_router import 다음에 삭제 라우터 import 추가
        import_end = content.find('\n', import_pos)
        new_import = '\nfrom deletion_api_endpoints import deletion_router'
        content = content[:import_end] + new_import + content[import_end:]
        print('✅ Deletion router import 추가')
    else:
        print('⚠️  Vector router import를 찾을 수 없음')

# 라우터 등록 추가
if 'app.include_router(deletion_router)' not in content:
    # app.include_router 위치 찾기
    vector_include_pos = content.find('app.include_router(vector_router)')
    if vector_include_pos != -1:
        # vector_router 등록 다음에 삭제 라우터 등록 추가
        include_end = content.find('\n', vector_include_pos)
        new_include = '\napp.include_router(deletion_router)'
        content = content[:include_end] + new_include + content[include_end:]
        print('✅ Deletion router 등록 추가')
    else:
        print('⚠️  Vector router 등록을 찾을 수 없음')

# 파일 모니터 시작 코드 추가
if 'start_deletion_monitoring()' not in content:
    # main 실행 부분 찾기
    main_pos = content.find('if __name__ == \"__main__\":')
    if main_pos != -1:
        # main 블록 시작 부분에 모니터 시작 코드 추가
        main_start = content.find('\n', main_pos) + 1
        monitor_code = '''
    # Enhanced Deletion Monitoring 시작
    try:
        from enhanced_file_monitor import start_deletion_monitoring
        start_deletion_monitoring()
        print(\"🔍 삭제 추적 모니터링 시작됨\")
    except Exception as e:
        print(f\"⚠️  삭제 추적 모니터링 시작 실패: {e}\")
'''
        content = content[:main_start] + monitor_code + content[main_start:]
        print('✅ 삭제 모니터링 시작 코드 추가')

# 수정된 내용 저장
with open('/app/enhanced_api.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('🔧 API 통합 패치 적용 완료')
"

# 데이터베이스 초기화
echo "🗄️  삭제 추적 데이터베이스 초기화 중..."
docker exec "$CONTAINER_NAME" python3 -c "
import sys
sys.path.append('/app')
from enhanced_deletion_tracking import deletion_tracker
print('✅ 삭제 추적 데이터베이스 초기화 완료')
"

# 컨테이너 재시작
echo "🔄 Smart File Manager 재시작 중..."
docker restart "$CONTAINER_NAME"

# 재시작 대기
echo "⏳ 서비스 재시작 대기 중..."
sleep 15

# 서비스 상태 확인
echo "🔍 서비스 상태 확인 중..."

# 헬스체크
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ 메인 서비스 정상 작동"
else
    echo "❌ 메인 서비스 응답 없음"
fi

# 새 엔드포인트 테스트
if curl -s http://localhost:8001/api/deletion/health > /dev/null; then
    echo "✅ 삭제 추적 API 정상 작동"
else
    echo "❌ 삭제 추적 API 응답 없음"
fi

# 실시간 테스트를 위한 샘플 데이터 추가 (우리가 이동한 파일들을 기록)
echo "📝 기존 Archive 이동 기록 추가 중..."
docker exec "$CONTAINER_NAME" python3 -c "
import sys
sys.path.append('/app')
from enhanced_deletion_tracking import deletion_tracker
import os

# 우리가 Archive로 이동한 파일들을 기록
archive_files = [
    'processed_files_20250710_122418.zip',
    'processed_files_20250710_115814.zip', 
    'processed_files_20250710_114346.zip',
    'processed_files_20250710_112904.zip',
    'processed_files_20250710_091832.zip'
]

for filename in archive_files:
    original_path = f'/Users/hyoseop1231/Desktop/01_Projects_진행중_📂/🔋_이차전지제조AI_프로젝트/uploads/{filename}'
    new_path = f'/Users/hyoseop1231/Desktop/06_Archive_보관함_📦/2025/이차전지_데이터_백업/{filename}'
    
    movement_id = deletion_tracker.track_movement(
        original_path=original_path,
        new_path=new_path,
        movement_type='archive',
        reason='desktop_organization'
    )
    
    if movement_id > 0:
        print(f'✅ {filename} 이동 기록 추가 (ID: {movement_id})')
    else:
        print(f'❌ {filename} 이동 기록 추가 실패')

print('📝 기존 Archive 이동 기록 추가 완료')
"

# 배포 완료 메시지
echo ""
echo "🎉 Smart File Manager 삭제 추적 기능 배포 완료!"
echo ""
echo "📋 새로 추가된 기능:"
echo "   ✅ 실시간 파일 삭제 감지"
echo "   ✅ 파일 이동 추적 (Archive 등)"
echo "   ✅ 삭제된 파일 히스토리 API"
echo "   ✅ 삭제/이동 통계"
echo "   ✅ 삭제된 파일 검색"
echo ""
echo "🌐 새로운 API 엔드포인트:"
echo "   📍 GET  /api/deletion/recent-deletions"
echo "   📍 GET  /api/deletion/recent-movements" 
echo "   📍 GET  /api/deletion/deleted-files"
echo "   📍 POST /api/deletion/search-deleted"
echo "   📍 GET  /api/deletion/stats"
echo "   📍 GET  /api/deletion/health"
echo ""
echo "🔗 테스트 URL:"
echo "   http://localhost:8001/api/deletion/deleted-files?limit=5"
echo ""
echo "📁 백업 위치: $BACKUP_DIR"

# 간단한 기능 테스트
echo ""
echo "🧪 간단한 기능 테스트 실행 중..."

# 최근 삭제된 파일 조회 테스트
echo "1. 최근 삭제된 파일 조회 테스트:"
curl -s "http://localhost:8001/api/deletion/deleted-files?limit=3" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'recent_deletions' in data:
        deletions = data['recent_deletions']
        print(f'   ✅ {len(deletions)}개의 기록 조회 성공')
        for i, deletion in enumerate(deletions[:2], 1):
            print(f'   {i}. {deletion[\"filename\"]} (삭제일: {deletion[\"deleted_at\"]})')
    else:
        print('   ❌ 예상된 응답 형식이 아님')
except Exception as e:
    print(f'   ❌ 테스트 실패: {e}')
"

# 이동 기록 조회 테스트
echo ""
echo "2. 파일 이동 기록 조회 테스트:"
curl -s "http://localhost:8001/api/deletion/recent-movements?limit=3" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'movements' in data:
        movements = data['movements']
        print(f'   ✅ {len(movements)}개의 이동 기록 조회 성공')
        for i, movement in enumerate(movements[:2], 1):
            print(f'   {i}. {movement[\"filename\"]} ({movement[\"movement_type\"]})')
    else:
        print('   ❌ 예상된 응답 형식이 아님')
except Exception as e:
    print(f'   ❌ 테스트 실패: {e}')
"

echo ""
echo "🎯 배포 완료! 이제 Claude Desktop에서 다음과 같이 요청할 수 있습니다:"
echo '   "최근 삭제된 파일 5개만 보여줘"'
echo '   "Archive로 이동한 파일들 보여줘"'
echo '   "삭제 통계 알려줘"'