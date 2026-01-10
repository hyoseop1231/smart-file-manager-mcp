---
spec_id: SPEC-CLASS-001
version: "1.0.0"
created: "2026-01-10"
---

# SPEC-CLASS-001: 인수 조건

## 1. 개요

이 문서는 SPEC-CLASS-001 (파일 분류 서비스)의 인수 조건을 Given-When-Then 형식으로 정의한다.

---

## 2. 핵심 분류 기능 테스트

### 2.1 단일 파일 분류 (캐시 미스)

```gherkin
Feature: 단일 파일 분류
  파일을 AI 기반으로 자동 분류한다.

  Scenario: 이미지 파일 분류 (캐시 미스)
    Given VisionService가 정상 동작 중이다
    And Redis 캐시에 해당 파일의 분류 결과가 없다
    And 유효한 JPEG 이미지 파일이 존재한다
    When classify_file 메서드를 호출한다
    Then VisionService.analyze_image가 호출된다
    And ClassificationResult가 반환된다
    And classification.category가 기본 카테고리 중 하나이다
    And classification.confidence가 0.0 이상 1.0 이하이다
    And tags.tags_en 목록이 비어있지 않다
    And tags.tags_ko 목록이 비어있지 않다
    And 결과가 Redis 캐시에 저장된다
    And processing_time_ms가 5000 미만이다
```

### 2.2 단일 파일 분류 (캐시 히트)

```gherkin
  Scenario: 이미지 파일 분류 (캐시 히트)
    Given Redis 캐시에 해당 파일의 분류 결과가 존재한다
    And 유효한 JPEG 이미지 파일이 존재한다
    When classify_file 메서드를 호출한다
    Then VisionService.analyze_image가 호출되지 않는다
    And 캐시된 ClassificationResult가 반환된다
    And cached 필드가 True이다
    And processing_time_ms가 50 미만이다
```

### 2.3 강제 새로고침

```gherkin
  Scenario: 분류 강제 새로고침
    Given Redis 캐시에 해당 파일의 분류 결과가 존재한다
    And 유효한 JPEG 이미지 파일이 존재한다
    When classify_file 메서드를 force_refresh=True로 호출한다
    Then VisionService.analyze_image가 호출된다
    And 새로운 ClassificationResult가 반환된다
    And cached 필드가 False이다
    And 새 결과가 캐시에 저장된다
```

---

## 3. 분류 엔진 테스트

### 3.1 분류 우선순위

```gherkin
Feature: 분류 우선순위
  사용자 규칙 > AI 분류 > 메타데이터 규칙 순으로 적용한다.

  Scenario: 사용자 정의 규칙 우선 적용
    Given 사용자 정의 카테고리 규칙이 등록되어 있다
    And 해당 규칙이 파일에 매칭된다
    When ClassificationEngine.classify를 호출한다
    Then classification.method가 "user_rule"이다
    And classification.category가 사용자 정의 카테고리이다

  Scenario: AI 분류 적용 (사용자 규칙 미매칭)
    Given 사용자 정의 규칙이 파일에 매칭되지 않는다
    And VisionService 분석 결과가 존재한다
    When ClassificationEngine.classify를 호출한다
    Then classification.method가 "ai"이다
    And VisionService 결과 기반 카테고리가 할당된다

  Scenario: 메타데이터 분류 적용 (AI 분석 없음)
    Given 사용자 정의 규칙이 매칭되지 않는다
    And VisionService 분석 결과가 없다 (None)
    When ClassificationEngine.classify를 호출한다
    Then classification.method가 "metadata"이다
    And 파일 확장자 및 속성 기반 카테고리가 할당된다
```

### 3.2 신뢰도 점수

```gherkin
Feature: 신뢰도 점수
  분류 결과에 신뢰도 점수를 포함한다.

  Scenario: 높은 신뢰도 분류
    Given VisionService 분석 결과의 objects 신뢰도가 높다
    When 분류를 수행한다
    Then classification.confidence가 0.7 이상이다
    And classification.requires_review가 False이다

  Scenario: 낮은 신뢰도 분류
    Given VisionService 분석 결과의 objects 신뢰도가 낮다
    When 분류를 수행한다
    Then classification.confidence가 0.5 미만이다
    And classification.requires_review가 True이다
```

---

## 4. 태그 생성 테스트

### 4.1 태그 생성

