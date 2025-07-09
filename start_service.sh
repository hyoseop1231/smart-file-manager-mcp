#!/bin/bash

# Smart File Manager MCP 자동 시작 스크립트

SERVICE_NAME="smart-file-manager"
AI_SERVICE_PATH="/Users/hyoseop1231/AI_Coding/smart-file-manager-mcp/ai-services/enhanced_api.py"
PID_FILE="/tmp/smart-file-manager.pid"

start_service() {
    echo "🚀 Smart File Manager MCP 서비스 시작 중..."
    
    # 이미 실행 중인지 확인
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "✅ 서비스가 이미 실행 중입니다 (PID: $(cat $PID_FILE))"
        return 0
    fi
    
    # AI 서비스 시작
    cd /Users/hyoseop1231/AI_Coding/smart-file-manager-mcp
    nohup python3 "$AI_SERVICE_PATH" > /tmp/smart-file-manager.log 2>&1 &
    echo $! > "$PID_FILE"
    
    # 시작 확인
    sleep 3
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ 서비스가 성공적으로 시작되었습니다!"
        echo "📍 URL: http://localhost:8001"
        echo "📊 Health Check: http://localhost:8001/health"
        echo "📝 로그: tail -f /tmp/smart-file-manager.log"
    else
        echo "❌ 서비스 시작에 실패했습니다. 로그를 확인하세요:"
        echo "   tail /tmp/smart-file-manager.log"
        return 1
    fi
}

stop_service() {
    echo "🛑 Smart File Manager MCP 서비스 중지 중..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            rm -f "$PID_FILE"
            echo "✅ 서비스가 중지되었습니다"
        else
            echo "⚠️ 프로세스가 이미 종료되었습니다"
            rm -f "$PID_FILE"
        fi
    else
        echo "⚠️ PID 파일을 찾을 수 없습니다"
        # 혹시 실행 중인 프로세스가 있다면 종료
        pkill -f "enhanced_api.py"
    fi
}

status_service() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "✅ 서비스가 실행 중입니다 (PID: $(cat $PID_FILE))"
        
        # API 상태 확인
        if curl -s http://localhost:8001/health > /dev/null 2>&1; then
            echo "🌐 API 서비스: 정상"
            echo "📊 상태 정보:"
            curl -s http://localhost:8001/health | jq '.db_stats.total_files' 2>/dev/null | xargs -I {} echo "   총 파일: {}"
        else
            echo "⚠️ API 서비스: 응답 없음"
        fi
    else
        echo "❌ 서비스가 실행되지 않았습니다"
    fi
}

restart_service() {
    stop_service
    sleep 2
    start_service
}

case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    *)
        echo "사용법: $0 {start|stop|restart|status}"
        echo ""
        echo "명령어:"
        echo "  start   - 서비스 시작"
        echo "  stop    - 서비스 중지"
        echo "  restart - 서비스 재시작"
        echo "  status  - 서비스 상태 확인"
        echo ""
        echo "예시:"
        echo "  $0 start    # 서비스 시작"
        echo "  $0 status   # 상태 확인"
        exit 1
        ;;
esac