"""
Tests for relink.py script.
"""

import os
import sys
import tempfile
import shutil
import logging
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


@pytest.mark.parametrize(
    "use_timing, should_log_timing", [(True, True), (False, False)]
)
def test_timing_logging(tmp_path, caplog, use_timing, should_log_timing):
    """Test that timing message is logged only when --timing flag is used."""
    # Create real directories
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    target_dir.mkdir()

    # Create a file
    source_file = source_dir / "test_file.txt"
    target_file = target_dir / "test_file.txt"
    source_file.write_text("source")
    target_file.write_text("target")

    # Build argv with or without --timing flag
    test_argv = [
        "relink.py",
        "--source-root",
        str(source_dir),
        "--target-root",
        str(target_dir),
    ]
    if use_timing:
        test_argv.append("--timing")

    with patch("sys.argv", test_argv):
        with caplog.at_level(logging.INFO):
            # Call main() which includes the timing logic
            relink.main()

    # Verify timing message presence based on flag
    if should_log_timing:
        assert "Execution time:" in caplog.text
        assert "seconds" in caplog.text
    else:
        assert "Execution time:" not in caplog.text
