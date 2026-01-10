---
id: SPEC-STT-001
document: acceptance
version: "1.0.0"
created: "2026-01-10"
updated: "2026-01-10"
---

# SPEC-STT-001: 인수 조건

## 1. 테스트 시나리오

### 1.1 Ubiquitous Requirements 테스트

#### TC-U001: 지원 오디오 포맷 처리

```gherkin
Feature: 지원 오디오 포맷 처리
  TAG: STT-001-U001

  Scenario: MP3 파일 STT 처리
    Given STTService가 초기화되어 있다
    And "test_audio.mp3" 파일이 존재한다
    When analyze_audio("test_audio.mp3")를 호출한다
    Then AudioAnalysisResult가 반환된다
    And transcription 필드에 텍스트가 포함된다

  Scenario: WAV 파일 STT 처리
    Given STTService가 초기화되어 있다
    And "test_audio.wav" 파일이 존재한다
    When analyze_audio("test_audio.wav")를 호출한다
    Then AudioAnalysisResult가 반환된다

  Scenario: FLAC 파일 STT 처리
    Given STTService가 초기화되어 있다
    And "test_audio.flac" 파일이 존재한다
    When analyze_audio("test_audio.flac")를 호출한다
    Then AudioAnalysisResult가 반환된다

  Scenario: M4A 파일 STT 처리
    Given STTService가 초기화되어 있다
    And "test_audio.m4a" 파일이 존재한다
    When analyze_audio("test_audio.m4a")를 호출한다
    Then AudioAnalysisResult가 반환된다

  Scenario: OGG 파일 STT 처리
    Given STTService가 초기화되어 있다
    And "test_audio.ogg" 파일이 존재한다
    When analyze_audio("test_audio.ogg")를 호출한다
    Then AudioAnalysisResult가 반환된다
```

#### TC-U002: 캐시 기반 중복 방지

```gherkin
Feature: 캐시 기반 중복 처리 방지
  TAG: STT-001-U002

  Scenario: 동일 파일 두 번째 요청 시 캐시 반환
    Given STTService가 캐시와 함께 초기화되어 있다
    And "test_audio.mp3"가 한 번 처리되었다
    When 동일한 "test_audio.mp3"에 대해 analyze_audio()를 호출한다
    Then AudioAnalysisResult.cached가 True이다
    And 처리 시간이 10ms 미만이다

  Scenario: force_refresh=True 시 캐시 무시
    Given STTService가 캐시와 함께 초기화되어 있다
    And "test_audio.mp3"가 캐시에 저장되어 있다
    When analyze_audio("test_audio.mp3", force_refresh=True)를 호출한다
    Then AudioAnalysisResult.cached가 False이다
    And 새로운 분석이 수행된다
```

#### TC-U003: 결과 타임스탬프 포함

```gherkin
Feature: 타임스탬프 및 신뢰도 포함
  TAG: STT-001-U003

  Scenario: 세그먼트 타임스탬프 포함
    Given STTService가 초기화되어 있다
    When analyze_audio("test_audio.mp3")를 호출한다
    Then 결과의 segments 리스트가 비어있지 않다
    And 각 segment에 start, end, text, confidence가 포함된다
    And start < end 이다

  Scenario: 단어 타임스탬프 포함
    Given STTService가 초기화되어 있다
    When analyze_audio("test_audio.mp3", word_timestamps=True)를 호출한다
    Then 결과의 segments[*].words 리스트가 비어있지 않다
    And 각 word에 word, start, end, probability가 포함된다

  Scenario: 언어 감지 정보 포함
    Given STTService가 초기화되어 있다
    When 한국어 오디오에 대해 analyze_audio()를 호출한다
    Then detected_language가 "ko"이다
    And language_probability가 0.5 이상이다
```

#### TC-U004: 통계 추적

```gherkin
Feature: 처리 통계 추적
  TAG: STT-001-U004

  Scenario: 총 처리 수 추적
    Given STTService가 초기화되어 있다
    And 초기 통계가 0이다
    When 3개의 오디오 파일을 처리한다
    Then get_analysis_stats().total_analyses가 3이다

  Scenario: 캐시 히트율 추적
    Given STTService가 초기화되어 있다
    And 1개의 파일을 처리했다
    When 동일 파일을 다시 처리한다
    Then get_analysis_stats().cached_analyses가 1이다

  Scenario: 평균 처리 시간 추적
    Given STTService가 초기화되어 있다
    When 여러 파일을 처리한다
    Then get_analysis_stats().average_realtime_factor가 계산된다
```

#### TC-U005: 처리 속도 목표

