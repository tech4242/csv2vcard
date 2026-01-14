"""Tests for input validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from csv2vcard.exceptions import ValidationError
from csv2vcard.validators import (
    sanitize_filename,
    validate_contact,
    validate_csv_file,
    validate_email,
    validate_gender,
    validate_geo,
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


class TestValidateEmail:
    """Test suite for validate_email function (v0.5.0)."""

    def test_valid_email_simple(self) -> None:
        """Test simple valid email."""
        assert validate_email("user@example.com") is True

    def test_valid_email_with_plus(self) -> None:
        """Test email with plus sign."""
        assert validate_email("user+tag@example.com") is True

    def test_valid_email_subdomain(self) -> None:
        """Test email with subdomain."""
        assert validate_email("user@mail.example.com") is True

    def test_invalid_email_no_at(self) -> None:
        """Test email without @ sign."""
        assert validate_email("userexample.com") is False

    def test_invalid_email_no_domain(self) -> None:
        """Test email without domain."""
        assert validate_email("user@") is False

    def test_invalid_email_no_tld(self) -> None:
        """Test email without TLD."""
        assert validate_email("user@example") is False

    def test_empty_email(self) -> None:
        """Test empty email."""
        assert validate_email("") is False


class TestValidateGender:
    """Test suite for validate_gender function (v0.5.0)."""

    def test_valid_male_letter(self) -> None:
        """Test valid M gender code."""
        assert validate_gender("M") is True

    def test_valid_female_letter(self) -> None:
        """Test valid F gender code."""
        assert validate_gender("F") is True

    def test_valid_other_letter(self) -> None:
        """Test valid O gender code."""
        assert validate_gender("O") is True

    def test_valid_none_letter(self) -> None:
        """Test valid N gender code."""
        assert validate_gender("N") is True

    def test_valid_unknown_letter(self) -> None:
        """Test valid U gender code."""
        assert validate_gender("U") is True

    def test_valid_male_word(self) -> None:
        """Test 'Male' as valid gender."""
        assert validate_gender("Male") is True

    def test_valid_female_word(self) -> None:
        """Test 'Female' as valid gender."""
        assert validate_gender("Female") is True

    def test_case_insensitive(self) -> None:
        """Test case insensitivity."""
        assert validate_gender("m") is True
        assert validate_gender("FEMALE") is True

    def test_invalid_gender(self) -> None:
        """Test invalid gender value."""
        assert validate_gender("X") is False
        assert validate_gender("invalid") is False

    def test_empty_gender(self) -> None:
        """Test empty gender."""
        assert validate_gender("") is False


class TestValidateGeo:
    """Test suite for validate_geo function (v0.5.0)."""

    def test_valid_coordinates_comma(self) -> None:
        """Test valid coordinates with comma separator."""
        assert validate_geo("37.386013,-122.082932") is True

    def test_valid_coordinates_semicolon(self) -> None:
        """Test valid coordinates with semicolon separator (vCard 3.0)."""
        assert validate_geo("37.386013;-122.082932") is True

    def test_valid_coordinates_with_spaces(self) -> None:
        """Test coordinates with spaces."""
        assert validate_geo("37.386013, -122.082932") is True

    def test_valid_coordinates_at_boundaries(self) -> None:
        """Test coordinates at valid boundaries."""
        assert validate_geo("90.0,180.0") is True
        assert validate_geo("-90.0,-180.0") is True
        assert validate_geo("0,0") is True

    def test_invalid_latitude_too_high(self) -> None:
        """Test latitude exceeding 90."""
        assert validate_geo("91.0,0.0") is False

    def test_invalid_latitude_too_low(self) -> None:
        """Test latitude below -90."""
        assert validate_geo("-91.0,0.0") is False

    def test_invalid_longitude_too_high(self) -> None:
        """Test longitude exceeding 180."""
        assert validate_geo("0.0,181.0") is False

    def test_invalid_longitude_too_low(self) -> None:
        """Test longitude below -180."""
        assert validate_geo("0.0,-181.0") is False

    def test_invalid_format_not_numbers(self) -> None:
        """Test non-numeric coordinates."""
        assert validate_geo("abc,def") is False

    def test_invalid_format_single_value(self) -> None:
        """Test single value instead of pair."""
        assert validate_geo("37.386013") is False

    def test_invalid_format_three_values(self) -> None:
        """Test three values."""
        assert validate_geo("37.386013,-122.082932,100") is False

    def test_empty_geo(self) -> None:
        """Test empty geo string."""
        assert validate_geo("") is False