```gherkin
Feature: 태그 생성
  VisionService 결과와 메타데이터를 기반으로 태그를 생성한다.

  Scenario: VisionService 결과 기반 태그 생성
    Given VisionService 분석 결과가 존재한다
    And objects에 ["person", "car", "building"]이 포함되어 있다
    And scene이 "outdoor"이다
    When TagGenerator.generate_tags를 호출한다
    Then tags_en에 "person", "car", "building", "outdoor"가 포함된다
    And tags_ko에 한국어 번역 태그가 포함된다

  Scenario: 태그 수 제한
    Given VisionService 결과에 30개의 objects가 감지되었다
    When TagGenerator.generate_tags를 호출한다
    Then 반환된 태그 수가 20개 이하이다

  Scenario: 메타데이터 기반 태그
    Given EXIF 정보에 DateTimeOriginal이 "2026:01:10"이다
    And 파일 확장자가 "jpg"이다
    When TagGenerator.generate_tags를 호출한다
    Then tags_en에 "2026", "January", "jpg"가 포함된다
```

### 4.2 태그 번역

```gherkin
Feature: 태그 번역
  영어 태그를 한국어로 번역한다.

  Scenario: 기본 태그 번역
    Given 영어 태그 목록 ["person", "car", "outdoor"]가 있다
    When TagGenerator.translate_tags를 호출한다
    Then 한국어 태그 ["사람", "자동차", "야외"]가 반환된다

  Scenario: 번역 불가 태그 처리
    Given 번역 사전에 없는 영어 태그 "specific_object"가 있다
    When TagGenerator.translate_tags를 호출한다
    Then 원본 영어 태그가 그대로 반환된다
```

---

## 5. 카테고리 레지스트리 테스트

### 5.1 기본 카테고리

```gherkin
Feature: 기본 카테고리 관리
  시스템 기본 카테고리를 제공한다.

  Scenario: 기본 카테고리 조회
    When CategoryRegistry.get_all_categories를 호출한다
    Then 8개의 기본 카테고리가 반환된다
    And "photo", "screenshot", "document", "artwork", "meme", "product", "video", "other"가 포함된다

  Scenario: 카테고리 상세 조회
    When CategoryRegistry.get_category("photo")를 호출한다
    Then name_ko가 "사진"이다
    And name_en이 "Photo"이다
    And sub_categories에 "portrait", "landscape", "macro", "aerial"이 포함된다
```

### 5.2 사용자 정의 카테고리

```gherkin
Feature: 사용자 정의 카테고리
  사용자가 커스텀 카테고리를 등록할 수 있다.

  Scenario: 사용자 정의 카테고리 등록
    Given 새로운 카테고리 "work_document"를 정의한다
    When CategoryRegistry.register_custom_category를 호출한다
    Then 카테고리가 등록된다
    And get_category("work_document")가 정상 반환된다

  Scenario: 유효하지 않은 카테고리 이름
    Given 카테고리 이름이 "invalid@name!"이다
    When CategoryRegistry.register_custom_category를 호출한다
    Then InvalidCategoryNameError가 발생한다
```

---

## 6. 정리 추천 테스트

### 6.1 정리 계획 생성

```gherkin
Feature: 정리 계획 생성
  분류 결과를 기반으로 파일 정리를 추천한다.

  Scenario: 스크린샷 정리 추천
    Given 파일이 "screenshot" 카테고리로 분류되었다
    And EXIF에 날짜 정보가 있다
    When OrganizationPlanner.create_plan을 호출한다
    Then action이 "move"이다
    And target_path가 "~/Screenshots/{year}/{month}/" 패턴이다
    And reason이 "Screenshot detected, organizing by date"를 포함한다

  Scenario: 사진 날짜별 정리 추천
    Given 파일이 "photo" 카테고리로 분류되었다
    And EXIF DateTimeOriginal이 "2026:01:10"이다
    When OrganizationPlanner.create_plan을 호출한다
    Then target_path가 "~/Photos/2026/01/" 패턴이다

  Scenario: 분류 없이 정리 추천 시도
    Given 파일에 분류 결과가 없다
    When OrganizationPlanner.create_plan을 호출한다
    Then OrganizationPlanError가 발생한다
```

---

## 7. 배치 처리 테스트

### 7.1 배치 분류

```gherkin
Feature: 배치 분류
  디렉토리 내 여러 파일을 동시에 분류한다.

  Scenario: 디렉토리 배치 분류
    Given 디렉토리에 10개의 이미지 파일이 있다
    When classify_directory를 호출한다
    Then BatchClassificationResult가 반환된다
    And total_files가 10이다
    And successful이 10이다
    And failed가 0이다
    And results 목록에 10개의 ClassificationResult가 있다

  Scenario: 배치 분류 중 오류 발생
    Given 디렉토리에 8개의 유효한 파일과 2개의 손상된 파일이 있다
    When classify_directory를 호출한다
    Then successful이 8이다
    And failed가 2이다
    And errors 목록에 2개의 오류가 있다
    And 유효한 8개 파일의 결과가 반환된다

  Scenario: 동시성 제한
    Given 디렉토리에 50개의 파일이 있다
    When classify_directory를 concurrency=10으로 호출한다
    Then 동시에 최대 10개의 파일만 처리된다
```

