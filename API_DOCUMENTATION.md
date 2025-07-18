# Smart File Manager API Documentation v4.0

## 개요

Smart File Manager의 멀티미디어 API는 파일 검색, AI 분석, 썸네일 생성 등 다양한 기능을 제공합니다.

- **Base URL**: `http://localhost:8001`
- **Protocol**: HTTP/REST
- **Format**: JSON

## 인증

현재 버전에서는 인증이 필요하지 않습니다. 프로덕션 환경에서는 적절한 인증 메커니즘을 구현해야 합니다.

## 핵심 API 엔드포인트

### 1. 헬스 체크

#### `GET /health`

시스템 상태와 서비스 가용성을 확인합니다.

**응답 예제:**
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "indexer": "available",
    "multimedia_processor": "available",
    "ai_vision": "available",
    "speech_recognition": "available"
  },
  "indexer_stats": {
    "total_files": 94202,
    "indexed_files": 94202,
    "by_extension": {
      ".py": 1523,
      ".jpg": 3421,
      ".mp4": 234
    }
  },
  "multimedia_capabilities": {
    "supported_formats": ["jpg", "png", "mp4", "mp3", "pdf"],
    "ai_services": ["vision", "speech", "ocr"]
  }
}
```

### 2. 멀티미디어 검색

#### `POST /search/multimedia`

파일 내용, 메타데이터, AI 분석 결과를 통합 검색합니다.

**요청 본문:**
```json
{
  "query": "회의록",
  "media_types": ["image", "video", "audio"],
  "categories": ["document", "presentation"],
  "limit": 20,
  "include_ai_analysis": false
}
```

**파라미터:**
- `query` (string, optional): 검색어 (기본값: "")
- `media_types` (array, optional): 미디어 타입 필터
- `categories` (array, optional): 카테고리 필터
- `limit` (integer, optional): 최대 결과 수 (기본값: 20)
- `include_ai_analysis` (boolean, optional): AI 분석 결과 포함 여부

**응답 예제:**
```json
{
  "success": true,
  "count": 3,
  "results": [
    {
      "id": 123,
      "path": "/files/meeting_note.docx",
      "name": "meeting_note.docx",
      "size": 245632,
      "modified_time": 1752652563.801,
      "media_type": "document",
      "category": "document",
      "has_multimedia_content": true,
      "has_ai_analysis": true,
      "has_thumbnail": false,
      "processing_status": {
        "status": "completed",
        "timestamp": 1752652564.0
      },
      "score": 0.95,
      "highlighted_name": "<mark>meeting</mark>_note.docx"
    }
  ],
  "search_method": "multimedia_enhanced",
  "processing_time": 0.023
}
```

### 3. AI 파일 분석

#### `POST /ai/analyze`

파일에 대한 AI 분석을 수행합니다.

**요청 본문:**
```json
{
  "file_path": "/files/image.jpg",
  "analysis_type": "auto",
  "force_reanalysis": false
}
```

**파라미터:**
- `file_path` (string, required): 분석할 파일 경로
- `analysis_type` (string, optional): 분석 타입 ("auto", "image", "speech")
- `force_reanalysis` (boolean, optional): 캐시 무시 여부

**응답 예제:**
```json
{
  "success": true,
  "file_path": "/files/image.jpg",
  "analysis_type": "image",
  "results": {
    "image_analysis": {
      "description": "회의실에서 프레젠테이션하는 모습",
      "confidence": 0.92,
      "metadata": {
        "objects": ["person", "screen", "laptop"],
        "text_detected": ["Q3 Sales Report", "Revenue Growth"]
      }
    }
  },
  "analyzed_at": 1752652565.123
}
```

### 4. 썸네일 생성/조회

#### `GET /media/thumbnail/{file_id}`

미디어 파일의 썸네일을 가져옵니다.

**파라미터:**
- `file_id` (integer, required): 파일 ID
- `size` (string, optional): 썸네일 크기 ("small", "medium", "large")

**응답:**
- Content-Type: image/jpeg 또는 image/png
- 썸네일 이미지 바이너리

### 5. 멀티미디어 통계

#### `GET /stats/multimedia`

시스템의 멀티미디어 처리 통계를 조회합니다.

**응답 예제:**
```json
{
  "indexer_statistics": {
    "total_files": 94202,
    "indexed_files": 94202,
    "last_index_time": 1752652560.0
  },
  "multimedia_capabilities": {
    "image_formats": ["jpg", "png", "gif", "webp"],
    "video_formats": ["mp4", "avi", "mkv", "mov"],
    "audio_formats": ["mp3", "wav", "flac", "m4a"]
  },
  "ai_analysis_coverage": {
    "multimedia": {
      "total": 5234,
      "analyzed": 4892,
      "percentage": 93.5
    }
  },
  "processing_breakdown": {
    "completed": {
      "image": 3421,
      "video": 234,
      "audio": 1237
    },
    "pending": {
      "image": 123,
      "video": 45,
      "audio": 89
    }
  },
  "timestamp": 1752652570.456
}
```

### 6. 파일 처리 상태

#### `GET /processing/status/{file_id}`

특정 파일의 처리 상태를 확인합니다.

**응답 예제:**
```json
{
  "file_id": 123,
  "file_name": "video.mp4",
  "media_type": "multimedia",
  "category": "video",
  "processing_status": {
    "status": "processing",
    "progress": 65,
    "current_step": "extracting_frames"
  },
  "content_extracted": true,
  "has_ai_analysis": false,
  "has_thumbnail": true,
  "processing_complete": false
}
```

### 7. 파일 재처리

#### `POST /processing/reprocess/{file_id}`

파일을 최신 처리 엔진으로 재처리합니다.

**응답 예제:**
```json
{
  "success": true,
  "task_id": "reprocess_123_1752652571",
  "message": "Reprocessing started",
  "file_id": 123
}
```

## 오류 처리

모든 API는 일관된 오류 응답 형식을 사용합니다:

```json
{
  "success": false,
  "error": "오류 메시지",
  "detail": "상세 오류 정보",
  "status_code": 400
}
```

### 일반적인 오류 코드

- `400 Bad Request`: 잘못된 요청 파라미터
- `404 Not Found`: 리소스를 찾을 수 없음
- `500 Internal Server Error`: 서버 오류

## 사용 예제

### Python 예제

```python
import requests

