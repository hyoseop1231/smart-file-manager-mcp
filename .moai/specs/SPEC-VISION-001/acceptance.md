---
id: SPEC-VISION-001
spec_ref: SPEC-VISION-001/spec.md
plan_ref: SPEC-VISION-001/plan.md
version: "1.0.0"
status: "planned"
created: "2026-01-10"
---

# SPEC-VISION-001: Acceptance Criteria

## 1. 개요

이 문서는 SPEC-VISION-001 (Vision 분석 서비스 통합)의 인수 기준을 Given-When-Then 형식으로 정의한다.

---

## 2. 이미지 분석 시나리오

### AC-IMG-001: 캐시 미스 시 API 분석

**Scenario**: 새로운 이미지 분석 요청 시 API를 통해 분석한다

```gherkin
Given 분석되지 않은 새로운 JPEG 이미지 파일이 존재할 때
  And 이미지 크기가 5MB이고 해상도가 1920x1080일 때
  And OpenRouter API가 정상 동작 중일 때
When VisionService.analyze_image()가 호출되면
Then OpenRouterClient.analyze_image()가 호출되어야 하고
  And Primary 모델(gemini-2.0-flash-001)로 분석이 수행되어야 하고
  And 분석 결과가 ImageAnalysisResult 형식으로 반환되어야 하고
  And 결과에 description, objects, scene, tags 필드가 포함되어야 하고
  And 결과가 캐시에 7일 TTL로 저장되어야 하고
  And 비용이 CostTracker에 기록되어야 하고
  And 처리 시간이 3초 이내여야 한다
```

**TAG**: VIS-001-E002, VIS-001-U002, VIS-001-U003, VIS-001-U004

---

### AC-IMG-002: 캐시 히트 시 즉시 반환

**Scenario**: 이전에 분석된 이미지 요청 시 캐시에서 반환한다

```gherkin
Given 이전에 분석되어 캐시에 저장된 이미지 파일이 존재할 때
  And 캐시 TTL이 아직 만료되지 않았을 때
When VisionService.analyze_image()가 호출되면
Then 캐시에서 분석 결과를 조회해야 하고
  And OpenRouterClient.analyze_image()가 호출되지 않아야 하고
  And 캐시된 ImageAnalysisResult가 반환되어야 하고
  And 결과의 cached 필드가 True여야 하고
  And 처리 시간이 50ms 이내여야 한다
```

**TAG**: VIS-001-E001, VIS-001-U001

---

### AC-IMG-003: 강제 새로고침

**Scenario**: force_refresh 옵션으로 캐시를 무시하고 새로 분석한다

```gherkin
Given 이전에 분석되어 캐시에 저장된 이미지 파일이 존재할 때
When VisionService.analyze_image(force_refresh=True)가 호출되면
Then 캐시를 확인하지 않고 API 분석을 수행해야 하고
  And OpenRouterClient.analyze_image()가 호출되어야 하고
  And 새로운 분석 결과가 캐시에 저장되어야 하고
  And 결과의 cached 필드가 False여야 한다
```

**TAG**: VIS-001-E010

---

### AC-IMG-004: Primary 모델 실패 시 Fallback

**Scenario**: Primary 모델 실패 시 Fallback 1으로 전환한다

```gherkin
Given JPEG 이미지 파일이 존재할 때
  And Primary 모델(gemini-2.0-flash-001)이 500 에러를 반환할 때
  And Fallback 1 모델(qwen2.5-vl-32b-instruct)이 정상 동작 중일 때
When VisionService.analyze_image()가 호출되면
Then Primary 모델 호출이 실패해야 하고
  And Fallback 1 모델로 자동 전환되어야 하고
  And Fallback 1 모델로 분석이 수행되어야 하고
  And 결과의 model_used 필드가 "qwen/qwen2.5-vl-32b-instruct"여야 한다
```

**TAG**: VIS-001-E003

---

### AC-IMG-005: 전체 API 실패 시 로컬 Fallback

**Scenario**: 모든 API 모델 실패 시 로컬 분석으로 대체한다

```gherkin
Given JPEG 이미지 파일이 존재할 때
  And 모든 OpenRouter 모델(Primary, Fallback 1, Fallback 2)이 실패할 때
When VisionService.analyze_image()가 호출되면
Then 로컬 메타데이터 분석이 수행되어야 하고
  And 결과에 width, height, format, size_bytes가 포함되어야 하고
  And 결과의 model_used 필드가 "local"이어야 하고
  And 결과의 estimated_cost가 0이어야 하고
  And AnalysisFailedError가 발생하지 않아야 한다
```

