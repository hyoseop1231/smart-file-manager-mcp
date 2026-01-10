# SPEC-ORG-001 구현 계획

## TAG 추적

- SPEC ID: SPEC-ORG-001
- 관련 SPEC: SPEC-INFRA-001, SPEC-CLASS-001

---

## 1. 구현 마일스톤

### Primary Goal (우선순위 높음)

핵심 파일 정리 실행 인프라 구축

#### 1.1 데이터 모델 정의

**파일**: `src/smart_file_manager/organization/models.py`

구현 항목:
- [ ] ConflictStrategy Enum 정의 (skip, overwrite, rename_suffix, rename_timestamp, ask_user)
- [ ] TransactionEntry dataclass 정의
- [ ] ExecutionResult dataclass 정의
- [ ] BatchExecutionResult dataclass 정의
- [ ] ValidationResult dataclass 정의
- [ ] Progress dataclass 정의
- [ ] RollbackResult dataclass 정의
- [ ] Conflict dataclass 정의
- [ ] OrganizationAction dataclass 정의

#### 1.2 예외 클래스 추가

**파일**: `src/smart_file_manager/core/exceptions.py`

구현 항목:
- [ ] OrganizationError 기본 예외 클래스
- [ ] SafetyValidationError
- [ ] ConflictResolutionError
- [ ] TransactionError
- [ ] RollbackError
- [ ] InsufficientSpaceError
- [ ] ProtectedPathError
- [ ] FileLockedError

#### 1.3 SafetyValidator 구현

**파일**: `src/smart_file_manager/organization/safety_validator.py`

구현 항목:
- [ ] PROTECTED_PATHS 상수 정의
- [ ] validate_plan() 메서드
- [ ] check_permissions() 메서드
- [ ] check_disk_space() 메서드
- [ ] is_protected_path() 메서드
- [ ] is_file_locked() 메서드
- [ ] validate_target_path() 메서드

#### 1.4 TransactionManager 구현

**파일**: `src/smart_file_manager/organization/transaction_manager.py`

구현 항목:
- [ ] 트랜잭션 로그 저장 경로 설정 (~/.smart_file_manager/transactions/)
- [ ] begin() 메서드 (UUID 기반 트랜잭션 ID 생성)
- [ ] record() 메서드 (JSON 로그 기록)
- [ ] commit() 메서드
- [ ] rollback() 메서드
- [ ] get_transaction() 메서드
- [ ] recover_from_crash() 메서드

### Secondary Goal (우선순위 중간)

파일 작업 실행 엔진 구축

#### 2.1 ConflictResolver 구현

**파일**: `src/smart_file_manager/organization/conflict_resolver.py`

구현 항목:
- [ ] resolve() 메서드
- [ ] generate_unique_name() 메서드 (suffix, timestamp 전략)
- [ ] detect_conflicts() 메서드 (사전 충돌 감지)
- [ ] 각 전략별 이름 생성 로직

#### 2.2 OrganizationExecutor 구현

**파일**: `src/smart_file_manager/organization/executor.py`

구현 항목:
- [ ] execute_action() 메서드 (액션 라우팅)
- [ ] execute_move() 메서드 (shutil.move 래핑)
- [ ] execute_copy() 메서드 (shutil.copy2 래핑)
- [ ] execute_rename() 메서드 (Path.rename 래핑)
- [ ] execute_delete() 메서드 (휴지통 이동)
- [ ] execute_group() 메서드 (다중 파일 이동)
- [ ] 휴지통 디렉토리 구조 관리
- [ ] 메타데이터 JSON 생성

#### 2.3 ProgressTracker 구현

**파일**: `src/smart_file_manager/organization/progress_tracker.py`

구현 항목:
- [ ] start() 메서드
- [ ] update() 메서드
- [ ] get_progress() 메서드
- [ ] register_callback() 메서드
- [ ] calculate_eta() 메서드 (이동 평균 기반)
- [ ] 콜백 호출 로직

### Final Goal (우선순위 낮음)

통합 서비스 및 고급 기능

#### 3.1 OrganizationService 구현

**파일**: `src/smart_file_manager/organization/organization_service.py`

구현 항목:
- [ ] 의존성 주입 설정 (Executor, Validator, Resolver, TransactionManager, ProgressTracker)
- [ ] execute_plan() 메서드
  - [ ] dry-run 모드 지원
  - [ ] 실행 전 SafetyValidator 호출
  - [ ] ConflictResolver 적용
  - [ ] TransactionManager 기록
- [ ] execute_batch() 메서드
  - [ ] 동시성 제한 (asyncio.Semaphore)
  - [ ] rollback_on_error 옵션
  - [ ] 개별 오류 시 건너뛰기
- [ ] rollback() 메서드
- [ ] get_transaction_history() 메서드
- [ ] cleanup_trash() 메서드

#### 3.2 패키지 초기화

**파일**: `src/smart_file_manager/organization/__init__.py`

구현 항목:
- [ ] 모든 공개 클래스/함수 export
- [ ] 버전 정보

---

## 2. 기술적 접근 방식

### 2.1 비동기 파일 I/O

```python
# aiofiles 사용 예시
import aiofiles
import aiofiles.os

async def async_copy(source: Path, target: Path) -> None:
    async with aiofiles.open(source, 'rb') as src:
        async with aiofiles.open(target, 'wb') as dst:
            while chunk := await src.read(8192):
                await dst.write(chunk)
```

### 2.2 동시성 제어

