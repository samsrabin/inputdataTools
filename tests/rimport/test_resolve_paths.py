"""
Tests for resolve_paths() function in rimport script.
"""

import os
import sys
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

# Import rimport module from file without .py extension
rimport_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "rimport",
)
loader = SourceFileLoader("rimport", rimport_path)
spec = importlib.util.spec_from_loader("rimport", loader)
if spec is None:
    raise ImportError(f"Could not create spec for rimport from {rimport_path}")
rimport = importlib.util.module_from_spec(spec)
sys.modules["rimport"] = rimport
loader.exec_module(rimport)


class TestResolvePaths:
    """Test suite for resolve_paths() function."""

    def test_single_relative_path(self, tmp_path):
        """Test resolving a single relative path."""
        root = tmp_path / "root"
        root.mkdir()

        result = rimport.resolve_paths(root, ["file1.nc"])

        assert len(result) == 1
        assert result[0] == (root / "file1.nc").resolve()

    def test_multiple_relative_paths(self, tmp_path):
        """Test resolving multiple relative paths."""
        root = tmp_path / "root"
        root.mkdir()

        relnames = ["file1.nc", "file2.nc", "file3.nc"]
        result = rimport.resolve_paths(root, relnames)

        assert len(result) == 3
        assert result[0] == (root / "file1.nc").resolve()
        assert result[1] == (root / "file2.nc").resolve()
        assert result[2] == (root / "file3.nc").resolve()

    def test_nested_relative_paths(self, tmp_path):
        """Test resolving nested relative paths."""
        root = tmp_path / "root"
        root.mkdir()

        relnames = ["dir1/file1.nc", "dir2/subdir/file2.nc"]
        result = rimport.resolve_paths(root, relnames)

        assert len(result) == 2
        assert result[0] == (root / "dir1" / "file1.nc").resolve()
        assert result[1] == (root / "dir2" / "subdir" / "file2.nc").resolve()

    def test_absolute_path(self, tmp_path):
        """Test that absolute paths are preserved."""
        root = tmp_path / "root"
        root.mkdir()

        abs_path = tmp_path / "other" / "file.nc"
        relnames = [str(abs_path)]

        result = rimport.resolve_paths(root, relnames)

        assert len(result) == 1
        assert result[0] == abs_path.resolve()

    def test_mixed_relative_and_absolute(self, tmp_path):
        """Test mixing relative and absolute paths."""
        root = tmp_path / "root"
        root.mkdir()

        abs_path = tmp_path / "other" / "file.nc"
        relnames = ["file1.nc", str(abs_path), "dir/file2.nc"]

        result = rimport.resolve_paths(root, relnames)

        assert len(result) == 3
        assert result[0] == (root / "file1.nc").resolve()
        assert result[1] == abs_path.resolve()
        assert result[2] == (root / "dir" / "file2.nc").resolve()

    def test_empty_list(self, tmp_path):
        """Test with empty list of names."""
        root = tmp_path / "root"
        root.mkdir()

        result = rimport.resolve_paths(root, [])

        assert len(result) == 0
        assert result == []

    def test_paths_with_spaces(self, tmp_path):
        """Test paths with spaces in names."""
        root = tmp_path / "root"
        root.mkdir()

        relnames = ["file with spaces.nc", "dir with spaces/file.nc"]
        result = rimport.resolve_paths(root, relnames)

        assert len(result) == 2
        assert result[0] == (root / "file with spaces.nc").resolve()
        assert result[1] == (root / "dir with spaces" / "file.nc").resolve()

    def test_paths_with_special_characters(self, tmp_path):
        """Test paths with special characters."""
        root = tmp_path / "root"
        root.mkdir()

        relnames = ["file-name_123.nc", "dir@test/file.nc"]
        result = rimport.resolve_paths(root, relnames)

        assert len(result) == 2
        assert result[0] == (root / "file-name_123.nc").resolve()
        assert result[1] == (root / "dir@test" / "file.nc").resolve()

    def test_returns_path_objects(self, tmp_path):
        """Test that result contains Path objects."""
        root = tmp_path / "root"
        root.mkdir()

        result = rimport.resolve_paths(root, ["file.nc"])

        assert len(result) == 1
        assert isinstance(result[0], Path)

    def test_resolves_dot_and_dotdot(self, tmp_path):
        """Test that . and .. are resolved."""
        root = tmp_path / "root"
        root.mkdir()

        relnames = ["./file1.nc", "dir/../file2.nc", "dir/./file3.nc"]
        result = rimport.resolve_paths(root, relnames)

        assert len(result) == 3
        assert result[0] == (root / "file1.nc").resolve()
        assert result[1] == (root / "file2.nc").resolve()
        assert result[2] == (root / "dir" / "file3.nc").resolve()
