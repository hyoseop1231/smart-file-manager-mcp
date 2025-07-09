#!/usr/bin/env python3

"""
Final MCP Server Test with Simple AI Service
Complete end-to-end test of MCP server functionality
"""

import json
import subprocess
import time
import threading
import os
import sys
import signal
from pathlib import Path
import requests

# Colors for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def colored_print(color, text):
    print(f"{color}{text}{NC}")

class TestRunner:
    def __init__(self):
        self.ai_process = None
        self.ai_port = 8000
        
    def start_ai_service(self):
        """Start the simple AI service"""
        colored_print(YELLOW, "🚀 Starting simple AI service...")
        try:
            self.ai_process = subprocess.Popen(
                [sys.executable, "ai-services/simple_api.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for service to start
            for i in range(10):
                try:
                    response = requests.get(f"http://localhost:{self.ai_port}/health", timeout=2)
                    if response.status_code == 200:
                        colored_print(GREEN, "✅ AI service started successfully")
                        return True
                except:
                    time.sleep(1)
            
            colored_print(RED, "❌ AI service failed to start")
            return False
            
        except Exception as e:
            colored_print(RED, f"❌ Failed to start AI service: {e}")
            return False
    
    def stop_ai_service(self):
        """Stop the AI service"""
        if self.ai_process:
            colored_print(YELLOW, "🛑 Stopping AI service...")
            self.ai_process.terminate()
            try:
                self.ai_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ai_process.kill()
            self.ai_process = None

    def test_mcp_server_basic(self):
        """Test basic MCP server functionality"""
        colored_print(YELLOW, "🔍 Testing MCP Server Basic Functions...")
        
        try:
            # Test tools/list
            test_input = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            })
            
            process = subprocess.run(
                ['node', 'mcp-server/dist/index.js'],
                input=test_input,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Parse response from stdout
            stdout_lines = process.stdout.strip().split('\n')
            response_line = None
            
            for line in stdout_lines:
                if line.startswith('{"result"'):
                    response_line = line
                    break
            
            if response_line:
                response = json.loads(response_line)
                if "result" in response and "tools" in response["result"]:
                    tools = response["result"]["tools"]
                    colored_print(GREEN, f"✅ MCP Server 기본 기능 정상 - {len(tools)}개 도구 확인")
                    
                    expected_tools = ["search_files", "quick_search", "organize_files", "smart_workflow"]
                    tool_names = [tool["name"] for tool in tools]
                    
                    for expected in expected_tools:
                        if expected in tool_names:
                            colored_print(GREEN, f"  ✅ {expected}")
                        else:
                            colored_print(RED, f"  ❌ {expected} 누락")
                            return False
                    
                    return True
                else:
                    colored_print(RED, f"❌ 잘못된 응답 형식: {response}")
                    return False
            else:
                colored_print(RED, "❌ JSON 응답을 찾을 수 없음")
                colored_print(RED, f"STDOUT: {process.stdout}")
                colored_print(RED, f"STDERR: {process.stderr}")
                return False
                
        except Exception as e:
            colored_print(RED, f"❌ MCP 서버 테스트 실패: {e}")
            return False

    def test_mcp_search_tool(self):
        """Test MCP search tool with AI service"""
        colored_print(YELLOW, "🔍 Testing MCP Search Tool...")
        
        try:
            # Test search_files tool
            test_input = json.dumps({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "search_files",
                    "arguments": {
                        "query": "test",
                        "limit": 5
                    }
                }
            })
            
            process = subprocess.run(
                ['node', 'mcp-server/dist/index.js'],
                input=test_input,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            # Parse response
            stdout_lines = process.stdout.strip().split('\n')
            response_line = None
            
            for line in stdout_lines:
                if line.startswith('{"result"'):
                    response_line = line
                    break
            
            if response_line:
                response = json.loads(response_line)
                if "result" in response and "content" in response["result"]:
                    content = response["result"]["content"][0]["text"]
                    search_result = json.loads(content)
                    
                    if "results" in search_result:
                        colored_print(GREEN, f"✅ 검색 기능 정상 - {len(search_result['results'])}개 결과")
                        return True
                    else:
                        colored_print(RED, f"❌ 검색 결과 형식 오류: {search_result}")
                        return False
                else:
                    colored_print(RED, f"❌ 도구 호출 응답 오류: {response}")
                    return False
            else:
                colored_print(RED, "❌ 도구 호출 응답 없음")
                colored_print(RED, f"STDOUT: {process.stdout}")
                colored_print(RED, f"STDERR: {process.stderr}")
                return False
                
        except Exception as e:
            colored_print(RED, f"❌ 검색 도구 테스트 실패: {e}")
            return False

    def test_ai_service_endpoints(self):
        """Test AI service endpoints"""
        colored_print(YELLOW, "🔍 Testing AI Service Endpoints...")
        
        try:
            # Test health
            response = requests.get(f"http://localhost:{self.ai_port}/health")
            if response.status_code == 200:
                health = response.json()
                colored_print(GREEN, f"✅ Health check 성공: {health['status']}")
            else:
                colored_print(RED, f"❌ Health check 실패: {response.status_code}")
                return False
            
            # Test search
            search_data = {
                "query": "test",
                "limit": 3
            }
            response = requests.post(f"http://localhost:{self.ai_port}/search", json=search_data)
            if response.status_code == 200:
                search_result = response.json()
                colored_print(GREEN, f"✅ 검색 API 성공: {len(search_result['results'])}개 결과")
            else:
                colored_print(RED, f"❌ 검색 API 실패: {response.status_code}")
                return False
            
            # Test recent files
            response = requests.get(f"http://localhost:{self.ai_port}/recent?hours=24&limit=10")
            if response.status_code == 200:
                recent_result = response.json()
                colored_print(GREEN, f"✅ 최근 파일 API 성공: {len(recent_result['results'])}개 결과")
            else:
                colored_print(RED, f"❌ 최근 파일 API 실패: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            colored_print(RED, f"❌ AI 서비스 테스트 실패: {e}")
            return False

    def test_integration(self):
        """Test full integration"""
        colored_print(YELLOW, "🔍 Testing Full Integration...")
        
        # Check configuration files
        config_files = ["claude-config-local.json"]
        for config_file in config_files:
            if os.path.exists(config_file):
                colored_print(GREEN, f"✅ {config_file} 존재")
                
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        if "mcpServers" in config and "smart-file-manager" in config["mcpServers"]:
                            colored_print(GREEN, f"✅ {config_file} 형식 정상")
                        else:
                            colored_print(RED, f"❌ {config_file} 형식 오류")
                            return False
                except Exception as e:
                    colored_print(RED, f"❌ {config_file} 파싱 오류: {e}")
                    return False
            else:
                colored_print(RED, f"❌ {config_file} 없음")
                return False
        
        return True

    def run_all_tests(self):
        """Run all tests"""
        colored_print(BLUE, "🚀 Smart File Manager MCP 최종 테스트")
        colored_print(BLUE, "=" * 60)
        
        # Change to project directory
        os.chdir(Path(__file__).parent)
        
        # Start AI service
        if not self.start_ai_service():
            return False
        
        try:
            tests = [
                ("MCP Server Basic", self.test_mcp_server_basic),
                ("AI Service Endpoints", self.test_ai_service_endpoints),
                ("MCP Search Tool", self.test_mcp_search_tool),
                ("Integration", self.test_integration)
            ]
            
            passed = 0
            failed = 0
            
            for test_name, test_func in tests:
                colored_print(BLUE, f"\n📋 {test_name} 테스트...")
                if test_func():
                    passed += 1
                    colored_print(GREEN, f"✅ {test_name} 성공")
                else:
                    failed += 1
                    colored_print(RED, f"❌ {test_name} 실패")
            
            # Results
            colored_print(BLUE, f"\n📊 테스트 결과")
            colored_print(BLUE, "=" * 30)
            colored_print(GREEN, f"✅ 성공: {passed}")
            if failed > 0:
                colored_print(RED, f"❌ 실패: {failed}")
            
            if failed == 0:
                colored_print(GREEN, "\n🎉 모든 테스트 통과!")
                colored_print(GREEN, "Claude Desktop에서 MCP 서버를 사용할 수 있습니다.")
                colored_print(YELLOW, "\n📝 Claude Desktop 설정:")
                colored_print(YELLOW, "1. Claude Desktop 설정 열기")
                colored_print(YELLOW, "2. claude-config-local.json 내용을 MCP 설정에 추가")
                colored_print(YELLOW, "3. Claude Desktop 재시작")
                colored_print(YELLOW, "\n🚀 실행 방법:")
                colored_print(YELLOW, "1. AI 서비스 실행: python3 ai-services/simple_api.py")
                colored_print(YELLOW, "2. Claude Desktop에서 파일 검색 테스트")
                colored_print(YELLOW, "\n💬 테스트 명령어:")
                colored_print(YELLOW, '  "다운로드 폴더에서 이미지 파일 찾아줘"')
                colored_print(YELLOW, '  "최근 24시간 동안 수정된 파일 보여줘"')
                colored_print(YELLOW, '  "PDF 문서만 찾아줘"')
            else:
                colored_print(RED, f"\n❌ {failed}개 테스트 실패")
                colored_print(RED, "문제를 해결한 후 다시 테스트해주세요.")
            
            return failed == 0
            
        finally:
            self.stop_ai_service()

def main():
    try:
        runner = TestRunner()
        success = runner.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        colored_print(YELLOW, "\n🛑 테스트 중단됨")
        return 1
    except Exception as e:
        colored_print(RED, f"\n❌ 테스트 실행 오류: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())