```python
# asyncio.Semaphore로 동시성 제한
semaphore = asyncio.Semaphore(5)

async def execute_with_limit(action):
    async with semaphore:
        return await executor.execute_action(action)

# 배치 실행
results = await asyncio.gather(
    *[execute_with_limit(action) for action in actions],
    return_exceptions=True
)
```

### 2.3 트랜잭션 로그 형식

```json
{
    "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
    "started_at": "2026-01-10T10:00:00Z",
    "status": "committed",
    "entries": [
        {
            "action": "move",
            "source_path": "/path/to/source.jpg",
            "target_path": "/path/to/organized/2026/01/source.jpg",
            "backup_path": null,
            "timestamp": "2026-01-10T10:00:01Z",
            "success": true,
            "error_message": null
        }
    ],
    "committed_at": "2026-01-10T10:00:05Z"
}
```

### 2.4 휴지통 메타데이터 형식

```json
{
    "original_path": "/path/to/original/file.jpg",
    "deleted_at": "2026-01-10T10:00:00Z",
    "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
    "file_size": 1048576,
    "content_hash": "sha256:abcd1234...",
    "restore_deadline": "2026-02-09T10:00:00Z"
}
```

---

## 3. 의존성

### 3.1 필수 패키지

```toml
[project.dependencies]
aiofiles = ">=23.0.0"
python-dateutil = ">=2.8.0"
```

### 3.2 내부 의존성

- `smart_file_manager.core.config.Settings`
- `smart_file_manager.core.exceptions`
- `smart_file_manager.classification.organization_planner.OrganizationPlan`
- `smart_file_manager.classification.organization_planner.BatchOrganizationPlan`

---

## 4. 아키텍처 설계 방향

### 4.1 계층 구조

```
OrganizationService (Facade)
    ├── SafetyValidator (검증)
    ├── ConflictResolver (충돌 해결)
    ├── OrganizationExecutor (실행)
    │   └── TransactionManager (트랜잭션)
    └── ProgressTracker (진행 추적)
```

### 4.2 의존성 주입 패턴

```python
class OrganizationService:
    def __init__(
        self,
        executor: OrganizationExecutor | None = None,
        validator: SafetyValidator | None = None,
        resolver: ConflictResolver | None = None,
        transaction_manager: TransactionManager | None = None,
        progress_tracker: ProgressTracker | None = None,
    ) -> None:
        self._executor = executor or OrganizationExecutor()
        self._validator = validator or SafetyValidator()
        self._resolver = resolver or ConflictResolver()
        self._transaction_manager = transaction_manager or TransactionManager()
        self._progress_tracker = progress_tracker or ProgressTracker()
```

### 4.3 오류 처리 전략

```python
# 배치 처리 시 개별 오류 격리
async def execute_batch(self, batch_plan, rollback_on_error=False):
    results = []
    for plan in batch_plan.plans:
        try:
            result = await self.execute_plan(plan)
            results.append(result)
        except OrganizationError as e:
            if rollback_on_error:
                await self._transaction_manager.rollback(transaction_id)
                raise
            results.append(ExecutionResult(
                success=False,
                error=e,
                ...
            ))
    return BatchExecutionResult(results=results, ...)
```

---

## 5. 리스크 대응 계획

### 5.1 데이터 손실 방지

- 모든 작업 전 트랜잭션 시작
- 작업별 원본 경로 기록
- 커밋 전 오류 발생 시 자동 롤백
- 휴지통 30일 보관

### 5.2 동시성 문제 방지

- 파일별 asyncio.Lock 관리
- 트랜잭션 ID 기반 작업 격리
- Semaphore로 동시 작업 수 제한

### 5.3 크래시 복구

- 미완료 트랜잭션 검색 기능
- 애플리케이션 시작 시 자동 복구 옵션
- 트랜잭션 로그 영속 저장

---

## 6. 테스트 전략

### 6.1 단위 테스트 우선순위

1. SafetyValidator.is_protected_path() - 보안 핵심
2. TransactionManager.rollback() - 데이터 보호 핵심
3. ConflictResolver.resolve() - 사용자 경험 핵심
4. OrganizationExecutor 각 액션 메서드

### 6.2 통합 테스트

- 전체 execute_plan() 흐름 테스트
- 배치 처리 동시성 테스트
- 롤백 시나리오 테스트
- 크래시 복구 테스트

### 6.3 테스트 환경

```python
@pytest.fixture
def temp_workspace(tmp_path):
    """테스트용 임시 작업 공간."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    # 테스트 파일 생성
    (workspace / "test.jpg").write_bytes(b"fake image data")
    return workspace
```

---

## 7. SPEC-CLASS-001과의 통합 예시

```python
# 전체 워크플로우 예시
from smart_file_manager.services.classification_service import ClassificationService
from smart_file_manager.organization.organization_service import OrganizationService
from smart_file_manager.organization.models import ConflictStrategy

# 1. 분류 수행
classification_service = ClassificationService()
classification_result = await classification_service.classify_file(
    Path("/path/to/image.jpg"),
    include_organization_plan=True,
)

# 2. 정리 계획 확인
plan = classification_result.organization_plan
print(f"추천: {plan.action} -> {plan.target_path}")
print(f"이유: {plan.reason}")

# 3. dry-run으로 검증
organization_service = OrganizationService()
dry_result = await organization_service.execute_plan(
    plan=plan,
    dry_run=True,
)

if dry_result.success:
    # 4. 실제 실행
    result = await organization_service.execute_plan(
        plan=plan,
        dry_run=False,
        conflict_strategy=ConflictStrategy.RENAME_SUFFIX,
    )
    print(f"실행 결과: {result.success}")
    print(f"트랜잭션 ID: {result.transaction_id}")
```
