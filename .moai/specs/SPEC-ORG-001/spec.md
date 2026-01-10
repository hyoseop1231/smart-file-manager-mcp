---
id: SPEC-ORG-001
version: "1.0.0"
status: "completed"
created: "2026-01-10"
updated: "2026-01-10"
author: "Developer"
priority: "high"
lifecycle: "spec-anchored"
dependencies:
  - SPEC-INFRA-001
  - SPEC-CLASS-001
---

# SPEC-ORG-001: Phase 6 - 파일 정리 실행 서비스

## HISTORY

| 버전 | 날짜 | 작성자 | 변경사항 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-10 | Developer | 초기 SPEC 작성 |

---

## 1. 개요

### 1.1 목적

SPEC-CLASS-001에서 구현된 OrganizationPlanner가 생성한 정리 계획(OrganizationPlan)을 실제로 **실행**하는 서비스를 구현한다. 파일 이동, 복사, 이름 변경, 삭제 등의 작업을 안전하게 수행하며, 롤백 기능과 진행 상황 추적을 제공한다.

### 1.2 범위

**핵심 구현 범위:**
- OrganizationService: 메인 정리 실행 서비스
- OrganizationExecutor: 계획 실행 엔진
- SafetyValidator: 실행 전 안전성 검증
- ConflictResolver: 파일명 충돌 해결
- TransactionManager: 롤백 지원 트랜잭션 관리
- ProgressTracker: 배치 작업 진행 상황 추적

**제외 범위:**
- OrganizationPlan 생성 (SPEC-CLASS-001에서 구현 완료)
- 분류 로직 (SPEC-CLASS-001에서 구현 완료)
- Vision 분석 (SPEC-VISION-001에서 구현 완료)

### 1.3 SPEC 의존성

이 SPEC은 다음 선행 SPEC에 의존한다:

| SPEC ID | 컴포넌트 | 용도 |
|---------|----------|------|
| SPEC-INFRA-001 | Settings, CacheInterface, Exceptions | 인프라 기반 |
| SPEC-CLASS-001 | OrganizationPlanner, ClassificationResult, OrganizationPlan | 정리 계획 소스 |

### 1.4 관련 문서

- `REFACTORING_SPEC_v5.md`: 전체 리팩토링 명세
- `.moai/project/product.md`: 파일 정리 요구사항 (사용자 시나리오 참조)
- `.moai/project/tech.md`: 기술 스택 정보
- `.moai/project/structure.md`: 데이터 흐름 및 저장소 구조
- `.moai/specs/SPEC-CLASS-001/spec.md`: OrganizationPlan 정의

---

## 2. EARS 요구사항

### 2.1 Ubiquitous Requirements (시스템 전반 적용)

**[REQ-U-001]** 시스템은 **항상** 실행 전 SafetyValidator를 통해 모든 작업의 안전성을 검증해야 한다.

**[REQ-U-002]** 시스템은 **항상** 실행 결과를 구조화된 로그에 기록해야 한다.

**[REQ-U-003]** 시스템은 **항상** TransactionManager를 통해 롤백 가능한 상태를 유지해야 한다.

**[REQ-U-004]** 시스템은 **항상** 실행 결과에 성공/실패 여부와 상세 정보를 포함해야 한다.

**[REQ-U-005]** 시스템은 **항상** 원본 파일의 백업 경로를 트랜잭션에 기록해야 한다.

**[REQ-U-006]** 시스템은 **항상** 파일 작업 전 대상 디렉토리의 존재 여부를 확인하고 없으면 생성해야 한다.

**[REQ-U-007]** 시스템은 **항상** 파일 작업의 처리 시간(ms)을 결과에 포함해야 한다.

### 2.2 Event-Driven Requirements (이벤트 기반 동작)

**[REQ-E-001]** **WHEN** plan이 실행 요청되면 **THEN** 먼저 dry-run으로 유효성을 검증해야 한다.

**[REQ-E-002]** **WHEN** 파일명 충돌이 발생하면 **THEN** ConflictResolver 전략을 적용해야 한다.

**[REQ-E-003]** **WHEN** 배치 작업 중 개별 파일 오류가 발생하면 **THEN** 해당 파일만 건너뛰고 나머지 파일 작업을 계속해야 한다.

**[REQ-E-004]** **WHEN** 트랜잭션 커밋 전 오류가 발생하면 **THEN** 전체 작업을 롤백해야 한다.

