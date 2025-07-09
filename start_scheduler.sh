#!/bin/bash

# Smart File Manager Scheduler 자동 시작 스크립트

SERVICE_NAME="smart-file-scheduler"
SCHEDULER_PATH="/Users/hyoseop1231/AI_Coding/smart-file-manager-mcp/ai-services/scheduler.py"
PID_FILE="/tmp/smart-file-scheduler.pid"

start_scheduler() {
    echo "🚀 Smart File Manager Scheduler 시작 중..."
    
    # 이미 실행 중인지 확인
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "✅ 스케줄러가 이미 실행 중입니다 (PID: $(cat $PID_FILE))"
        return 0
    fi
    
    # 환경 변수 설정
    export DB_PATH="/tmp/smart-file-manager/db/file-index.db"
    export EMBEDDINGS_PATH="/tmp/smart-file-manager/embeddings"
    export METADATA_PATH="/tmp/smart-file-manager/metadata"
    export FULL_INDEX_INTERVAL=7200    # 2시간
    export QUICK_INDEX_INTERVAL=1800   # 30분
    export CLEANUP_INTERVAL=86400      # 24시간
    
    # 스케줄러 시작
    cd /Users/hyoseop1231/AI_Coding/smart-file-manager-mcp/ai-services
    nohup python3 "$SCHEDULER_PATH" > /tmp/smart-file-scheduler.log 2>&1 &
    echo $! > "$PID_FILE"
    
    # 시작 확인
    sleep 3
    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "✅ 스케줄러가 성공적으로 시작되었습니다!"
        echo "📝 로그: tail -f /tmp/smart-file-scheduler.log"
        echo "⏰ 스케줄:"
        echo "   - 전체 인덱싱: 2시간마다"
        echo "   - 빠른 인덱싱: 30분마다"
        echo "   - 데이터베이스 정리: 24시간마다"
    else
        echo "❌ 스케줄러 시작에 실패했습니다. 로그를 확인하세요:"
        echo "   tail /tmp/smart-file-scheduler.log"
        return 1
    fi
}

stop_scheduler() {
    echo "🛑 Smart File Manager Scheduler 중지 중..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            rm -f "$PID_FILE"
            echo "✅ 스케줄러가 중지되었습니다"
        else
            echo "⚠️ 프로세스가 이미 종료되었습니다"
            rm -f "$PID_FILE"
        fi
    else
        echo "⚠️ PID 파일을 찾을 수 없습니다"
        # 혹시 실행 중인 프로세스가 있다면 종료
        pkill -f "scheduler.py"
    fi
}

status_scheduler() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "✅ 스케줄러가 실행 중입니다 (PID: $(cat $PID_FILE))"
        echo "📊 최근 로그:"
        tail -n 5 /tmp/smart-file-scheduler.log 2>/dev/null || echo "   로그 파일이 없습니다"
    else
        echo "❌ 스케줄러가 실행되지 않았습니다"
    fi
}

restart_scheduler() {
    stop_scheduler
    sleep 2
    start_scheduler
}

case "$1" in
    start)
        start_scheduler
        ;;
    stop)
        stop_scheduler
        ;;
    restart)
        restart_scheduler
        ;;
    status)
        status_scheduler
        ;;
    *)
        echo "사용법: $0 {start|stop|restart|status}"
        echo ""
        echo "명령어:"
        echo "  start   - 스케줄러 시작"
        echo "  stop    - 스케줄러 중지"
        echo "  restart - 스케줄러 재시작"
        echo "  status  - 스케줄러 상태 확인"
        echo ""
        echo "환경 변수:"
        echo "  FULL_INDEX_INTERVAL  - 전체 인덱싱 간격 (초, 기본: 7200)"
        echo "  QUICK_INDEX_INTERVAL - 빠른 인덱싱 간격 (초, 기본: 1800)"
        echo "  CLEANUP_INTERVAL     - 정리 간격 (초, 기본: 86400)"
        exit 1
        ;;
esac