**TAG**: VIS-001-E005

---

### AC-IMG-006: 대용량 이미지 자동 리사이징

**Scenario**: 20MB를 초과하는 이미지는 자동으로 리사이징한다

```gherkin
Given 25MB 크기의 8000x6000 해상도 JPEG 이미지가 존재할 때
When VisionService.analyze_image()가 호출되면
Then 이미지가 최대 4096px로 자동 리사이징되어야 하고
  And 리사이징된 이미지로 API 분석이 수행되어야 하고
  And 결과가 정상적으로 반환되어야 한다
```

**TAG**: VIS-001-E008

---

### AC-IMG-007: 지원되지 않는 형식 거부

**Scenario**: 지원되지 않는 이미지 형식은 명확한 에러로 거부한다

```gherkin
Given HEIC 형식의 이미지 파일이 존재할 때
When VisionService.analyze_image()가 호출되면
Then UnsupportedFormatError가 발생해야 하고
  And 에러 메시지에 "HEIC format is not supported"가 포함되어야 하고
  And 지원되는 형식 목록이 에러 메시지에 포함되어야 한다
```

**TAG**: VIS-001-N001

---

### AC-IMG-008: 파일 미존재 에러

**Scenario**: 존재하지 않는 파일 경로는 에러를 반환한다

```gherkin
Given 존재하지 않는 파일 경로가 주어질 때
When VisionService.analyze_image()가 호출되면
Then FileNotFoundError가 발생해야 하고
  And 에러 메시지에 파일 경로가 포함되어야 한다
```

**TAG**: VIS-001-N002

---

### AC-IMG-009: 손상된 이미지 처리

**Scenario**: 손상된 이미지 파일은 명확한 에러로 처리한다

```gherkin
Given 손상되어 디코딩할 수 없는 JPEG 파일이 존재할 때
When VisionService.analyze_image()가 호출되면
Then CorruptedFileError가 발생해야 하고
  And 에러 메시지에 "Cannot decode image file"이 포함되어야 한다
```

**TAG**: VIS-001-S005

---

## 3. 비디오 분석 시나리오

### AC-VID-001: 비디오 분석 기본 플로우

**Scenario**: 비디오 파일을 키프레임 추출 후 분석한다

```gherkin
Given 1분 길이의 MP4 비디오 파일이 존재할 때
  And FFmpeg가 설치되어 있을 때
  And OpenRouter API가 정상 동작 중일 때
When VisionService.analyze_video()가 호출되면
Then FFmpeg로 키프레임이 추출되어야 하고
  And 최대 5개의 대표 프레임이 선택되어야 하고
  And 각 프레임에 대해 이미지 분석이 수행되어야 하고
  And 결과가 VideoAnalysisResult 형식으로 반환되어야 하고
  And 결과에 summary, frame_analyses, metadata가 포함되어야 하고
  And 처리 시간이 30초 이내여야 한다
```

**TAG**: VIS-001-E006, VIS-001-E007

---

### AC-VID-002: 긴 비디오 샘플링 간격 조정

**Scenario**: 10분을 초과하는 비디오는 샘플링 간격을 증가시킨다

```gherkin
Given 15분 길이의 MP4 비디오 파일이 존재할 때
When VisionService.analyze_video()가 호출되면
Then 키프레임 추출 간격이 60초로 설정되어야 하고
  And 최대 30개의 키프레임이 추출되어야 하고
  And 분석할 대표 프레임이 5개로 제한되어야 한다
```

**TAG**: VIS-001-S004

---

### AC-VID-003: FFmpeg 미설치 에러

**Scenario**: FFmpeg가 설치되지 않은 환경에서 비디오 분석 시 에러를 반환한다

```gherkin
Given MP4 비디오 파일이 존재할 때
  And FFmpeg가 시스템에 설치되어 있지 않을 때
When VisionService.analyze_video()가 호출되면
Then DependencyError가 발생해야 하고
  And 에러 메시지에 "FFmpeg is required for video analysis"가 포함되어야 하고
  And FFmpeg 설치 가이드 URL이 에러에 포함되어야 한다
```

**TAG**: VIS-001-N007

---

### AC-VID-004: 지원되지 않는 비디오 형식

**Scenario**: 지원되지 않는 비디오 코덱은 에러를 반환한다