**[REQ-E-005]** **WHEN** 진행 상황이 업데이트되면 **THEN** ProgressTracker를 통해 콜백을 호출해야 한다.

**[REQ-E-006]** **WHEN** move 액션이 요청되면 **THEN** 파일을 대상 경로로 이동하고 원본 위치를 트랜잭션에 기록해야 한다.

**[REQ-E-007]** **WHEN** copy 액션이 요청되면 **THEN** 파일을 대상 경로로 복사하고 복사본 경로를 트랜잭션에 기록해야 한다.

**[REQ-E-008]** **WHEN** rename 액션이 요청되면 **THEN** 파일명을 변경하고 원본 이름을 트랜잭션에 기록해야 한다.

**[REQ-E-009]** **WHEN** delete 액션이 요청되면 **THEN** 휴지통으로 이동하고 휴지통 경로를 트랜잭션에 기록해야 한다.

**[REQ-E-010]** **WHEN** group 액션이 요청되면 **THEN** 유사 파일들을 동일 디렉토리로 이동해야 한다.

**[REQ-E-011]** **WHEN** rollback이 요청되면 **THEN** 트랜잭션 로그를 역순으로 실행하여 원래 상태로 복원해야 한다.

**[REQ-E-012]** **WHEN** dry-run 모드에서 충돌이 감지되면 **THEN** 예상 충돌 목록을 결과에 포함해야 한다.

### 2.3 State-Driven Requirements (상태 기반 동작)

**[REQ-S-001]** **IF** dry-run 모드이면 **THEN** 실제 파일 작업을 수행하지 않고 검증 결과만 반환해야 한다.

**[REQ-S-002]** **IF** 디스크 공간이 부족하면 **THEN** 작업을 중단하고 InsufficientSpaceError를 발생시켜야 한다.

**[REQ-S-003]** **IF** 대상 파일이 이미 존재하면 **THEN** ConflictResolver 전략에 따라 처리해야 한다.

**[REQ-S-004]** **IF** 파일이 읽기 전용이면 **THEN** PermissionError를 발생시키고 해당 파일을 건너뛰어야 한다.

**[REQ-S-005]** **IF** 트랜잭션이 활성 상태이면 **THEN** 새 트랜잭션을 시작하지 않고 기존 트랜잭션에 작업을 추가해야 한다.

**[REQ-S-006]** **IF** 배치 처리 중인 상태이면 **THEN** 동시성 제한(최대 5개)을 적용해야 한다.

**[REQ-S-007]** **IF** rollback_on_error가 True이면 **THEN** 첫 번째 오류 발생 시 전체 배치를 롤백해야 한다.

### 2.4 Unwanted Behavior Requirements (금지 동작)

**[REQ-N-001]** 시스템은 **사용자 확인 없이** 파일을 영구 삭제**하지 않아야** 한다.

**[REQ-N-002]** 시스템은 **시스템 디렉토리**(/System, /usr, /bin 등)에 대한 작업을 **허용하지 않아야** 한다.

**[REQ-N-003]** 시스템은 **숨김 파일**(. 으로 시작)을 기본적으로 **이동/삭제하지 않아야** 한다.

**[REQ-N-004]** 시스템은 **실행 중인 파일**이나 **잠긴 파일**을 **이동하지 않아야** 한다.

**[REQ-N-005]** 시스템은 **동일 파일에 대한 중복 실행**을 **허용하지 않아야** 한다 (Race Condition 방지).

**[REQ-N-006]** 시스템은 **0 byte 파일**을 대상으로 이동/복사를 수행하면 **경고를 발생**시켜야 한다.

**[REQ-N-007]** 시스템은 **심볼릭 링크**를 따라가서 원본을 수정**하지 않아야** 한다.

**[REQ-N-008]** 시스템은 **루트 디렉토리**(/)에 직접 파일을 생성**하지 않아야** 한다.

### 2.5 Optional Requirements (선택적 기능)

**[REQ-O-001]** **가능하면** 작업 진행률을 실시간으로 UI에 전달해야 한다.

**[REQ-O-002]** **가능하면** 작업 완료 예상 시간(ETA)을 계산하여 제공해야 한다.

**[REQ-O-003]** **가능하면** 실행 취소(Undo) 기능을 제공해야 한다.