```gherkin
Feature: 4배 실시간 속도 달성
  TAG: STT-001-U005

  Scenario: GPU에서 Realtime Factor 0.25x 이하
    Given STTService가 CUDA 디바이스로 초기화되어 있다
    And 60초 길이의 오디오 파일이 있다
    When analyze_audio()를 호출한다
    Then AudioAnalysisResult.realtime_factor가 0.25 이하이다
    And processing_time_ms가 15000 이하이다

  Scenario: CPU에서 Realtime Factor 1.0x 이하
    Given STTService가 CPU 디바이스로 초기화되어 있다
    And 60초 길이의 오디오 파일이 있다
    When analyze_audio()를 호출한다
    Then AudioAnalysisResult.realtime_factor가 1.0 이하이다
```

### 1.2 Event-Driven Requirements 테스트

#### TC-E001: 서비스 초기화

```gherkin
Feature: 서비스 초기화
  TAG: STT-001-E001

  Scenario: 기본 초기화
    Given Faster-Whisper 패키지가 설치되어 있다
    When STTService()를 생성한다
    Then 서비스가 성공적으로 초기화된다
    And device_used가 "cuda" 또는 "cpu"이다

  Scenario: 명시적 디바이스 지정
    Given CUDA가 사용 가능하다
    When STTService(device="cuda")를 생성한다
    Then device가 "cuda"로 설정된다

  Scenario: CPU 폴백
    Given CUDA가 사용 불가능하다
    When STTService(device="auto")를 생성한다
    Then device가 "cpu"로 설정된다
```

#### TC-E002: 분석 흐름

```gherkin
Feature: 분석 처리 흐름
  TAG: STT-001-E002

  Scenario: 캐시 미스 시 전체 흐름
    Given STTService가 캐시와 함께 초기화되어 있다
    And "new_audio.mp3"가 캐시에 없다
    When analyze_audio("new_audio.mp3")를 호출한다
    Then 캐시 조회가 수행된다
    And STT 변환이 수행된다
    And 결과가 캐시에 저장된다
    And AudioAnalysisResult가 반환된다
```

#### TC-E003: 비지원 포맷 에러

```gherkin
Feature: 비지원 포맷 처리
  TAG: STT-001-E003

  Scenario: TXT 파일 거부
    Given STTService가 초기화되어 있다
    When analyze_audio("test.txt")를 호출한다
    Then UnsupportedFormatError가 발생한다
    And 에러 메시지에 지원 포맷 목록이 포함된다

  Scenario: 이미지 파일 거부
    Given STTService가 초기화되어 있다
    When analyze_audio("image.jpg")를 호출한다
    Then UnsupportedFormatError가 발생한다
```

#### TC-E004: 캐시 히트 즉시 반환

```gherkin
Feature: 캐시 히트 시 즉시 반환
  TAG: STT-001-E004

  Scenario: 캐시된 결과 반환
    Given "test_audio.mp3"가 캐시에 저장되어 있다
    When analyze_audio("test_audio.mp3")를 호출한다
    Then STT 모델이 호출되지 않는다
    And 캐시된 AudioAnalysisResult가 반환된다
    And result.cached가 True이다
```

#### TC-E005: 배치 분석 동시성

```gherkin
Feature: 배치 분석 동시성 제어
  TAG: STT-001-E005

  Scenario: 동시 처리 제한
    Given STTService가 초기화되어 있다
    And 10개의 오디오 파일이 있다
    When batch_analyze(paths, concurrency=3)를 호출한다
    Then 최대 3개의 파일이 동시에 처리된다
    And 모든 파일이 성공적으로 처리된다

  Scenario: 일부 파일 실패 시 계속 처리
    Given 10개의 파일 중 2개가 손상되어 있다
    When batch_analyze(paths)를 호출한다
    Then 8개의 성공 결과가 반환된다
    And 예외가 전파되지 않는다
```

### 1.3 State-Driven Requirements 테스트

#### TC-S001: CUDA GPU 추론

```gherkin
Feature: CUDA GPU 추론
  TAG: STT-001-S001

  Scenario: CUDA 가용 시 float16 사용
    Given CUDA가 사용 가능하다
    When STTService(device="auto", compute_type="auto")를 생성한다
    Then device_used가 "cuda"이다
    And compute_type이 "float16"이다
```

#### TC-S002: CPU 폴백

```gherkin
Feature: CPU 폴백 처리
  TAG: STT-001-S002

  Scenario: GPU 미사용 시 int8 양자화
    Given CUDA가 사용 불가능하다
    When STTService(device="auto", compute_type="auto")를 생성한다
    Then device_used가 "cpu"이다
    And compute_type이 "int8"이다
```

### 1.4 Unwanted Behavior Requirements 테스트