```gherkin
Given WMV 형식의 비디오 파일이 존재할 때
When VisionService.analyze_video()가 호출되면
Then UnsupportedFormatError가 발생해야 하고
  And 에러 메시지에 지원되는 형식 목록이 포함되어야 한다
```

**TAG**: VIS-001-N006

---

## 4. 예산 관리 시나리오

### AC-BUDGET-001: 일일 예산 초과 시 Free 티어 전환

**Scenario**: 일일 예산 초과 시 Free 티어 모델만 사용한다

```gherkin
Given 일일 API 사용 비용이 $0.95일 때
  And 이미지 분석 요청이 예상 비용 $0.10일 때
When VisionService.analyze_image()가 호출되면
Then 예산 초과가 감지되어야 하고
  And Free 티어 모델(gemini-2.0-flash-exp:free)로 자동 전환되어야 하고
  And 결과의 model_used가 Free 티어 모델이어야 하고
  And 결과의 estimated_cost가 0이어야 한다
```

**TAG**: VIS-001-S001

---

### AC-BUDGET-002: 월간 예산 초과 시 유료 API 거부

**Scenario**: 월간 예산 초과 시 유료 API 호출을 거부한다

```gherkin
Given 월간 API 사용 비용이 $30.00을 초과했을 때
  And 캐시에 분석 결과가 없을 때
When VisionService.analyze_image()가 호출되면
Then Free 티어 모델로만 분석이 시도되어야 하고
  And 유료 모델(Primary, Fallback 1)은 건너뛰어야 하고
  And 결과의 estimated_cost가 0이어야 한다
```

**TAG**: VIS-001-S002, VIS-001-N005

---

## 5. 캐시 시나리오

### AC-CACHE-001: Redis 장애 시 MemoryCache 사용

**Scenario**: Redis가 사용 불가 시 MemoryCache로 대체한다

```gherkin
Given Redis 서버가 연결 불가 상태일 때
When VisionService.analyze_image()가 호출되면
Then MemoryCache로 자동 전환되어야 하고
  And 분석이 정상적으로 수행되어야 하고
  And 결과가 MemoryCache에 저장되어야 한다
```

**TAG**: VIS-001-S003

---

### AC-CACHE-002: Race Condition 방지

**Scenario**: 동일 파일에 대한 동시 분석 요청 시 중복 API 호출을 방지한다

```gherkin
Given 동일한 이미지 파일에 대해 5개의 동시 분석 요청이 발생할 때
  And 캐시에 분석 결과가 없을 때
When 모든 요청이 동시에 처리될 때
Then OpenRouterClient.analyze_image()는 1회만 호출되어야 하고
  And 모든 요청이 동일한 분석 결과를 받아야 하고
  And 중복 비용이 발생하지 않아야 한다
```

**TAG**: VIS-001-N004

---

## 6. 배치 분석 시나리오

### AC-BATCH-001: 여러 파일 배치 분석

**Scenario**: 여러 이미지 파일을 동시에 분석한다

```gherkin
Given 10개의 JPEG 이미지 파일이 존재할 때
  And 모든 파일이 캐시에 없을 때
When VisionService.batch_analyze(paths, concurrency=5)가 호출되면
Then 동시에 최대 5개의 분석이 병렬로 수행되어야 하고
  And 모든 파일에 대해 분석 결과가 반환되어야 하고
  And 각 결과가 리스트로 정리되어야 하고
  And 처리 시간이 단일 순차 처리보다 빨라야 한다
```

---

## 7. 메트릭 및 로깅 시나리오

### AC-METRIC-001: 분석 결과에 메트릭 포함

**Scenario**: 분석 결과에 처리 시간, 모델, 비용 정보가 포함된다

```gherkin
Given JPEG 이미지 파일이 존재할 때
When VisionService.analyze_image()가 호출되면
Then 결과에 processing_time_ms 필드가 포함되어야 하고
  And 결과에 model_used 필드가 포함되어야 하고
  And 결과에 estimated_cost 필드가 포함되어야 하고
  And 결과에 cached 필드가 포함되어야 한다
```

**TAG**: VIS-001-U007

---

## 8. 성능 기준

### AC-PERF-001: 이미지 분석 성능

```gherkin
Given 5MB JPEG 이미지가 존재할 때
When VisionService.analyze_image()가 100회 호출될 때
Then P95 응답 시간이 3초 이내여야 하고
  And P50 응답 시간이 2초 이내여야 하고
  And 메모리 사용량이 500MB를 초과하지 않아야 한다
```

