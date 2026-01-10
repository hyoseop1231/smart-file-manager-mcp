# SPEC-ORG-001 인수 조건

## TAG 추적

- SPEC ID: SPEC-ORG-001
- 관련 SPEC: SPEC-INFRA-001, SPEC-CLASS-001

---

## 1. 핵심 인수 조건

### 1.1 안전성 검증 (REQ-U-001)

**Given** OrganizationPlan이 준비되어 있을 때
**When** execute_plan()이 호출되면
**Then** SafetyValidator.validate_plan()이 먼저 호출되어야 한다
**And** 검증 실패 시 SafetyValidationError가 발생해야 한다

```gherkin
Feature: 안전성 검증
  Scenario: 보호된 경로 접근 차단
    Given 대상 경로가 "/System/Library"인 OrganizationPlan
    When execute_plan()을 호출하면
    Then ProtectedPathError가 발생해야 한다
    And 파일 작업이 수행되지 않아야 한다

  Scenario: 디스크 공간 부족 감지
    Given 파일 크기가 10GB이고 남은 디스크 공간이 5GB일 때
    When execute_plan()을 호출하면
    Then InsufficientSpaceError가 발생해야 한다
    And 에러 메시지에 필요 공간과 가용 공간이 포함되어야 한다
```

### 1.2 dry-run 모드 (REQ-S-001, REQ-E-001)

**Given** 유효한 OrganizationPlan이 있을 때
**When** execute_plan(dry_run=True)이 호출되면
**Then** 실제 파일 작업이 수행되지 않아야 한다
**And** 예상되는 모든 충돌이 결과에 포함되어야 한다
**And** ValidationResult가 반환되어야 한다

```gherkin
Feature: Dry-run 모드
  Scenario: dry-run에서 충돌 감지
    Given 대상 경로에 이미 파일이 존재할 때
    And OrganizationPlan의 action이 "move"일 때
    When execute_plan(dry_run=True)을 호출하면
    Then ExecutionResult.dry_run이 True여야 한다
    And ValidationResult.conflicts에 충돌 정보가 포함되어야 한다
    And 원본 파일이 이동되지 않아야 한다
```

### 1.3 파일 이동 실행 (REQ-E-006)

**Given** action="move"인 OrganizationPlan이 있을 때
**When** execute_plan()이 호출되면
**Then** 파일이 대상 경로로 이동되어야 한다
**And** TransactionManager에 원본 경로가 기록되어야 한다
**And** 원본 위치에 파일이 없어야 한다

```gherkin
Feature: 파일 이동
  Scenario: 성공적인 파일 이동
    Given "/source/image.jpg" 파일이 존재할 때
    And action="move", target="/target/organized/image.jpg"인 Plan
    When execute_plan()을 호출하면
    Then "/target/organized/image.jpg"에 파일이 존재해야 한다
    And "/source/image.jpg"에 파일이 없어야 한다
    And ExecutionResult.success가 True여야 한다
    And ExecutionResult.transaction_id가 유효한 UUID여야 한다

  Scenario: 대상 디렉토리 자동 생성
    Given 대상 디렉토리가 존재하지 않을 때
    When execute_plan()을 호출하면
    Then 대상 디렉토리가 자동으로 생성되어야 한다
    And 파일이 정상적으로 이동되어야 한다
```

### 1.4 충돌 해결 (REQ-E-002, REQ-S-003)

**Given** 대상 경로에 동일 이름의 파일이 존재할 때
**When** execute_plan(conflict_strategy=ConflictStrategy.RENAME_SUFFIX)이 호출되면
**Then** 파일명에 접미사(_1, _2 등)가 추가되어야 한다
**And** 기존 파일이 보존되어야 한다

```gherkin
Feature: 충돌 해결
  Scenario: skip 전략
    Given 대상 경로에 "image.jpg"가 이미 존재할 때
    When execute_plan(conflict_strategy=SKIP)을 호출하면
    Then ExecutionResult.success가 False여야 한다
    And 원본 파일이 이동되지 않아야 한다
    And 기존 파일이 보존되어야 한다

  Scenario: rename_suffix 전략
    Given 대상 경로에 "image.jpg"가 이미 존재할 때
    When execute_plan(conflict_strategy=RENAME_SUFFIX)을 호출하면
    Then "image_1.jpg"로 저장되어야 한다
    And ExecutionResult.target_path가 "image_1.jpg"를 가리켜야 한다

  Scenario: overwrite 전략
    Given 대상 경로에 "image.jpg"가 이미 존재할 때
    When execute_plan(conflict_strategy=OVERWRITE)을 호출하면
    Then 기존 파일이 덮어쓰기되어야 한다
    And 덮어쓰기된 파일의 내용이 원본과 동일해야 한다
```

