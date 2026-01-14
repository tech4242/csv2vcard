"""Tests for CLI functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

# Only run CLI tests if typer is available
typer = pytest.importorskip("typer")
from typer.testing import CliRunner  # noqa: E402

from csv2vcard.cli import app  # noqa: E402


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


class TestCLI:
    """Test suite for CLI commands."""

    def test_convert_command(
        self, runner: CliRunner, sample_csv: Path, temp_dir: Path
    ) -> None:
        """Test the convert command."""
        output_dir = temp_dir / "output"

        result = runner.invoke(
            app,
            ["convert", str(sample_csv), "-o", str(output_dir)],
        )

        assert result.exit_code == 0
        assert "Successfully created" in result.stdout
        assert "2" in result.stdout  # 2 files created

    def test_convert_with_delimiter(
        self, runner: CliRunner, semicolon_csv: Path, temp_dir: Path
    ) -> None:
        """Test convert command with custom delimiter."""
        output_dir = temp_dir / "output"

        result = runner.invoke(
            app,
            ["convert", str(semicolon_csv), "-d", ";", "-o", str(output_dir)],
        )

        assert result.exit_code == 0
        assert "Successfully created" in result.stdout

    def test_convert_vcard_4(
        self, runner: CliRunner, sample_csv: Path, temp_dir: Path
    ) -> None:
        """Test creating vCard 4.0 via CLI."""
        output_dir = temp_dir / "output"

        result = runner.invoke(
            app,
            ["convert", str(sample_csv), "-V", "4.0", "-o", str(output_dir)],
        )

        assert result.exit_code == 0

        # Verify content is v4.0
        vcf_files = list(output_dir.glob("*.vcf"))
        assert len(vcf_files) > 0
        content = vcf_files[0].read_text()
        assert "VERSION:4.0" in content

    def test_convert_invalid_version(
        self, runner: CliRunner, sample_csv: Path, temp_dir: Path
    ) -> None:
        """Test error handling for invalid vCard version."""
        result = runner.invoke(
            app,
            ["convert", str(sample_csv), "-V", "2.0", "-o", str(temp_dir)],
        )

        assert result.exit_code == 1
        assert "Invalid vCard version" in result.stdout

    def test_convert_nonexistent_file(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test error handling for nonexistent file."""
        result = runner.invoke(
            app,
            ["convert", str(temp_dir / "nonexistent.csv")],
        )

        assert result.exit_code != 0

    def test_convert_verbose(
        self, runner: CliRunner, sample_csv: Path, temp_dir: Path
    ) -> None:
        """Test verbose output."""
        output_dir = temp_dir / "output"

        result = runner.invoke(
            app,
            ["convert", str(sample_csv), "-v", "-o", str(output_dir)],
        )

        assert result.exit_code == 0

    def test_convert_lists_created_files(
        self, runner: CliRunner, sample_csv: Path, temp_dir: Path
    ) -> None:
        """Test that convert lists created files."""
        output_dir = temp_dir / "output"

        result = runner.invoke(
            app,
            ["convert", str(sample_csv), "-o", str(output_dir)],
        )

        assert result.exit_code == 0
        assert ".vcf" in result.stdout

    def test_test_command(
        self, runner: CliRunner, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test the test command."""
        monkeypatch.chdir(temp_dir)

        result = runner.invoke(app, ["test"])

        assert result.exit_code == 0
        assert "Test vCard created" in result.stdout
        assert (temp_dir / "export" / "gump_forrest.vcf").exists()

    def test_test_command_with_output_dir(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test the test command with custom output directory."""
        output_dir = temp_dir / "custom"

        result = runner.invoke(
            app,
            ["test", "-o", str(output_dir)],
        )

        assert result.exit_code == 0
        assert (output_dir / "gump_forrest.vcf").exists()

    def test_test_command_v4(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test the test command with vCard 4.0."""
        output_dir = temp_dir / "output"

        result = runner.invoke(
            app,
            ["test", "-V", "4.0", "-o", str(output_dir)],
        )

        assert result.exit_code == 0
        content = (output_dir / "gump_forrest.vcf").read_text()
        assert "VERSION:4.0" in content

    def test_version_flag(self, runner: CliRunner) -> None:
        """Test --version flag."""
        result = runner.invoke(app, ["convert", "--version"])

        assert result.exit_code == 0
        assert "csv2vcard version" in result.stdout

    def test_help_flag(self, runner: CliRunner) -> None:
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Convert CSV files to vCard format" in result.stdout

    def test_convert_help(self, runner: CliRunner) -> None:
        """Test convert --help."""
        result = runner.invoke(app, ["convert", "--help"])

        assert result.exit_code == 0
        assert "CSV file" in result.stdout
        # Check for "delimiter" without dashes due to ANSI escape codes in rich output
        assert "delimiter" in result.stdout