**[REQ-O-004]** **가능하면** 일시 중지/재개 기능을 제공해야 한다.

**[REQ-O-005]** **가능하면** 파일 이동 전 미리보기(Preview) 기능을 제공해야 한다.

**[REQ-O-006]** **가능하면** 배치 작업의 부분 롤백을 지원해야 한다.

---

## 3. 기술 명세

### 3.1 지원 액션 유형

| 액션 | 설명 | 롤백 방법 |
|------|------|-----------|
| `move` | 파일을 대상 경로로 이동 | 원본 위치로 재이동 |
| `copy` | 파일을 대상 경로로 복사 | 복사본 삭제 |
| `rename` | 파일명 변경 | 원본 이름으로 복원 |
| `delete` | 휴지통으로 이동 (안전 삭제) | 휴지통에서 복원 |
| `group` | 유사 파일을 동일 디렉토리로 이동 | 원본 위치로 재이동 |

### 3.2 충돌 해결 전략

| 전략 | 설명 | 사용 케이스 |
|------|------|-------------|
| `skip` | 충돌 시 건너뛰기 | 기본값, 안전 우선 |
| `overwrite` | 기존 파일 덮어쓰기 | 명시적 사용자 요청 시 |
| `rename_suffix` | 파일명에 접미사 추가 (예: `_1`, `_2`) | 중복 허용 필요 시 |
| `rename_timestamp` | 파일명에 타임스탬프 추가 | 버전 관리 필요 시 |
| `ask_user` | 사용자에게 선택 요청 | 대화형 모드 |

### 3.3 휴지통 구조

```
~/.smart_file_manager/
└── trash/
    └── {date}/
        └── {original_filename}_{timestamp}_{hash}/
            ├── file.ext           # 원본 파일
            └── metadata.json      # 원본 경로, 삭제 시간 등
```

### 3.4 트랜잭션 로그 구조

```python
@dataclass
class TransactionEntry:
    """트랜잭션 로그 엔트리."""
    action: str                # move, copy, rename, delete
    source_path: Path          # 원본 경로
    target_path: Path          # 대상 경로
    backup_path: Path | None   # 백업 경로 (롤백용)
    timestamp: datetime        # 실행 시간
    success: bool              # 성공 여부
    error_message: str | None  # 오류 메시지
```

### 3.5 디렉토리 구조

```
src/
└── smart_file_manager/
    ├── organization/
    │   ├── __init__.py
    │   ├── organization_service.py     # [NEW] 메인 서비스
    │   ├── executor.py                  # [NEW] OrganizationExecutor
    │   ├── safety_validator.py          # [NEW] SafetyValidator
    │   ├── conflict_resolver.py         # [NEW] ConflictResolver
    │   ├── transaction_manager.py       # [NEW] TransactionManager
    │   ├── progress_tracker.py          # [NEW] ProgressTracker
    │   └── models.py                    # [NEW] 데이터 모델
    │
    └── core/
        └── exceptions.py               # OrganizationError 클래스 추가
```

### 3.6 예외 클래스 추가

```python
class OrganizationError(SmartFileManagerError):
    """정리 실행 관련 기본 예외."""

class SafetyValidationError(OrganizationError):
    """안전성 검증 실패."""

class ConflictResolutionError(OrganizationError):
    """충돌 해결 실패."""

class TransactionError(OrganizationError):
    """트랜잭션 처리 실패."""

class RollbackError(OrganizationError):
    """롤백 실패."""

class InsufficientSpaceError(OrganizationError):
    """디스크 공간 부족."""

class ProtectedPathError(OrganizationError):
    """보호된 경로 접근 시도."""

class FileLockedError(OrganizationError):
    """파일이 잠겨있음."""
```

---

## 4. 인터페이스 설계

### 4.1 OrganizationService 클래스

