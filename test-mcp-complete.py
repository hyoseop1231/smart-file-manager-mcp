#!/usr/bin/env python3

"""
Complete MCP Server Test
Tests both MCP server and AI service functionality
"""

import json
import subprocess
import time
import threading
import os
import sys
from pathlib import Path
import requests
import signal

# Colors for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def colored_print(color, text):
    print(f"{color}{text}{NC}")

def test_mcp_server():
    """Test MCP server JSON-RPC functionality"""
    colored_print(YELLOW, "🔍 Testing MCP Server...")
    
    try:
        # Test tools/list
        cmd = [
            'node', 
            'mcp-server/dist/index.js'
        ]
        
        test_input = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        })
        
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=test_input, timeout=5)
        
        # Parse the JSON response (first line should be the response)
        lines = stdout.strip().split('\n')
        response_line = None
        for line in lines:
            if line.startswith('{"result"') or line.startswith('{"error"'):
                response_line = line
                break
        
        if response_line:
            response = json.loads(response_line)
            if "result" in response and "tools" in response["result"]:
                tools = response["result"]["tools"]
                colored_print(GREEN, f"✅ MCP Server 정상 - {len(tools)}개 도구 확인")
                for tool in tools:
                    colored_print(GREEN, f"  - {tool['name']}: {tool['description']}")
                return True
            else:
                colored_print(RED, f"❌ MCP Server 응답 오류: {response}")
                return False
        else:
            colored_print(RED, f"❌ MCP Server JSON 응답 없음")
            colored_print(RED, f"STDOUT: {stdout}")
            colored_print(RED, f"STDERR: {stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        colored_print(RED, "❌ MCP Server 응답 시간 초과")
        return False
    except Exception as e:
        colored_print(RED, f"❌ MCP Server 테스트 실패: {e}")
        return False

def test_ai_service():
    """Test AI service by starting it temporarily"""
    colored_print(YELLOW, "🔍 Testing AI Service...")
    
    # Start AI service in background
    ai_process = None
    try:
        ai_process = subprocess.Popen(
            [sys.executable, "ai-services/api.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for service to start
        time.sleep(3)
        
        # Test health endpoint
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                colored_print(GREEN, "✅ AI Service 정상 작동")
                colored_print(GREEN, f"  - 상태: {health_data.get('status', 'unknown')}")
                return True
            else:
                colored_print(RED, f"❌ AI Service 상태 오류: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            colored_print(RED, f"❌ AI Service 연결 실패: {e}")
            return False
            
    except Exception as e:
        colored_print(RED, f"❌ AI Service 시작 실패: {e}")
        return False
    finally:
        if ai_process:
            ai_process.terminate()
            try:
                ai_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                ai_process.kill()

def test_integration():
    """Test MCP server with AI service integration"""
    colored_print(YELLOW, "🔍 Testing Integration...")
    
    # This would require starting both services and testing a search call
    # For now, just verify the configuration
    try:
        # Check if local config exists
        if os.path.exists("claude-config-local.json"):
            with open("claude-config-local.json", "r") as f:
                config = json.load(f)
                colored_print(GREEN, "✅ 로컬 설정 파일 존재")
                return True
        else:
            colored_print(RED, "❌ 로컬 설정 파일 없음")
            return False
    except Exception as e:
        colored_print(RED, f"❌ 통합 테스트 실패: {e}")
        return False

def main():
    """Main test function"""
    colored_print(BLUE, "🚀 Smart File Manager MCP 완전 테스트")
    colored_print(BLUE, "=" * 50)
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    tests = [
        ("MCP Server", test_mcp_server),
        ("AI Service", test_ai_service),
        ("Integration", test_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        colored_print(BLUE, f"\n📋 {test_name} 테스트 시작...")
        if test_func():
            passed += 1
        else:
            failed += 1
    
    colored_print(BLUE, f"\n📊 테스트 결과")
    colored_print(BLUE, "=" * 20)
    colored_print(GREEN, f"✅ 성공: {passed}")
    colored_print(RED, f"❌ 실패: {failed}")
    
    if failed == 0:
        colored_print(GREEN, "\n🎉 모든 테스트 통과!")
        colored_print(GREEN, "Claude Desktop에서 MCP 서버를 사용할 수 있습니다.")
        colored_print(YELLOW, "\n📝 다음 단계:")
        colored_print(YELLOW, "1. claude-config-local.json 내용을 Claude Desktop 설정에 추가")
        colored_print(YELLOW, "2. AI 서비스 실행: cd ai-services && python3 api.py")
        colored_print(YELLOW, "3. Claude Desktop에서 파일 검색 테스트")
    else:
        colored_print(RED, f"\n❌ {failed}개 테스트 실패")
        colored_print(RED, "문제를 해결한 후 다시 테스트해주세요.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)