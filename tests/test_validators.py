"""Tests for input validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from csv2vcard.exceptions import ValidationError
from csv2vcard.validators import (
    sanitize_filename,
    validate_contact,
    validate_csv_file,
    validate_output_directory,
)


class TestValidateContact:
    """Test suite for validate_contact function."""

    def test_valid_contact(self, sample_contact: dict[str, str]) -> None:
        """Test validation of a valid contact."""
        warnings = validate_contact(sample_contact)
        assert warnings == []

    def test_missing_required_fields(self) -> None:
        """Test detection of missing required fields."""
        contact = {"title": "Boss"}
        warnings = validate_contact(contact)

        assert len(warnings) > 0
        assert any("required" in w.lower() for w in warnings)

    def test_missing_required_fields_strict(self) -> None:
        """Test that strict mode raises on missing required fields."""
        contact = {"title": "Boss"}

        with pytest.raises(ValidationError, match="required"):
            validate_contact(contact, strict=True)

    def test_empty_required_field(self) -> None:
        """Test detection of empty required field."""
        contact = {"last_name": "", "first_name": "John"}
        warnings = validate_contact(contact)

        assert len(warnings) > 0
        assert any("empty" in w.lower() for w in warnings)

    def test_empty_required_field_strict(self) -> None:
        """Test strict mode with empty required field."""
        contact = {"last_name": "", "first_name": "John"}

        with pytest.raises(ValidationError, match="empty"):
            validate_contact(contact, strict=True)

    def test_invalid_email(self) -> None:
        """Test detection of invalid email format."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "email": "not-an-email",
        }
        warnings = validate_contact(contact)

        assert len(warnings) == 1
        assert "email" in warnings[0].lower()

    def test_valid_email(self) -> None:
        """Test that valid email passes validation."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "email": "john@example.com",
        }
        warnings = validate_contact(contact)

        assert warnings == []

    def test_whitespace_required_field(self) -> None:
        """Test that whitespace-only required field is detected."""
        contact = {"last_name": "   ", "first_name": "John"}
        warnings = validate_contact(contact)

        assert len(warnings) > 0


class TestValidateCSVFile:
    """Test suite for validate_csv_file function."""

    def test_valid_csv_file(self, sample_csv: Path) -> None:
        """Test validation of valid CSV file."""
        # Should not raise
        validate_csv_file(sample_csv)

    def test_nonexistent_file(self, temp_dir: Path) -> None:
        """Test validation of nonexistent file."""
        with pytest.raises(ValidationError, match="not found"):
            validate_csv_file(temp_dir / "nonexistent.csv")

    def test_not_a_file(self, temp_dir: Path) -> None:
        """Test validation when path is a directory."""
        with pytest.raises(ValidationError, match="not a file"):
            validate_csv_file(temp_dir)

    def test_non_csv_extension_warning(
        self, temp_dir: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that non-.csv extension generates warning."""
        import logging

        txt_file = temp_dir / "contacts.txt"
        txt_file.write_text("content")

        with caplog.at_level(logging.WARNING):
            validate_csv_file(txt_file)

        assert any(".csv" in record.message for record in caplog.records)

    def test_non_csv_extension_strict(self, temp_dir: Path) -> None:
        """Test strict mode with non-.csv extension."""
        txt_file = temp_dir / "contacts.txt"
        txt_file.write_text("content")

        with pytest.raises(ValidationError, match=".csv"):
            validate_csv_file(txt_file, strict=True)


class TestValidateOutputDirectory:
    """Test suite for validate_output_directory function."""

    def test_nonexistent_directory_ok(self, temp_dir: Path) -> None:
        """Test that nonexistent directory passes validation."""
        # Should not raise - will be created later
        validate_output_directory(temp_dir / "new_dir")

    def test_existing_directory_ok(self, temp_dir: Path) -> None:
        """Test that existing directory passes validation."""
        validate_output_directory(temp_dir)

    def test_file_instead_of_directory(self, temp_dir: Path) -> None:
        """Test error when path is a file instead of directory."""
        file_path = temp_dir / "not_a_dir"
        file_path.write_text("content")

        with pytest.raises(ValidationError, match="not a directory"):
            validate_output_directory(file_path)


class TestSanitizeFilename:
    """Test suite for sanitize_filename function."""

    def test_simple_name(self) -> None:
        """Test sanitization of simple name."""
        assert sanitize_filename("John") == "john"

    def test_special_characters(self) -> None:
        """Test removal of special characters."""
        result = sanitize_filename("O'Brien")
        assert "'" not in result
        assert result == "o_brien"

    def test_path_traversal(self) -> None:
        """Test prevention of path traversal."""
        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result
        assert "/" not in result

    def test_empty_string(self) -> None:
        """Test handling of empty string."""
        result = sanitize_filename("")
        assert result == "unknown"

    def test_only_special_chars(self) -> None:
        """Test handling of string with only special characters."""
        result = sanitize_filename("!@#$%^")
        assert result == "unknown"

    def test_unicode_characters(self) -> None:
        """Test handling of Unicode characters."""
        result = sanitize_filename("Mueller")
        assert result == "mueller"

    def test_hyphen_allowed(self) -> None:
        """Test that hyphens are allowed."""
        result = sanitize_filename("Mary-Jane")
        assert result == "mary-jane"

    def test_underscore_allowed(self) -> None:
        """Test that underscores are allowed."""
        result = sanitize_filename("John_Doe")
        assert result == "john_doe"