```python
class OrganizationService:
    """통합 정리 실행 서비스.

    OrganizationPlan을 받아 실제 파일 작업을 수행한다.

    Attributes:
        executor: OrganizationExecutor 인스턴스
        safety_validator: SafetyValidator 인스턴스
        conflict_resolver: ConflictResolver 인스턴스
        transaction_manager: TransactionManager 인스턴스
        progress_tracker: ProgressTracker 인스턴스
    """

    async def execute_plan(
        self,
        plan: OrganizationPlan,
        *,
        dry_run: bool = False,
        conflict_strategy: ConflictStrategy = ConflictStrategy.SKIP,
        progress_callback: ProgressCallback | None = None,
    ) -> ExecutionResult:
        """단일 정리 계획 실행."""

    async def execute_batch(
        self,
        batch_plan: BatchOrganizationPlan,
        *,
        dry_run: bool = False,
        conflict_strategy: ConflictStrategy = ConflictStrategy.SKIP,
        rollback_on_error: bool = False,
        concurrency: int = 5,
        progress_callback: ProgressCallback | None = None,
    ) -> BatchExecutionResult:
        """배치 정리 계획 실행."""

    async def rollback(
        self,
        transaction_id: str,
    ) -> RollbackResult:
        """트랜잭션 롤백."""

    async def get_transaction_history(
        self,
        limit: int = 100,
    ) -> list[TransactionSummary]:
        """트랜잭션 이력 조회."""

    async def cleanup_trash(
        self,
        older_than_days: int = 30,
    ) -> CleanupResult:
        """휴지통 정리."""
```

### 4.2 OrganizationExecutor 클래스

```python
class OrganizationExecutor:
    """정리 계획 실행 엔진.

    개별 액션을 실행하고 결과를 반환한다.
    """

    async def execute_action(
        self,
        action: OrganizationAction,
        *,
        dry_run: bool = False,
    ) -> ActionResult:
        """단일 액션 실행."""

    async def execute_move(
        self,
        source: Path,
        target: Path,
    ) -> ActionResult:
        """파일 이동."""

    async def execute_copy(
        self,
        source: Path,
        target: Path,
    ) -> ActionResult:
        """파일 복사."""

    async def execute_rename(
        self,
        source: Path,
        new_name: str,
    ) -> ActionResult:
        """파일명 변경."""

    async def execute_delete(
        self,
        source: Path,
    ) -> ActionResult:
        """파일 삭제 (휴지통으로 이동)."""

    async def execute_group(
        self,
        sources: list[Path],
        target_directory: Path,
    ) -> ActionResult:
        """파일 그룹화."""
```

### 4.3 SafetyValidator 클래스

```python
class SafetyValidator:
    """실행 전 안전성 검증.

    파일 권한, 경로 유효성, 디스크 공간 등을 검증한다.
    """

    def validate_plan(
        self,
        plan: OrganizationPlan,
    ) -> ValidationResult:
        """정리 계획 검증."""

    def check_permissions(
        self,
        path: Path,
        required_permissions: Permissions,
    ) -> bool:
        """파일 권한 확인."""

    def check_disk_space(
        self,
        target_path: Path,
        required_bytes: int,
    ) -> bool:
        """디스크 공간 확인."""

    def is_protected_path(
        self,
        path: Path,
    ) -> bool:
        """보호된 경로 여부 확인."""

    def is_file_locked(
        self,
        path: Path,
    ) -> bool:
        """파일 잠금 상태 확인."""

    def validate_target_path(
        self,
        target: Path,
    ) -> ValidationResult:
        """대상 경로 유효성 검증."""
```

### 4.4 ConflictResolver 클래스

```python
class ConflictResolver:
    """파일명 충돌 해결.

    다양한 전략으로 충돌을 해결한다.
    """

    def resolve(
        self,
        source: Path,
        target: Path,
        strategy: ConflictStrategy,
    ) -> ResolvedPath:
        """충돌 해결."""

    def generate_unique_name(
        self,
        base_path: Path,
        strategy: ConflictStrategy,
    ) -> Path:
        """고유 파일명 생성."""

    def detect_conflicts(
        self,
        plans: list[OrganizationPlan],
    ) -> list[Conflict]:
        """충돌 사전 감지."""
```

### 4.5 TransactionManager 클래스

```python
class TransactionManager:
    """롤백 지원 트랜잭션 관리.

    모든 파일 작업을 추적하고 롤백을 지원한다.
    """

    def begin(self) -> str:
        """새 트랜잭션 시작. 트랜잭션 ID 반환."""

    def record(
        self,
        transaction_id: str,
        entry: TransactionEntry,
    ) -> None:
        """작업 기록."""

    def commit(
        self,
        transaction_id: str,
    ) -> None:
        """트랜잭션 커밋."""

    def rollback(
        self,
        transaction_id: str,
    ) -> RollbackResult:
        """트랜잭션 롤백."""

    def get_transaction(
        self,
        transaction_id: str,
    ) -> Transaction:
        """트랜잭션 조회."""

    def recover_from_crash(self) -> list[Transaction]:
        """크래시 복구 (미완료 트랜잭션 검색)."""
```