### AC-PERF-002: 비디오 분석 성능

```gherkin
Given 1분 길이의 50MB MP4 비디오가 존재할 때
When VisionService.analyze_video()가 10회 호출될 때
Then P95 응답 시간이 30초 이내여야 하고
  And 키프레임 추출 시간이 5초 이내여야 하고
  And 메모리 사용량이 1GB를 초과하지 않아야 한다
```

### AC-PERF-003: 캐시 조회 성능

```gherkin
Given 캐시에 분석 결과가 저장되어 있을 때
When VisionService.analyze_image()가 1000회 호출될 때
Then P95 응답 시간이 50ms 이내여야 하고
  And P50 응답 시간이 10ms 이내여야 한다
```

---

## 9. Definition of Done

### 9.1 기능 완료 조건

- [ ] 모든 EARS 요구사항이 구현됨 (Ubiquitous 7개, Event-driven 10개, State-driven 6개, Unwanted 7개)
- [ ] 모든 인수 테스트 시나리오가 통과함 (20+ 시나리오)
- [ ] OpenRouterClient 통합이 완료됨
- [ ] 3-tier Fallback 체인이 구현됨
- [ ] 캐시 통합 (Redis + MemoryCache)이 완료됨
- [ ] 비용 추적이 통합됨

### 9.2 품질 완료 조건

- [ ] 테스트 커버리지 90% 이상
- [ ] 모든 단위 테스트 통과
- [ ] 모든 통합 테스트 통과
- [ ] ruff 린터 경고 0개
- [ ] mypy 타입 체크 통과
- [ ] 모든 함수에 docstring 작성

### 9.3 성능 완료 조건

- [ ] 이미지 분석 P95 < 3초
- [ ] 비디오 분석 (1분) < 30초
- [ ] 캐시 조회 P95 < 50ms
- [ ] 메모리 사용량 기준 충족

### 9.4 문서 완료 조건

- [ ] API 문서 (docstring) 작성
- [ ] 사용 예제 코드 작성
- [ ] 에러 처리 가이드 작성
- [ ] FFmpeg 설치 가이드 작성

---

## 10. TAG 추적표

| TAG ID | 시나리오 | 요구사항 | 상태 |
|--------|----------|----------|------|
| VIS-001-U001 | AC-IMG-002 | REQ-U-001 | Pending |
| VIS-001-U002 | AC-IMG-001 | REQ-U-002 | Pending |
| VIS-001-U003 | AC-IMG-001 | REQ-U-003 | Pending |
| VIS-001-U004 | AC-IMG-001 | REQ-U-004 | Pending |
| VIS-001-U007 | AC-METRIC-001 | REQ-U-007 | Pending |
| VIS-001-E001 | AC-IMG-002 | REQ-E-001 | Pending |
| VIS-001-E002 | AC-IMG-001 | REQ-E-002 | Pending |
| VIS-001-E003 | AC-IMG-004 | REQ-E-003 | Pending |
| VIS-001-E005 | AC-IMG-005 | REQ-E-005 | Pending |
| VIS-001-E006 | AC-VID-001 | REQ-E-006 | Pending |
| VIS-001-E007 | AC-VID-001 | REQ-E-007 | Pending |
| VIS-001-E008 | AC-IMG-006 | REQ-E-008 | Pending |
| VIS-001-E010 | AC-IMG-003 | REQ-E-010 | Pending |
| VIS-001-S001 | AC-BUDGET-001 | REQ-S-001 | Pending |
| VIS-001-S002 | AC-BUDGET-002 | REQ-S-002 | Pending |
| VIS-001-S003 | AC-CACHE-001 | REQ-S-003 | Pending |
| VIS-001-S004 | AC-VID-002 | REQ-S-004 | Pending |
| VIS-001-S005 | AC-IMG-009 | REQ-S-005 | Pending |
| VIS-001-N001 | AC-IMG-007 | REQ-N-001 | Pending |
| VIS-001-N002 | AC-IMG-008 | REQ-N-002 | Pending |
| VIS-001-N004 | AC-CACHE-002 | REQ-N-004 | Pending |
| VIS-001-N005 | AC-BUDGET-002 | REQ-N-005 | Pending |
| VIS-001-N006 | AC-VID-004 | REQ-N-006 | Pending |
| VIS-001-N007 | AC-VID-003 | REQ-N-007 | Pending |