# 파일 검색
response = requests.post('http://localhost:8001/search/multimedia', json={
    'query': '프로젝트 보고서',
    'media_types': ['document'],
    'limit': 10
})

results = response.json()
for file in results['results']:
    print(f"{file['name']} - Score: {file['score']}")

# AI 분석 요청
response = requests.post('http://localhost:8001/ai/analyze', json={
    'file_path': '/files/presentation.jpg',
    'analysis_type': 'image'
})

analysis = response.json()
print(f"이미지 설명: {analysis['results']['image_analysis']['description']}")
```

### cURL 예제

```bash
# 헬스 체크
curl http://localhost:8001/health

# 멀티미디어 검색
curl -X POST http://localhost:8001/search/multimedia \
  -H "Content-Type: application/json" \
  -d '{
    "query": "회의",
    "media_types": ["video", "audio"],
    "limit": 5
  }'

# 통계 조회
curl http://localhost:8001/stats/multimedia | jq
```

## 성능 최적화 팁

1. **검색 최적화**
   - 구체적인 검색어 사용
   - 적절한 필터 적용으로 검색 범위 축소
   - `limit` 파라미터로 결과 수 제한

2. **대용량 파일 처리**
   - 비동기 처리를 위해 `/processing/reprocess` 사용
   - 작업 상태는 `/processing/status`로 확인

3. **캐싱 활용**
   - AI 분석 결과는 자동 캐싱됨
   - `force_reanalysis=false`로 캐시 활용

## 변경 이력

### v4.0 (2024-01-18)
- ✅ `/search/multimedia` 쿼리 파라미터 옵셔널 처리
- ✅ `/stats/multimedia` 타입 안정성 개선
- ✅ Row 객체 처리 로직 개선
- ✅ 디버깅 코드 정리 및 성능 최적화

### v3.0
- 멀티미디어 처리 기능 추가
- AI 비전 및 음성 인식 통합
- FTS5 전문 검색 구현