#### TC-N001: 오디오 길이 제한

```gherkin
Feature: 오디오 길이 제한
  TAG: STT-001-N001

  Scenario: 2시간 초과 파일 거부
    Given STTService가 초기화되어 있다
    And 오디오 길이가 7201초(2시간 초과)인 파일이 있다
    When analyze_audio()를 호출한다
    Then AudioTooLongError가 발생한다
    And 에러 메시지에 최대 허용 시간이 포함된다

  Scenario: 2시간 이하 파일 허용
    Given 오디오 길이가 7200초(정확히 2시간)인 파일이 있다
    When analyze_audio()를 호출한다
    Then 정상적으로 처리된다
```

#### TC-N002: 파일 크기 제한

```gherkin
Feature: 파일 크기 제한
  TAG: STT-001-N002

  Scenario: 100MB 초과 파일 거부
    Given STTService가 초기화되어 있다
    And 파일 크기가 101MB인 오디오가 있다
    When analyze_audio()를 호출한다
    Then FileTooLargeError가 발생한다

  Scenario: 100MB 이하 파일 허용
    Given 파일 크기가 100MB인 오디오가 있다
    When analyze_audio()를 호출한다
    Then 정상적으로 처리된다
```

#### TC-N003: 손상된 파일 처리

```gherkin
Feature: 손상된 파일 처리
  TAG: STT-001-N003

  Scenario: 손상된 오디오 파일 에러
    Given STTService가 초기화되어 있다
    And "corrupted.mp3"가 손상된 파일이다
    When analyze_audio("corrupted.mp3")를 호출한다
    Then AudioProcessingError가 발생한다
    And 에러 메시지에 원인이 포함된다
```

---

## 2. 품질 게이트

### 2.1 코드 품질

| 항목 | 기준 | 도구 |
|------|------|------|
| 테스트 커버리지 | >= 85% | pytest-cov |
| 린트 통과 | 0 warnings | ruff |
| 타입 체크 | 0 errors | mypy |
| 문서화 | 모든 public API | docstring |

### 2.2 성능 기준

| 메트릭 | GPU 기준 | CPU 기준 |
|--------|----------|----------|
| Realtime Factor | <= 0.25x | <= 1.0x |
| 캐시 히트 응답 | < 10ms | < 10ms |
| 메모리 사용량 | < 8GB VRAM | < 4GB RAM |

### 2.3 기능 완성도

- [ ] 모든 Ubiquitous 요구사항 구현
- [ ] 모든 Event-Driven 요구사항 구현
- [ ] 모든 State-Driven 요구사항 구현
- [ ] 모든 Unwanted Behavior 요구사항 구현
- [ ] 선택적 요구사항 1개 이상 구현

---

## 3. Definition of Done

### 3.1 개발 완료 조건

- [ ] `services/stt_service.py` 구현 완료
- [ ] `services/stt_models.py` 구현 완료
- [ ] `core/config.py` STT 설정 추가
- [ ] `core/constants.py` SUPPORTED_AUDIO_FORMATS 추가
- [ ] 단위 테스트 작성 (커버리지 >= 85%)
- [ ] 통합 테스트 작성

### 3.2 품질 검증 완료 조건

- [ ] ruff 린트 통과
- [ ] mypy 타입 체크 통과
- [ ] pytest 전체 통과
- [ ] 성능 벤치마크 목표 달성

### 3.3 문서화 완료 조건

- [ ] API 문서 작성 (docstring)
- [ ] README 업데이트
- [ ] CHANGELOG 업데이트

---

## 4. 검증 방법

### 4.1 단위 테스트

```bash
# 전체 테스트 실행
pytest tests/services/test_stt_service.py -v

# 커버리지 포함
pytest tests/services/test_stt_service.py --cov=smart_file_manager.services.stt_service --cov-report=html

# 특정 테스트 실행
pytest -k "test_supported_audio_formats" -v
```

### 4.2 성능 벤치마크

```bash
# 벤치마크 스크립트 실행
python scripts/benchmark_stt.py --device cuda --samples 10

# 예상 출력:
# Realtime Factor (GPU): 0.18x
# Average Processing Time: 10.8s for 60s audio
# Memory Usage: 6.2GB VRAM
```

### 4.3 수동 검증

```python
# Python REPL에서 검증
from smart_file_manager.services.stt_service import STTService
from pathlib import Path

service = STTService()
result = await service.analyze_audio(Path("test.mp3"))

print(f"Transcription: {result.transcription[:100]}...")
print(f"Language: {result.detected_language}")
print(f"Realtime Factor: {result.realtime_factor:.2f}x")
print(f"Cached: {result.cached}")
```