### 4.6 ProgressTracker 클래스

```python
class ProgressTracker:
    """배치 작업 진행 상황 추적.

    진행률, ETA, 현재 파일 정보를 추적한다.
    """

    def start(
        self,
        total_files: int,
    ) -> None:
        """추적 시작."""

    def update(
        self,
        current_file: Path,
        status: FileStatus,
    ) -> None:
        """진행 상황 업데이트."""

    def get_progress(self) -> Progress:
        """현재 진행 상황 조회."""

    def register_callback(
        self,
        callback: ProgressCallback,
    ) -> None:
        """콜백 등록."""

    def calculate_eta(self) -> timedelta | None:
        """예상 완료 시간 계산."""
```

### 4.7 응답 데이터 구조

```python
@dataclass
class ExecutionResult:
    """단일 실행 결과."""
    success: bool
    action: str
    source_path: Path
    target_path: Path | None
    transaction_id: str
    processing_time_ms: float
    error: OrganizationError | None
    dry_run: bool

@dataclass
class BatchExecutionResult:
    """배치 실행 결과."""
    total_files: int
    successful: int
    failed: int
    skipped: int
    results: list[ExecutionResult]
    transaction_id: str
    total_processing_time_ms: float
    rollback_available: bool

@dataclass
class ValidationResult:
    """검증 결과."""
    valid: bool
    errors: list[str]
    warnings: list[str]
    conflicts: list[Conflict]

@dataclass
class Progress:
    """진행 상황."""
    current_file: Path
    current_index: int
    total_files: int
    percentage: float
    eta: timedelta | None
    status: str

@dataclass
class RollbackResult:
    """롤백 결과."""
    success: bool
    restored_files: int
    failed_restorations: list[Path]
    error: RollbackError | None

@dataclass
class Conflict:
    """충돌 정보."""
    source_path: Path
    target_path: Path
    conflict_type: str  # file_exists, name_collision
    suggested_resolution: ConflictStrategy
```

---

## 5. 제약사항

### 5.1 기술적 제약

- Python 3.11 이상 필수
- SPEC-CLASS-001 (OrganizationPlanner) 필수
- SPEC-INFRA-001 (Settings, CacheInterface, Exceptions) 필수
- aiofiles >= 23.0.0 권장 (비동기 파일 I/O)
- shutil (표준 라이브러리) 활용

### 5.2 성능 제약

| 항목 | 목표 |
|------|------|
| 단일 파일 이동/복사 시간 | < 1초 (10MB 이하) |
| dry-run 검증 시간 | < 100ms |
| 배치 처리 처리량 (100 파일) | < 30초 |
| 롤백 시간 (100 작업) | < 60초 |
| 트랜잭션 기록 시간 | < 10ms |
| 진행 상황 업데이트 간격 | 매 파일 또는 1초 |
| 최대 동시 파일 작업 수 | 5개 |

### 5.3 파일 크기 제약

| 항목 | 제한 |
|------|------|
| 단일 파일 이동/복사 최대 크기 | 4GB |
| 배치 작업 최대 파일 수 | 1000개 |
| 트랜잭션 로그 보관 기간 | 30일 |
| 휴지통 자동 정리 기간 | 30일 |

### 5.4 보호 경로 목록 (macOS/Linux)

```python
PROTECTED_PATHS = [
    "/",
    "/System",
    "/usr",
    "/bin",
    "/sbin",
    "/etc",
    "/var",
    "/private",
    "/Library",
    "/Applications",
    "~/.ssh",
    "~/.gnupg",
]
```

---

## 6. 추적성

### 6.1 선행/후속 SPEC

| 관계 | SPEC ID | 설명 |
|------|---------|------|
| 선행 | SPEC-INFRA-001 | 인프라 준비 (Settings, Cache, Exceptions) |
| 선행 | SPEC-CLASS-001 | 분류 서비스 (OrganizationPlanner, OrganizationPlan) |
| 후속 | SPEC-MCP-001 | MCP 서버 통합 (정리 실행 도구 노출) |
| 후속 | SPEC-UI-001 | Web UI 통합 (진행 상황 표시) |

