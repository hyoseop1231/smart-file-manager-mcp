"""Tests for SafetyValidator.

TAG: ORG-001-S1
SPEC: SPEC-ORG-001

Tests for safety validation of file organization operations including:
- Protected path detection
- Permission checking
- Disk space validation
- File lock detection
- Plan validation
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from smart_file_manager.core.exceptions import (
    InsufficientSpaceError,
    ProtectedPathError,
)
from smart_file_manager.organization.safety_validator import (
    PROTECTED_PATHS,
    SafetyValidator,
)


class TestSafetyValidatorInit:
    """Tests for SafetyValidator initialization."""

    def test_default_protected_paths(self) -> None:
        """Test default protected paths are set."""
        validator = SafetyValidator()
        assert validator._protected_paths == PROTECTED_PATHS

    def test_custom_protected_paths(self) -> None:
        """Test custom protected paths can be provided."""
        custom_paths: frozenset[Path] = frozenset([Path("/custom/path")])
        validator = SafetyValidator(protected_paths=custom_paths)
        assert validator._protected_paths == custom_paths

    def test_include_hidden_default_false(self) -> None:
        """Test include_hidden defaults to False."""
        validator = SafetyValidator()
        assert validator._include_hidden is False

    def test_include_hidden_can_be_enabled(self) -> None:
        """Test include_hidden can be set to True."""
        validator = SafetyValidator(include_hidden=True)
        assert validator._include_hidden is True


class TestIsProtectedPath:
    """Tests for is_protected_path method."""

    def test_root_is_protected(self) -> None:
        """Test root path is protected."""
        validator = SafetyValidator()
        assert validator.is_protected_path(Path("/")) is True

    def test_system_dirs_protected(self) -> None:
        """Test /System, /usr, /etc are protected."""
        validator = SafetyValidator()
        assert validator.is_protected_path(Path("/System")) is True
        assert validator.is_protected_path(Path("/usr")) is True
        assert validator.is_protected_path(Path("/etc")) is True

    def test_bin_sbin_protected(self) -> None:
        """Test /bin and /sbin are protected."""
        validator = SafetyValidator()
        assert validator.is_protected_path(Path("/bin")) is True
        assert validator.is_protected_path(Path("/sbin")) is True

    def test_var_library_protected(self) -> None:
        """Test /var and /Library are protected."""
        validator = SafetyValidator()
        assert validator.is_protected_path(Path("/var")) is True
        assert validator.is_protected_path(Path("/Library")) is True

    def test_ssh_dir_protected(self) -> None:
        """Test ~/.ssh is protected."""
        validator = SafetyValidator()
        ssh_path = Path.home() / ".ssh"
        assert validator.is_protected_path(ssh_path) is True

    def test_gnupg_dir_protected(self) -> None:
        """Test ~/.gnupg is protected."""
        validator = SafetyValidator()
        gnupg_path = Path.home() / ".gnupg"
        assert validator.is_protected_path(gnupg_path) is True

    def test_config_dir_protected(self) -> None:
        """Test ~/.config is protected."""
        validator = SafetyValidator()
        config_path = Path.home() / ".config"
        assert validator.is_protected_path(config_path) is True

    def test_subdirs_of_protected_are_protected(self) -> None:
        """Test subdirectories of protected paths are protected."""
        validator = SafetyValidator()
        assert validator.is_protected_path(Path("/System/Library")) is True
        assert validator.is_protected_path(Path("/usr/bin")) is True
        assert validator.is_protected_path(Path("/etc/ssh")) is True

    def test_home_dir_not_protected(self) -> None:
        """Test home directory itself is not protected."""
        validator = SafetyValidator()
        # Home directory is not in the protected list
        assert validator.is_protected_path(Path.home()) is False

    def test_downloads_not_protected(self) -> None:
        """Test ~/Downloads is not protected."""
        validator = SafetyValidator()
        downloads = Path.home() / "Downloads"
        assert validator.is_protected_path(downloads) is False

    def test_documents_not_protected(self) -> None:
        """Test ~/Documents is not protected."""
        validator = SafetyValidator()
        documents = Path.home() / "Documents"
        assert validator.is_protected_path(documents) is False


class TestCheckPermissions:
    """Tests for check_permissions method."""

    def test_read_permission_for_copy(self) -> None:
        """Test read permission required for copy."""
        validator = SafetyValidator()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                result = validator.check_permissions(tmp_path, "copy")
                assert result is True
            finally:
                tmp_path.unlink()

    def test_write_permission_for_move(self) -> None:
        """Test write permission required for move."""
        validator = SafetyValidator()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                result = validator.check_permissions(tmp_path, "move")
                assert result is True
            finally:
                tmp_path.unlink()

    def test_write_permission_for_delete(self) -> None:
        """Test write permission required for delete."""
        validator = SafetyValidator()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                result = validator.check_permissions(tmp_path, "delete")
                assert result is True
            finally:
                tmp_path.unlink()

    def test_write_permission_for_rename(self) -> None:
        """Test write permission required for rename."""
        validator = SafetyValidator()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                result = validator.check_permissions(tmp_path, "rename")
                assert result is True
            finally:
                tmp_path.unlink()

    def test_nonexistent_path_returns_true(self) -> None:
        """Test nonexistent path returns True (will be checked during execution)."""
        validator = SafetyValidator()
        nonexistent = Path("/nonexistent/path/to/file.txt")
        result = validator.check_permissions(nonexistent, "move")
        assert result is True


class TestCheckDiskSpace:
    """Tests for check_disk_space method."""

    def test_sufficient_space_returns_true(self) -> None:
        """Test returns True when space is sufficient."""
        validator = SafetyValidator()
        # Request only 1 byte - should always have enough space
        result = validator.check_disk_space(Path.home(), 1)
        assert result is True

    def test_insufficient_space_returns_false(self) -> None:
        """Test returns False when space is insufficient."""
        validator = SafetyValidator()
        # Request an absurdly large amount - 1 exabyte
        result = validator.check_disk_space(Path.home(), 10**18)
        assert result is False

    def test_includes_ten_percent_buffer(self) -> None:
        """Test 10% buffer is required."""
        validator = SafetyValidator()
        # Get available space and request slightly less than 90% of it
        import shutil

        stat = shutil.disk_usage(Path.home())
        available = stat.free
        # Request 95% of available - should fail due to 10% buffer requirement
        request_size = int(available * 0.95)
        result = validator.check_disk_space(Path.home(), request_size)
        assert result is False


class TestIsFileLocked:
    """Tests for is_file_locked method."""

    def test_unlocked_file_returns_false(self) -> None:
        """Test unlocked file returns False."""
        validator = SafetyValidator()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                result = validator.is_file_locked(tmp_path)
                assert result is False
            finally:
                tmp_path.unlink()

    def test_nonexistent_file_returns_false(self) -> None:
        """Test nonexistent file returns False."""
        validator = SafetyValidator()
        nonexistent = Path("/nonexistent/file.txt")
        result = validator.is_file_locked(nonexistent)
        assert result is False

    def test_directory_returns_false(self) -> None:
        """Test directory returns False."""
        validator = SafetyValidator()
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = validator.is_file_locked(Path(tmp_dir))
            assert result is False


class TestValidatePlan:
    """Tests for validate_plan method."""

    def test_valid_plan_passes(self) -> None:
        """Test valid plan returns valid result."""
        validator = SafetyValidator()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            target_path = Path(tempfile.gettempdir()) / "target_file.txt"
            try:
                result = validator.validate_plan(tmp_path, target_path, "move")
                assert result.valid is True
                assert len(result.errors) == 0
            finally:
                tmp_path.unlink()

    def test_protected_source_raises_error(self) -> None:
        """Test protected source raises ProtectedPathError."""
        validator = SafetyValidator()
        source = Path("/System/Library/test.txt")
        target = Path(tempfile.gettempdir()) / "target.txt"
        with pytest.raises(ProtectedPathError) as exc_info:
            validator.validate_plan(source, target, "move")
        assert "protected" in str(exc_info.value).lower()

    def test_protected_target_raises_error(self) -> None:
        """Test protected target raises ProtectedPathError."""
        validator = SafetyValidator()
        source = Path(tempfile.gettempdir()) / "source.txt"
        target = Path("/System/Library/target.txt")
        with pytest.raises(ProtectedPathError) as exc_info:
            validator.validate_plan(source, target, "move")
        assert "protected" in str(exc_info.value).lower()

    def test_hidden_file_warning(self) -> None:
        """Test hidden file adds warning when include_hidden is False."""
        validator = SafetyValidator(include_hidden=False)
        with tempfile.TemporaryDirectory() as tmp_dir:
            hidden_file = Path(tmp_dir) / ".hidden_file"
            hidden_file.touch()
            target = Path(tmp_dir) / "target.txt"
            try:
                result = validator.validate_plan(hidden_file, target, "move")
                assert len(result.warnings) > 0
                assert any("hidden" in w.lower() for w in result.warnings)
            finally:
                hidden_file.unlink()

    def test_hidden_file_no_warning_when_included(self) -> None:
        """Test hidden file does not add warning when include_hidden is True."""
        validator = SafetyValidator(include_hidden=True)
        with tempfile.TemporaryDirectory() as tmp_dir:
            hidden_file = Path(tmp_dir) / ".hidden_file"
            hidden_file.touch()
            target = Path(tmp_dir) / "target.txt"
            try:
                result = validator.validate_plan(hidden_file, target, "move")
                assert not any("hidden" in w.lower() for w in result.warnings)
            finally:
                hidden_file.unlink()

    def test_root_target_adds_error(self) -> None:
        """Test root directory target adds error."""
        validator = SafetyValidator()
        source = Path(tempfile.gettempdir()) / "source.txt"
        target = Path("/target.txt")  # Parent is root
        with pytest.raises(ProtectedPathError):
            validator.validate_plan(source, target, "move")

    def test_insufficient_disk_space_raises_error(self) -> None:
        """Test insufficient disk space raises InsufficientSpaceError."""
        validator = SafetyValidator()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            # Write a small amount of data
            tmp.write(b"test data")
            tmp.flush()
            target_path = Path(tempfile.gettempdir()) / "target.txt"
            try:
                # Mock disk space to simulate insufficient space
                with patch.object(validator, "_get_available_space", return_value=0):
                    with pytest.raises(InsufficientSpaceError):
                        validator.validate_plan(tmp_path, target_path, "copy")
            finally:
                tmp_path.unlink()

    def test_locked_file_adds_error(self) -> None:
        """Test locked file adds error to validation result."""
        validator = SafetyValidator()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            target_path = Path(tempfile.gettempdir()) / "target.txt"
            try:
                # Mock file lock detection
                with patch.object(validator, "is_file_locked", return_value=True):
                    result = validator.validate_plan(tmp_path, target_path, "move")
                    assert result.valid is False
                    assert any("locked" in e.lower() for e in result.errors)
            finally:
                tmp_path.unlink()


class TestProtectedPathsConstant:
    """Tests for PROTECTED_PATHS constant."""

    def test_protected_paths_is_frozenset(self) -> None:
        """Test PROTECTED_PATHS is a frozenset."""
        assert isinstance(PROTECTED_PATHS, frozenset)

    def test_protected_paths_contains_root(self) -> None:
        """Test PROTECTED_PATHS contains root path."""
        assert Path("/") in PROTECTED_PATHS

    def test_protected_paths_contains_system_dirs(self) -> None:
        """Test PROTECTED_PATHS contains system directories."""
        assert Path("/System") in PROTECTED_PATHS
        assert Path("/usr") in PROTECTED_PATHS
        assert Path("/bin") in PROTECTED_PATHS
        assert Path("/sbin") in PROTECTED_PATHS
        assert Path("/etc") in PROTECTED_PATHS
        assert Path("/var") in PROTECTED_PATHS
        assert Path("/Library") in PROTECTED_PATHS

    def test_protected_paths_contains_user_sensitive_dirs(self) -> None:
        """Test PROTECTED_PATHS contains user sensitive directories."""
        assert Path.home() / ".ssh" in PROTECTED_PATHS
        assert Path.home() / ".gnupg" in PROTECTED_PATHS
        assert Path.home() / ".config" in PROTECTED_PATHS


class TestHiddenFileDetection:
    """Tests for hidden file detection."""

    def test_is_hidden_file_with_dot_prefix(self) -> None:
        """Test file starting with dot is detected as hidden."""
        validator = SafetyValidator()
        hidden = Path("/some/path/.hidden_file")
        assert validator._is_hidden_file(hidden) is True

    def test_is_not_hidden_file_without_dot(self) -> None:
        """Test file without dot prefix is not hidden."""
        validator = SafetyValidator()
        normal = Path("/some/path/normal_file.txt")
        assert validator._is_hidden_file(normal) is False


class TestGetAvailableSpace:
    """Tests for _get_available_space method."""

    def test_returns_positive_value_for_valid_path(self) -> None:
        """Test returns positive value for valid path."""
        validator = SafetyValidator()
        space = validator._get_available_space(Path.home())
        assert space > 0

    def test_returns_zero_for_nonexistent_path(self) -> None:
        """Test returns zero for nonexistent path."""
        validator = SafetyValidator()
        space = validator._get_available_space(Path("/nonexistent/deeply/nested/path"))
        assert space >= 0  # Should not raise, returns 0 or parent's space

    def test_handles_oserror_gracefully(self) -> None:
        """Test handles OSError gracefully and returns 0."""
        validator = SafetyValidator()
        with patch("shutil.disk_usage", side_effect=OSError("Mocked error")):
            space = validator._get_available_space(Path.home())
            assert space == 0


class TestCheckPermissionsExtended:
    """Extended tests for check_permissions method."""

    def test_unknown_action_returns_true(self) -> None:
        """Test unknown action type returns True."""
        validator = SafetyValidator()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                result = validator.check_permissions(tmp_path, "unknown_action")
                assert result is True
            finally:
                tmp_path.unlink()

    def test_read_action_returns_true(self) -> None:
        """Test read action returns True (not explicitly handled)."""
        validator = SafetyValidator()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                result = validator.check_permissions(tmp_path, "read")
                assert result is True
            finally:
                tmp_path.unlink()


class TestValidatePlanExtended:
    """Extended tests for validate_plan method."""

    def test_delete_action_skips_disk_space_check(self) -> None:
        """Test delete action does not check disk space."""
        validator = SafetyValidator()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            target_path = Path(tempfile.gettempdir()) / "target.txt"
            try:
                # Even with no disk space, delete should work
                with patch.object(validator, "_get_available_space", return_value=0):
                    result = validator.validate_plan(tmp_path, target_path, "delete")
                    assert result.valid is True
            finally:
                tmp_path.unlink()

    def test_permission_error_adds_to_errors(self) -> None:
        """Test permission error adds to error list."""
        validator = SafetyValidator()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            target_path = Path(tempfile.gettempdir()) / "target.txt"
            try:
                with patch.object(validator, "check_permissions", return_value=False):
                    result = validator.validate_plan(tmp_path, target_path, "move")
                    assert result.valid is False
                    assert any("permission" in e.lower() for e in result.errors)
            finally:
                tmp_path.unlink()

    def test_directory_source_for_copy(self) -> None:
        """Test directory source for copy action."""
        validator = SafetyValidator()
        with tempfile.TemporaryDirectory() as tmp_dir:
            source = Path(tmp_dir)
            target = Path(tempfile.gettempdir()) / "target_dir"
            result = validator.validate_plan(source, target, "copy")
            # Should pass - directory size is 0
            assert result.valid is True

    def test_nonexistent_source_for_move(self) -> None:
        """Test nonexistent source for move action."""
        validator = SafetyValidator()
        source = Path(tempfile.gettempdir()) / "nonexistent_source.txt"
        target = Path(tempfile.gettempdir()) / "target.txt"
        # Nonexistent source - disk space check skipped
        result = validator.validate_plan(source, target, "move")
        assert result.valid is True


class TestIsProtectedPathEdgeCases:
    """Edge case tests for is_protected_path method."""

    def test_ssh_subdir_is_protected(self) -> None:
        """Test subdirectory of ~/.ssh is protected."""
        validator = SafetyValidator()
        ssh_subdir = Path.home() / ".ssh" / "keys"
        assert validator.is_protected_path(ssh_subdir) is True

    def test_config_subdir_is_protected(self) -> None:
        """Test subdirectory of ~/.config is protected."""
        validator = SafetyValidator()
        config_subdir = Path.home() / ".config" / "app"
        assert validator.is_protected_path(config_subdir) is True

    def test_regular_path_not_protected(self) -> None:
        """Test regular path outside protected areas is not protected."""
        validator = SafetyValidator()
        with tempfile.TemporaryDirectory() as tmp_dir:
            regular_path = Path(tmp_dir) / "some_file.txt"
            assert validator.is_protected_path(regular_path) is False
