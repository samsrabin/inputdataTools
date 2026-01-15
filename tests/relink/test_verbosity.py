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


@pytest.fixture(name="current_user")
def fixture_current_user():
    """Get the current user's username."""
    username = os.environ["USER"]
    return username


def test_quiet_mode_suppresses_info_messages(temp_dirs, caplog):
    """Test that quiet mode suppresses INFO level messages."""
    source_dir, target_dir = temp_dirs
    username = os.environ["USER"]

    # Create files
    source_file = os.path.join(source_dir, "test_file.txt")
    target_file = os.path.join(target_dir, "test_file.txt")

    with open(source_file, "w", encoding="utf-8") as f:
        f.write("source")
    with open(target_file, "w", encoding="utf-8") as f:
        f.write("target")

    # Create a symlink to test "Skipping symlink" message
    source_link = os.path.join(source_dir, "existing_link.txt")
    dummy_target = os.path.join(tempfile.gettempdir(), "somewhere")
    os.symlink(dummy_target, source_link)

    # Run the function with WARNING level (quiet mode)
    with caplog.at_level(logging.WARNING):
        relink.find_and_replace_owned_files(source_dir, target_dir, username)

    # Verify INFO messages are NOT in the log
    assert "Searching for files owned by" not in caplog.text
    assert "Skipping symlink:" not in caplog.text
    assert "Found owned file:" not in caplog.text
    assert "Deleted original file:" not in caplog.text
    assert "Created symbolic link:" not in caplog.text


def test_quiet_mode_shows_warnings(temp_dirs, caplog):
    """Test that quiet mode still shows WARNING level messages."""
    source_dir, target_dir = temp_dirs
    username = os.environ["USER"]

    # Create only source file (no corresponding target) to trigger warning
    source_file = os.path.join(source_dir, "orphan.txt")
    with open(source_file, "w", encoding="utf-8") as f:
        f.write("orphan content")

    # Run the function with WARNING level (quiet mode)
    with caplog.at_level(logging.WARNING):
        relink.find_and_replace_owned_files(source_dir, target_dir, username)

    # Verify WARNING message IS in the log
    assert "Warning: Corresponding file not found" in caplog.text


def test_quiet_mode_shows_errors(temp_dirs, caplog):
    """Test that quiet mode still shows ERROR level messages."""
    source_dir, target_dir = temp_dirs
    username = os.environ["USER"]

    # Test 1: Invalid username error
    invalid_username = "nonexistent_user_12345"
    with caplog.at_level(logging.WARNING):
        relink.find_and_replace_owned_files(source_dir, target_dir, invalid_username)
    assert "Error: User" in caplog.text
    assert "not found" in caplog.text

    # Clear the log for next test
    caplog.clear()

    # Test 2: Error deleting file
    source_file = os.path.join(source_dir, "test.txt")
    target_file = os.path.join(target_dir, "test.txt")

    with open(source_file, "w", encoding="utf-8") as f:
        f.write("source")
    with open(target_file, "w", encoding="utf-8") as f:
        f.write("target")

    def mock_rename(src, dst):
        raise OSError("Simulated rename error")

    with patch("os.rename", side_effect=mock_rename):
        with caplog.at_level(logging.WARNING):
            relink.find_and_replace_owned_files(source_dir, target_dir, username)
        assert "Error deleting file" in caplog.text

    # Clear the log for next test
    caplog.clear()

    # Test 3: Error creating symlink
    source_file2 = os.path.join(source_dir, "test2.txt")
    target_file2 = os.path.join(target_dir, "test2.txt")

    with open(source_file2, "w", encoding="utf-8") as f:
        f.write("source2")
    with open(target_file2, "w", encoding="utf-8") as f:
        f.write("target2")

    def mock_symlink(src, dst):
        raise OSError("Simulated symlink error")

    with patch("os.symlink", side_effect=mock_symlink):
        with caplog.at_level(logging.WARNING):
            relink.find_and_replace_owned_files(source_dir, target_dir, username)
        assert "Error creating symlink" in caplog.text
