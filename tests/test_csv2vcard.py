"""Tests for main csv2vcard functionality."""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from csv2vcard.csv2vcard import csv2vcard, test_csv2vcard
from csv2vcard.models import VCardVersion


class TestCSV2VCard:
    """Test suite for main csv2vcard function."""

    def test_csv2vcard_creates_files(
        self, sample_csv: Path, temp_dir: Path
    ) -> None:
        """Test that csv2vcard creates vCard files."""
        output_dir = temp_dir / "output"

        files = csv2vcard(sample_csv, ",", output_dir=output_dir)

        assert len(files) == 2
        assert all(f.exists() for f in files)
        assert all(f.suffix == ".vcf" for f in files)

    def test_csv2vcard_returns_paths(
        self, sample_csv: Path, temp_dir: Path
    ) -> None:
        """Test that csv2vcard returns list of Path objects."""
        output_dir = temp_dir / "output"

        files = csv2vcard(sample_csv, ",", output_dir=output_dir)

        assert isinstance(files, list)
        assert all(isinstance(f, Path) for f in files)

    def test_csv2vcard_v4(
        self, sample_csv: Path, temp_dir: Path
    ) -> None:
        """Test creating vCard 4.0 files."""
        output_dir = temp_dir / "output"

        files = csv2vcard(
            sample_csv, ",",
            output_dir=output_dir,
            version=VCardVersion.V4_0,
        )

        # Check that files contain v4.0 format
        content = files[0].read_text()
        assert "VERSION:4.0" in content

    def test_csv2vcard_v3_default(
        self, sample_csv: Path, temp_dir: Path
    ) -> None:
        """Test that default version is 3.0."""
        output_dir = temp_dir / "output"

        files = csv2vcard(sample_csv, ",", output_dir=output_dir)

        content = files[0].read_text()
        assert "VERSION:3.0" in content

    def test_csv2vcard_with_semicolon_delimiter(
        self, semicolon_csv: Path, temp_dir: Path
    ) -> None:
        """Test csv2vcard with semicolon delimiter."""
        output_dir = temp_dir / "output"

        files = csv2vcard(semicolon_csv, ";", output_dir=output_dir)

        assert len(files) == 1

    def test_csv2vcard_deprecated_parameter(
        self, sample_csv: Path, temp_dir: Path
    ) -> None:
        """Test that deprecated 'csv_delimeter' parameter works with warning."""
        output_dir = temp_dir / "output"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            files = csv2vcard(
                sample_csv,
                csv_delimeter=",",  # Deprecated spelling
                output_dir=output_dir,
            )

            # Filter for our specific deprecation warning
            delimeter_warnings = [
                x for x in w
                if issubclass(x.category, DeprecationWarning)
                and "csv_delimeter" in str(x.message)
            ]
            assert len(delimeter_warnings) == 1
            assert "deprecated" in str(delimeter_warnings[0].message).lower()
            assert len(files) == 2

    def test_csv2vcard_returns_empty_for_nonexistent_file(
        self, temp_dir: Path
    ) -> None:
        """Test handling of nonexistent CSV file."""
        files = csv2vcard(
            temp_dir / "nonexistent.csv", ",",
            output_dir=temp_dir / "output",
        )

        assert files == []

    def test_csv2vcard_creates_output_directory(
        self, sample_csv: Path, temp_dir: Path
    ) -> None:
        """Test that output directory is created if it doesn't exist."""
        output_dir = temp_dir / "new_dir" / "nested"

        files = csv2vcard(sample_csv, ",", output_dir=output_dir)

        assert output_dir.exists()
        assert len(files) == 2

    def test_csv2vcard_accepts_path_object(
        self, sample_csv: Path, temp_dir: Path
    ) -> None:
        """Test that csv2vcard accepts Path objects."""
        output_dir = temp_dir / "output"

        files = csv2vcard(sample_csv, ",", output_dir=output_dir)

        assert len(files) == 2

    def test_csv2vcard_empty_csv(
        self, empty_csv: Path, temp_dir: Path
    ) -> None:
        """Test csv2vcard with empty CSV file."""
        output_dir = temp_dir / "output"

        files = csv2vcard(empty_csv, ",", output_dir=output_dir)

        assert files == []


class TestTestCSV2VCard:
    """Test the test_csv2vcard demo function."""

    def test_creates_forrest_gump_vcard(
        self, temp_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that test_csv2vcard creates the demo vCard."""
        test_csv2vcard(output_dir=temp_dir)

        # Check that file was created
        expected_file = temp_dir / "gump_forrest.vcf"
        assert expected_file.exists()

        # Check that vCard was printed
        captured = capsys.readouterr()
        assert "BEGIN:VCARD" in captured.out
        assert "Forrest" in captured.out

    def test_creates_v4_vcard(
        self, temp_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test test_csv2vcard with vCard 4.0."""
        test_csv2vcard(output_dir=temp_dir, version=VCardVersion.V4_0)

        expected_file = temp_dir / "gump_forrest.vcf"
        content = expected_file.read_text()
        assert "VERSION:4.0" in content

    def test_uses_default_directory(
        self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test test_csv2vcard uses default export directory."""
        monkeypatch.chdir(temp_dir)

        test_csv2vcard()

        expected_file = temp_dir / "export" / "gump_forrest.vcf"
        assert expected_file.exists()


class TestBackwardsCompatibility:
    """Test backwards compatibility with old API."""

    def test_direct_function_import(self, sample_csv: Path, temp_dir: Path) -> None:
        """Test that direct function import works (new API)."""
        # New, cleaner import pattern - function is directly accessible
        from csv2vcard import csv2vcard as convert_func

        files = convert_func(str(sample_csv), ",", output_dir=temp_dir)

        assert len(files) == 2

    def test_module_import_pattern(self, sample_csv: Path, temp_dir: Path) -> None:
        """Test that explicit module import still works."""
        # For users who prefer explicit module access
        from csv2vcard.csv2vcard import csv2vcard as csv2vcard_func

        files = csv2vcard_func(str(sample_csv), ",", output_dir=temp_dir)

        assert len(files) == 2

    def test_old_positional_args(self, sample_csv: Path, temp_dir: Path) -> None:
        """Test that old positional argument style works."""
        files = csv2vcard(sample_csv, ",", output_dir=temp_dir)

        assert len(files) == 2
