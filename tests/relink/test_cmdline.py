"""
Tests for relink.py script as called from command line
"""

import os
import sys
import tempfile
import shutil
import logging
import subprocess
from unittest.mock import patch

import pytest

# Add parent directory to path to import relink module
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
# pylint: disable=wrong-import-position
import relink  # noqa: E402


@pytest.fixture(scope="function", autouse=True)
def configure_logging():
    """Configure logging to output to stdout for all tests."""
    # Configure logging before each test
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stdout,
        force=True,  # Force reconfiguration
    )
    yield
    # Clean up logging handlers after each test
    logging.getLogger().handlers.clear()


@pytest.fixture(scope="function", name="mock_default_dirs")
def fixture_mock_default_dirs():
    """Mock the default directories to use temporary directories."""
    source_dir = tempfile.mkdtemp(prefix="test_default_source_")
    target_dir = tempfile.mkdtemp(prefix="test_default_target_")

    with patch.object(relink, "DEFAULT_SOURCE_ROOT", source_dir):
        with patch.object(relink, "DEFAULT_TARGET_ROOT", target_dir):
            yield source_dir, target_dir

    # Cleanup
    shutil.rmtree(source_dir, ignore_errors=True)
    shutil.rmtree(target_dir, ignore_errors=True)


@pytest.fixture(scope="function", name="temp_dirs")
def fixture_temp_dirs():
    """Create temporary source and target directories for testing."""
    source_dir = tempfile.mkdtemp(prefix="test_source_")
    target_dir = tempfile.mkdtemp(prefix="test_target_")

    yield source_dir, target_dir

    # Cleanup
    shutil.rmtree(source_dir, ignore_errors=True)
    shutil.rmtree(target_dir, ignore_errors=True)


class TestCommandLineExecution:
    """Test suite for command-line execution of relink.py."""

    @pytest.fixture
    def mock_dirs(self, tmp_path):
        """Create temporary directories and files for command-line testing."""
        source_dir = tmp_path / "source"
        target_dir = tmp_path / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        # Create a test file
        source_file = source_dir / "test_file.txt"
        target_file = target_dir / "test_file.txt"
        source_file.write_text("source content")
        target_file.write_text("target content")

        return source_dir, target_dir, source_file, target_file

    def test_command_line_execution_dry_run(self, mock_dirs):
        """Test executing relink.py from command line with --dry-run flag."""
        source_dir, target_dir, source_file, _ = mock_dirs

        # Get the path to relink.py
        relink_script = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "relink.py",
        )

        # Build the command
        command = [
            sys.executable,
            relink_script,
            "--source-root",
            str(source_dir),
            "--target-root",
            str(target_dir),
            "--dry-run",
        ]

        # Execute the command
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        # Verify the command executed successfully
        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"

        # Verify dry-run messages in output
        assert "DRY RUN MODE" in result.stdout
        assert "[DRY RUN] Would create symbolic link:" in result.stdout

        # Verify no actual changes were made
        assert source_file.is_file()
        assert not source_file.is_symlink()

    def test_command_line_execution_actual_run(self, mock_dirs):
        """Test executing relink.py from command line without dry-run."""
        source_dir, target_dir, source_file, target_file = mock_dirs

        # Get the path to relink.py
        relink_script = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "relink.py",
        )

        # Build the command
        command = [
            sys.executable,
            relink_script,
            "--source-root",
            str(source_dir),
            "--target-root",
            str(target_dir),
        ]

        # Execute the command
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        # Verify the command executed successfully
        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"

        # Verify the file was converted to a symlink
        assert source_file.is_symlink()
        assert os.readlink(str(source_file)) == str(target_file)

        # Verify success messages in output
        assert "Created symbolic link:" in result.stdout