### 7.2 재귀 처리

```gherkin
  Scenario: 하위 디렉토리 포함 분류
    Given 디렉토리에 3개의 파일이 있다
    And 하위 디렉토리에 5개의 파일이 있다
    When classify_directory를 recursive=True로 호출한다
    Then total_files가 8이다

  Scenario: 하위 디렉토리 제외 분류
    Given 디렉토리에 3개의 파일이 있다
    And 하위 디렉토리에 5개의 파일이 있다
    When classify_directory를 recursive=False로 호출한다
    Then total_files가 3이다
```

---

## 8. 오류 처리 테스트

### 8.1 입력 검증

```gherkin
Feature: 입력 검증
  잘못된 입력에 대해 적절한 오류를 발생시킨다.

  Scenario: 존재하지 않는 파일
    Given 파일 경로가 존재하지 않는다
    When classify_file을 호출한다
    Then FileNotFoundError가 발생한다

  Scenario: 지원되지 않는 파일 형식
    Given 파일 확장자가 ".xyz"이다
    When classify_file을 호출한다
    Then UnsupportedFormatError가 발생한다
```

### 8.2 폴백 동작

```gherkin
Feature: 폴백 동작
  서비스 장애 시 대체 동작을 수행한다.

  Scenario: VisionService 장애 시 메타데이터 분류
    Given VisionService가 사용 불가 상태이다
    When classify_file을 호출한다
    Then 메타데이터 기반 분류 결과가 반환된다
    And classification.method가 "metadata"이다

  Scenario: Redis 장애 시 메모리 캐시 사용
    Given Redis 연결이 실패한다
    When classify_file을 호출한다
    Then MemoryCache가 사용된다
    And 분류가 정상적으로 완료된다

  Scenario: 예산 초과 시 캐시만 사용
    Given 일일 API 예산이 초과되었다
    And 캐시에 분류 결과가 없다
    When classify_file을 호출한다
    Then 메타데이터 기반 분류만 수행된다
    And VisionService API가 호출되지 않는다
```

---

## 9. 성능 테스트

### 9.1 응답 시간

```gherkin
Feature: 응답 시간 성능
  정의된 성능 목표를 충족한다.

  Scenario: 캐시 히트 응답 시간
    Given 캐시에 분류 결과가 존재한다
    When classify_file을 호출한다
    Then 응답 시간이 50ms 미만이다

  Scenario: 캐시 미스 응답 시간
    Given 캐시에 분류 결과가 없다
    And VisionService가 정상 동작한다
    When classify_file을 호출한다
    Then 응답 시간이 5초 미만이다

  Scenario: 배치 처리 시간
    Given 100개의 파일이 있다
    When classify_directory를 호출한다
    Then 총 처리 시간이 60초 미만이다
```

---

## 10. 검증 체크리스트

### 10.1 기능 검증

- [ ] 단일 파일 분류 동작 확인
- [ ] 캐시 히트/미스 동작 확인
- [ ] 8개 기본 카테고리 분류 동작 확인
- [ ] 사용자 정의 카테고리 등록/적용 확인
- [ ] 태그 생성 (영어/한국어) 확인
- [ ] 정리 추천 생성 확인
- [ ] 배치 분류 동작 확인
- [ ] 오류 발생 시 폴백 동작 확인

### 10.2 성능 검증

- [ ] 캐시 히트 응답 시간 < 50ms
- [ ] 캐시 미스 응답 시간 < 5초
- [ ] 배치 100개 처리 시간 < 60초
- [ ] 메모리 사용량 < 500MB

### 10.3 품질 검증

- [ ] 분류 정확도 > 80% (수동 검증)
- [ ] 태그 품질 검증 (수동 검증)
- [ ] 한국어 번역 품질 검증
- [ ] 테스트 커버리지 > 80%

---

## 11. Definition of Done

SPEC-CLASS-001은 다음 조건이 모두 충족되면 완료로 간주한다:

1. **코드 완성**: 모든 핵심 컴포넌트가 구현되었다
   - ClassificationService
   - ClassificationEngine
   - CategoryRegistry
   - TagGenerator
   - OrganizationPlanner
   - BatchClassifier

2. **테스트 통과**: 모든 인수 조건 시나리오가 통과한다
   - 단위 테스트 커버리지 > 80%
   - 통합 테스트 통과
   - 성능 테스트 목표 충족

3. **품질 기준 충족**:
   - 분류 정확도 > 80%
   - 태그 품질 검증 통과
   - 코드 리뷰 완료

4. **문서화 완료**:
   - API 문서 작성
   - 사용 예시 제공
   - 설정 가이드 제공

5. **의존성 검증**:
   - SPEC-VISION-001과 정상 연동
   - 캐시 시스템 정상 동작
   - 예외 처리 정상 동작