### 1.5 롤백 기능 (REQ-U-003, REQ-E-011)

**Given** 완료된 트랜잭션이 있을 때
**When** rollback(transaction_id)이 호출되면
**Then** 모든 작업이 역순으로 취소되어야 한다
**And** 파일들이 원래 위치로 복원되어야 한다

```gherkin
Feature: 트랜잭션 롤백
  Scenario: 단일 이동 작업 롤백
    Given "/source/image.jpg"가 "/target/image.jpg"로 이동된 트랜잭션
    When rollback(transaction_id)을 호출하면
    Then "/source/image.jpg"가 복원되어야 한다
    And "/target/image.jpg"가 없어야 한다
    And RollbackResult.success가 True여야 한다

  Scenario: 배치 작업 롤백
    Given 10개 파일이 이동된 트랜잭션
    When rollback(transaction_id)을 호출하면
    Then 10개 파일 모두 원래 위치로 복원되어야 한다
    And RollbackResult.restored_files가 10이어야 한다

  Scenario: 부분 롤백 실패 처리
    Given 복원 중 일부 파일의 원본 위치가 변경된 경우
    When rollback(transaction_id)을 호출하면
    Then 가능한 파일들은 복원되어야 한다
    And RollbackResult.failed_restorations에 실패 목록이 포함되어야 한다
```

### 1.6 배치 처리 (REQ-E-003, REQ-S-006)

**Given** 여러 개의 OrganizationPlan이 포함된 BatchOrganizationPlan이 있을 때
**When** execute_batch()가 호출되면
**Then** 모든 파일이 병렬로 처리되어야 한다
**And** 개별 오류가 전체 작업을 중단시키지 않아야 한다

```gherkin
Feature: 배치 처리
  Scenario: 개별 오류 시 계속 처리
    Given 10개 파일 중 3번째 파일에 권한 오류가 있을 때
    When execute_batch(rollback_on_error=False)을 호출하면
    Then 나머지 9개 파일은 정상 처리되어야 한다
    And BatchExecutionResult.failed가 1이어야 한다
    And BatchExecutionResult.successful이 9이어야 한다

  Scenario: rollback_on_error 옵션
    Given 10개 파일 중 3번째 파일에 오류가 있을 때
    When execute_batch(rollback_on_error=True)을 호출하면
    Then 1-2번 파일 작업이 롤백되어야 한다
    And BatchExecutionResult.successful이 0이어야 한다

  Scenario: 동시성 제한
    Given 100개 파일의 배치 작업
    When execute_batch(concurrency=5)를 호출하면
    Then 동시에 5개 이하의 파일만 처리되어야 한다
```

### 1.7 휴지통 삭제 (REQ-E-009, REQ-N-001)

**Given** action="delete"인 OrganizationPlan이 있을 때
**When** execute_plan()이 호출되면
**Then** 파일이 영구 삭제되지 않고 휴지통으로 이동되어야 한다
**And** 메타데이터(원본 경로, 삭제 시간)가 함께 저장되어야 한다

```gherkin
Feature: 안전한 삭제
  Scenario: 휴지통으로 이동
    Given "/path/to/unwanted.jpg" 파일
    And action="delete"인 Plan
    When execute_plan()을 호출하면
    Then "~/.smart_file_manager/trash/{date}/" 아래에 파일이 이동되어야 한다
    And metadata.json에 원본 경로가 기록되어야 한다
    And 30일 후 자동 삭제 예정 시간이 기록되어야 한다
```

---

## 2. 보안 관련 인수 조건

### 2.1 보호된 경로 차단 (REQ-N-002)

```gherkin
Feature: 보호된 경로 차단
  Scenario Outline: 시스템 디렉토리 접근 차단
    Given 대상 경로가 "<protected_path>"인 Plan
    When execute_plan()을 호출하면
    Then ProtectedPathError가 발생해야 한다

    Examples:
      | protected_path        |
      | /                     |
      | /System               |
      | /usr/bin              |
      | /etc/passwd           |
      | ~/.ssh/id_rsa         |
```

### 2.2 숨김 파일 처리 (REQ-N-003)

