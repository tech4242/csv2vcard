"""Tests for vCard export functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from csv2vcard.exceptions import ExportError
from csv2vcard.export_vcard import ensure_export_dir, export_vcard
from csv2vcard.models import VCardOutput, VCardVersion


class TestExportVCard:
    """Test suite for vCard export."""

    def test_export_vcard_creates_file(self, temp_dir: Path) -> None:
        """Test that export_vcard creates a file."""
        vcard = {
            "filename": "test.vcf",
            "output": "BEGIN:VCARD\nVERSION:3.0\nEND:VCARD\n",
            "name": "Test Contact",
        }

        result = export_vcard(vcard, output_dir=temp_dir)

        assert result.exists()
        assert result.name == "test.vcf"
        assert result.read_text() == vcard["output"]

    def test_export_vcard_returns_path(self, temp_dir: Path) -> None:
        """Test that export_vcard returns the file path."""
        vcard = {
            "filename": "test.vcf",
            "output": "content",
            "name": "Test",
        }

        result = export_vcard(vcard, output_dir=temp_dir)

        assert isinstance(result, Path)
        assert result.parent == temp_dir

    def test_export_vcard_accepts_vcard_output(self, temp_dir: Path) -> None:
        """Test that export_vcard accepts VCardOutput objects."""
        vcard = VCardOutput(
            filename="typed_test.vcf",
            output="BEGIN:VCARD\nVERSION:4.0\nEND:VCARD\n",
            name="Test Contact",
            version=VCardVersion.V4_0,
        )

        result = export_vcard(vcard, output_dir=temp_dir)

        assert result.exists()
        assert result.name == "typed_test.vcf"

    def test_export_vcard_prevents_path_traversal(self, temp_dir: Path) -> None:
        """Test that path traversal in filename is blocked."""
        vcard = {
            "filename": "../../../etc/malicious.vcf",
            "output": "malicious content",
            "name": "Attacker",
        }

        with pytest.raises(ExportError, match="path traversal"):
            export_vcard(vcard, output_dir=temp_dir)

    def test_export_vcard_creates_directory(self, temp_dir: Path) -> None:
        """Test that output directory is created if it doesn't exist."""
        output_dir = temp_dir / "new_subdir"
        vcard = {
            "filename": "test.vcf",
            "output": "content",
            "name": "Test",
        }

        result = export_vcard(vcard, output_dir=output_dir)

        assert output_dir.exists()
        assert result.exists()

    def test_export_vcard_default_directory(
        self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test default export directory behavior."""
        monkeypatch.chdir(temp_dir)

        vcard = {
            "filename": "test.vcf",
            "output": "BEGIN:VCARD\nEND:VCARD\n",
            "name": "Test",
        }

        result = export_vcard(vcard)

        assert result.parent.name == "export"
        assert (temp_dir / "export" / "test.vcf").exists()

    def test_export_vcard_overwrites_existing(self, temp_dir: Path) -> None:
        """Test that existing files are overwritten."""
        existing = temp_dir / "existing.vcf"
        existing.write_text("old content")

        vcard = {
            "filename": "existing.vcf",
            "output": "new content",
            "name": "Test",
        }

        export_vcard(vcard, output_dir=temp_dir)

        assert existing.read_text() == "new content"

    def test_export_vcard_utf8_encoding(self, temp_dir: Path) -> None:
        """Test that files are written with UTF-8 encoding."""
        vcard = {
            "filename": "unicode.vcf",
            "output": "BEGIN:VCARD\nFN:Hans Muller\nEND:VCARD\n",
            "name": "Hans Muller",
        }

        result = export_vcard(vcard, output_dir=temp_dir)
        content = result.read_text(encoding="utf-8")

        assert "Hans Muller" in content


class TestEnsureExportDir:
    """Test export directory creation."""

    def test_creates_directory(self, temp_dir: Path) -> None:
        """Test that directory is created if it doesn't exist."""
        export_path = temp_dir / "new_export"

        result = ensure_export_dir(export_path)

        assert result.exists()
        assert result.is_dir()

    def test_creates_nested_directories(self, temp_dir: Path) -> None:
        """Test creation of nested directories."""
        export_path = temp_dir / "a" / "b" / "c"

        result = ensure_export_dir(export_path)

        assert result.exists()
        assert result.is_dir()

    def test_handles_existing_directory(self, temp_dir: Path) -> None:
        """Test that existing directory is handled gracefully."""
        export_path = temp_dir / "existing"
        export_path.mkdir()

        result = ensure_export_dir(export_path)

        assert result.exists()
        assert result == export_path

    def test_raises_on_file_conflict(self, temp_dir: Path) -> None:
        """Test that error is raised if path exists as file."""
        file_path = temp_dir / "not_a_dir"
        file_path.write_text("I am a file")

        with pytest.raises(ExportError):
            ensure_export_dir(file_path)

    def test_default_directory(
        self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test default directory creation."""
        monkeypatch.chdir(temp_dir)

        result = ensure_export_dir()

        assert result.name == "export"
        assert result.exists()

    def test_accepts_string_path(self, temp_dir: Path) -> None:
        """Test that ensure_export_dir accepts string paths."""
        export_path = str(temp_dir / "string_path")

        result = ensure_export_dir(export_path)

        assert result.exists()


class TestCheckExportDeprecation:
    """Test deprecated check_export function."""

    def test_check_export_warns(
        self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that check_export issues deprecation warning."""
        from csv2vcard.export_vcard import check_export

        monkeypatch.chdir(temp_dir)

        with pytest.warns(DeprecationWarning, match="deprecated"):
            check_export()

        assert (temp_dir / "export").exists()
