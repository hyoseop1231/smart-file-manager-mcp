"""
Ollama integration for AI models
"""
import os
import json
import requests
import subprocess
from typing import Dict, Any, List, Optional
import base64
from pathlib import Path

class OllamaService:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.models = {
            "text": "qwen3:30b-a3b",  # 텍스트 분석용 (qwen2.5 대체)
            "vision": "llava:13b",  # 이미지 분석 전용 모델
            "embedding": "nomic-embed-text"  # 임베딩 전용 모델
        }
        
    def check_and_pull_model(self, model_name: str) -> bool:
        """Check if model exists, pull if not"""
        try:
            # Check if model exists
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                
                if model_name not in model_names:
                    print(f"📥 모델 '{model_name}'을 다운로드합니다...")
                    # Pull model
                    pull_response = requests.post(
                        f"{self.base_url}/api/pull",
                        json={"name": model_name},
                        stream=True
                    )
                    
                    # Stream progress
                    for line in pull_response.iter_lines():
                        if line:
                            data = json.loads(line)
                            if "status" in data:
                                print(f"  {data['status']}", end='\r')
                    
                    print(f"\n✅ 모델 '{model_name}' 다운로드 완료!")
                    return True
                else:
                    print(f"✅ 모델 '{model_name}'이 이미 존재합니다.")
                    return True
            return False
        except Exception as e:
            print(f"❌ Ollama 연결 실패: {e}")
            return False
    
    def ensure_all_models(self):
        """Ensure all required models are available"""
        if os.getenv("SKIP_MODEL_CHECK", "false").lower() == "true":
            print("⏭️  모델 체크 스킵 (SKIP_MODEL_CHECK=true)")
            return
        for model_type, model_name in self.models.items():
            self.check_and_pull_model(model_name)
    
    async def generate_text(self, prompt: str, model: Optional[str] = None) -> str:
        """Generate text using Ollama"""
        if not model:
            model = self.models["text"]
            
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                }
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            return ""
        except Exception as e:
            print(f"Error generating text: {e}")
            return ""
    
    async def analyze_image(self, image_path: str, prompt: str) -> str:
        """Analyze image using vision model (llava)"""
        try:
            # Read image and encode to base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Use llava vision model
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.models["vision"],
                    "prompt": prompt,
                    "images": [image_data],
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.5
                    }
                }
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            return ""
        except Exception as e:
            print(f"Error analyzing image: {e}")
            # Fallback to filename-based classification
            file_name = Path(image_path).name
            return f"이미지 파일: {file_name}"
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate text embedding using Ollama"""
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.models["embedding"],
                    "prompt": text
                }
            )
            
            if response.status_code == 200:
                return response.json().get("embedding", [])
            return []
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []
    
    async def categorize_file(self, file_path: str) -> Dict[str, Any]:
        """Categorize a file using AI"""
        file_type = Path(file_path).suffix.lower()
        file_name = Path(file_path).name
        
        # Image files
        if file_type in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            prompt = f"""이미지를 분석하고 다음 정보를 JSON 형식으로 제공하세요:
            1. 카테고리 (예: 문서, 스크린샷, 사진, 아트, 다이어그램 등)
            2. 주요 내용 설명
            3. 추천 폴더명 (한글)
            
            응답 형식:
            {{"category": "카테고리", "description": "설명", "suggested_folder": "폴더명"}}
            """
            
            result = await self.analyze_image(file_path, prompt)
            try:
                return json.loads(result)
            except:
                return {"category": "이미지", "description": file_name, "suggested_folder": "이미지"}
        
        # Text files
        elif file_type in ['.txt', '.md', '.py', '.js', '.java', '.cpp', '.json', '.xml']:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(1000)  # First 1000 chars
                
                prompt = f"""다음 파일 내용을 분석하고 JSON 형식으로 분류하세요:
                파일명: {file_name}
                내용 일부: {content}
                
                응답 형식:
                {{"category": "카테고리", "description": "설명", "suggested_folder": "폴더명"}}
                """
                
                result = await self.generate_text(prompt)
                try:
                    return json.loads(result)
                except:
                    return {"category": "텍스트", "description": file_name, "suggested_folder": "문서"}
            except:
                return {"category": "텍스트", "description": file_name, "suggested_folder": "문서"}
        
        # Default categorization by extension
        else:
            category_map = {
                '.pdf': ("PDF문서", "PDF"),
                '.doc': ("워드문서", "문서"),
                '.docx': ("워드문서", "문서"),
                '.xls': ("엑셀", "스프레드시트"),
                '.xlsx': ("엑셀", "스프레드시트"),
                '.ppt': ("프레젠테이션", "프레젠테이션"),
                '.pptx': ("프레젠테이션", "프레젠테이션"),
                '.zip': ("압축파일", "압축파일"),
                '.mp4': ("동영상", "비디오"),
                '.mp3': ("음악", "오디오")
            }
            
            category, folder = category_map.get(file_type, ("기타", "기타"))
            return {
                "category": category,
                "description": file_name,
                "suggested_folder": folder
            }

# Global instance
ollama_service = OllamaService()