```gherkin
Feature: 숨김 파일 보호
  Scenario: 숨김 파일 기본 제외
    Given ".hidden_file"이라는 숨김 파일
    And 기본 설정의 OrganizationPlan
    When execute_plan()을 호출하면
    Then 숨김 파일이 이동되지 않아야 한다
    And 경고 메시지가 로그에 기록되어야 한다

  Scenario: 명시적 숨김 파일 처리
    Given ".hidden_file"이라는 숨김 파일
    And include_hidden=True 옵션의 OrganizationPlan
    When execute_plan()을 호출하면
    Then 숨김 파일이 정상적으로 처리되어야 한다
```

---

## 3. 진행 상황 추적 인수 조건

### 3.1 진행률 콜백 (REQ-E-005, REQ-O-001)

```gherkin
Feature: 진행 상황 추적
  Scenario: 배치 처리 진행률 콜백
    Given 100개 파일의 배치 작업
    And progress_callback이 등록되어 있을 때
    When execute_batch()를 호출하면
    Then 매 파일 완료 시 progress_callback이 호출되어야 한다
    And Progress.percentage가 0%에서 100%까지 증가해야 한다
    And Progress.current_file에 현재 처리 중인 파일이 표시되어야 한다

  Scenario: ETA 계산
    Given 50개 파일이 처리 완료되고 50개가 남은 상태
    And 평균 처리 시간이 100ms일 때
    When get_progress()를 호출하면
    Then Progress.eta가 약 5초로 계산되어야 한다
```

---

## 4. 에지 케이스 인수 조건

### 4.1 특수 파일 처리

```gherkin
Feature: 특수 파일 처리
  Scenario: 0 byte 파일 경고
    Given 크기가 0 byte인 파일
    When execute_plan()을 호출하면
    Then 경고가 로그에 기록되어야 한다
    And 작업은 정상적으로 진행되어야 한다

  Scenario: 심볼릭 링크 처리
    Given 심볼릭 링크 파일
    When execute_plan()을 호출하면
    Then 링크 자체만 이동되어야 한다
    And 링크 대상 파일은 영향받지 않아야 한다

  Scenario: 매우 긴 파일명
    Given 255자 길이의 파일명
    When rename_suffix 전략으로 충돌 해결 시
    Then 파일명이 최대 길이를 초과하지 않아야 한다
    And 접미사가 정상적으로 추가되어야 한다
```

### 4.2 동시성 문제

```gherkin
Feature: 동시성 안전
  Scenario: 동일 파일 중복 실행 방지
    Given 동일 파일에 대한 두 개의 execute_plan() 호출
    When 동시에 실행되면
    Then 두 번째 호출은 대기하거나 거부되어야 한다
    And 파일 손상이 발생하지 않아야 한다

  Scenario: 크래시 복구
    Given 실행 중 애플리케이션이 중단된 트랜잭션
    When 애플리케이션이 재시작되면
    Then recover_from_crash()가 미완료 트랜잭션을 감지해야 한다
    And 사용자에게 복구 옵션을 제공해야 한다
```

---

## 5. 성능 인수 조건

```gherkin
Feature: 성능 요구사항
  Scenario: 단일 파일 이동 성능
    Given 10MB 크기의 파일
    When execute_plan(action="move")을 호출하면
    Then 1초 이내에 완료되어야 한다

  Scenario: dry-run 성능
    Given 1000개 파일의 배치 작업
    When execute_batch(dry_run=True)를 호출하면
    Then 10초 이내에 완료되어야 한다

  Scenario: 배치 처리 성능
    Given 100개 파일의 배치 작업
    When execute_batch()를 호출하면
    Then 30초 이내에 완료되어야 한다
```

---

## 6. Definition of Done

- [ ] 모든 EARS 요구사항이 구현됨
- [ ] 모든 Gherkin 시나리오에 대한 테스트 작성 및 통과
- [ ] 단위 테스트 커버리지 85% 이상
- [ ] SafetyValidator가 모든 보호 경로를 차단함
- [ ] TransactionManager 롤백이 정상 동작함
- [ ] dry-run 모드에서 실제 파일 작업이 발생하지 않음
- [ ] 배치 처리 시 동시성 제한이 적용됨
- [ ] 휴지통에 삭제된 파일과 메타데이터가 저장됨
- [ ] 진행 상황 콜백이 정상 호출됨
- [ ] SPEC-CLASS-001의 OrganizationPlan과 정상 연동됨
- [ ] mypy 타입 체크 통과
- [ ] ruff 린트 체크 통과
- [ ] API 문서화 완료