### 6.2 TAG 추적

| TAG ID | 요구사항 | 테스트 케이스 |
|--------|----------|---------------|
| ORG-001-U001 | REQ-U-001 | test_safety_validator_called_before_execution |
| ORG-001-U002 | REQ-U-002 | test_execution_logged_to_structured_log |
| ORG-001-U003 | REQ-U-003 | test_transaction_manager_maintains_rollback_state |
| ORG-001-U006 | REQ-U-006 | test_target_directory_created_if_not_exists |
| ORG-001-E001 | REQ-E-001 | test_dry_run_before_execution |
| ORG-001-E002 | REQ-E-002 | test_conflict_resolver_applied_on_conflict |
| ORG-001-E003 | REQ-E-003 | test_batch_continues_on_individual_error |
| ORG-001-E004 | REQ-E-004 | test_rollback_on_commit_failure |
| ORG-001-E006 | REQ-E-006 | test_move_action_execution |
| ORG-001-E007 | REQ-E-007 | test_copy_action_execution |
| ORG-001-E009 | REQ-E-009 | test_delete_moves_to_trash |
| ORG-001-E011 | REQ-E-011 | test_rollback_restores_original_state |
| ORG-001-S001 | REQ-S-001 | test_dry_run_no_file_operations |
| ORG-001-S002 | REQ-S-002 | test_insufficient_space_error |
| ORG-001-S003 | REQ-S-003 | test_conflict_strategy_applied |
| ORG-001-N001 | REQ-N-001 | test_no_permanent_delete_without_confirmation |
| ORG-001-N002 | REQ-N-002 | test_protected_path_rejection |
| ORG-001-N003 | REQ-N-003 | test_hidden_files_excluded_by_default |
| ORG-001-N005 | REQ-N-005 | test_no_duplicate_execution |

### 6.3 SPEC-CLASS-001 연동 포인트

```python
# SPEC-CLASS-001에서 정의된 데이터 구조 사용
from smart_file_manager.classification.organization_planner import (
    OrganizationPlan,
    BatchOrganizationPlan,
)
from smart_file_manager.services.classification_service import (
    ClassificationResult,
)

# 연동 예시
classification_result: ClassificationResult = await classification_service.classify_file(file_path)
organization_plan: OrganizationPlan = classification_result.organization_plan

# OrganizationService로 실행
execution_result: ExecutionResult = await organization_service.execute_plan(
    plan=organization_plan,
    dry_run=False,
    conflict_strategy=ConflictStrategy.SKIP,
)
```

---

## 7. 리스크 분석

### 7.1 데이터 손실 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| 파일 이동 중 중단 | 낮음 | 높음 | 트랜잭션 로그 + 자동 롤백 |
| 휴지통 실수로 삭제 | 낮음 | 중간 | 휴지통 30일 보관 정책 |
| 충돌 덮어쓰기 | 중간 | 높음 | 기본값 skip + 사용자 확인 |

### 7.2 성능 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| 대용량 파일 처리 지연 | 중간 | 중간 | 청크 기반 복사 + 진행률 피드백 |
| 배치 처리 메모리 부족 | 낮음 | 중간 | 스트리밍 처리 + 동시성 제한 |
| 트랜잭션 로그 비대 | 낮음 | 낮음 | 30일 자동 정리 |

### 7.3 동시성 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| 동일 파일 동시 작업 | 중간 | 높음 | 파일 잠금 + Race Condition 방지 |
| 트랜잭션 충돌 | 낮음 | 중간 | 트랜잭션 ID 기반 격리 |

---

## 8. 용어 정의

| 용어 | 정의 |
|------|------|
| **OrganizationPlan** | SPEC-CLASS-001에서 정의된 파일 정리 계획 |
| **ExecutionResult** | 정리 계획 실행 결과 |
| **Transaction** | 롤백 가능한 파일 작업 단위 |
| **ConflictStrategy** | 파일명 충돌 시 해결 전략 |
| **dry-run** | 실제 파일 작업 없이 검증만 수행하는 모드 |
| **Rollback** | 트랜잭션 로그를 사용하여 원래 상태로 복원 |
| **ProgressCallback** | 진행 상황 업데이트 시 호출되는 콜백 함수 |
| **휴지통** | 안전 삭제를 위한 임시 저장 공간 |
