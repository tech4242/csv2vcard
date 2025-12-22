"""Tests for CSV parsing functionality."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from csv2vcard.exceptions import ParseError, ValidationError
from csv2vcard.models import Contact
from csv2vcard.parse_csv import iter_contacts, parse_csv


class TestParseCSV:
    """Test suite for parse_csv function."""

    def test_parse_valid_csv(self, sample_csv: Path) -> None:
        """Test parsing a valid CSV file."""
        contacts = parse_csv(sample_csv)

        assert len(contacts) == 2
        assert contacts[0]["last_name"] == "Gump"
        assert contacts[0]["first_name"] == "Forrest"
        assert contacts[1]["last_name"] == "Doe"
        assert contacts[1]["first_name"] == "Jane"

    def test_parse_with_semicolon_delimiter(self, semicolon_csv: Path) -> None:
        """Test parsing CSV with semicolon delimiter."""
        contacts = parse_csv(semicolon_csv, csv_delimiter=";")

        assert len(contacts) == 1
        assert contacts[0]["last_name"] == "Smith"
        assert contacts[0]["first_name"] == "John"

    def test_parse_unicode_csv(self, unicode_csv: Path) -> None:
        """Test parsing CSV with Unicode characters."""
        contacts = parse_csv(unicode_csv)

        assert len(contacts) == 2
        assert contacts[0]["last_name"] == "Mueller"
        assert contacts[0]["city"] == "Munchen"
        assert contacts[1]["last_name"] == "Dupont"
        assert contacts[1]["city"] == "Paris"

    def test_parse_nonexistent_file(self, temp_dir: Path) -> None:
        """Test parsing a file that doesn't exist."""
        contacts = parse_csv(temp_dir / "nonexistent.csv")
        assert contacts == []

    def test_parse_nonexistent_file_strict(self, temp_dir: Path) -> None:
        """Test parsing nonexistent file in strict mode."""
        with pytest.raises(ValidationError, match="not found"):
            parse_csv(temp_dir / "nonexistent.csv", strict=True)

    def test_parse_empty_csv(self, empty_csv: Path) -> None:
        """Test parsing an empty CSV file."""
        contacts = parse_csv(empty_csv)
        assert contacts == []

    def test_parse_empty_csv_strict(self, empty_csv: Path) -> None:
        """Test parsing empty CSV in strict mode."""
        with pytest.raises(ParseError, match="empty"):
            parse_csv(empty_csv, strict=True)

    def test_parse_header_only_csv(self, header_only_csv: Path) -> None:
        """Test parsing a CSV with only headers."""
        contacts = parse_csv(header_only_csv)
        assert contacts == []

    def test_parse_strips_whitespace_from_headers(self, temp_dir: Path) -> None:
        """Test that header names are stripped of whitespace."""
        csv_content = " last_name , first_name , title \nGump,Forrest,Boss\n"
        csv_path = temp_dir / "whitespace.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        contacts = parse_csv(csv_path)

        assert len(contacts) == 1
        assert "last_name" in contacts[0]
        assert " last_name " not in contacts[0]

    def test_parse_accepts_path_object(self, sample_csv: Path) -> None:
        """Test that parse_csv accepts Path objects."""
        contacts = parse_csv(sample_csv)
        assert len(contacts) == 2

    def test_parse_accepts_string_path(self, sample_csv: Path) -> None:
        """Test that parse_csv accepts string paths."""
        contacts = parse_csv(str(sample_csv))
        assert len(contacts) == 2


class TestParseCSVValidation:
    """Test CSV validation in parse_csv."""

    def test_row_column_mismatch_skipped(
        self, malformed_csv: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that rows with wrong column count are skipped."""
        with caplog.at_level(logging.WARNING):
            contacts = parse_csv(malformed_csv)

        # Should skip rows with wrong column count
        # First data row has 2 columns (expected 3) - skipped
        # Second data row has 6 columns (expected 3) - skipped
        assert len(contacts) == 0

    def test_missing_required_fields_warning(
        self, temp_dir: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that missing required fields generate warnings."""
        csv_content = "title,org\nBoss,Acme\n"
        csv_path = temp_dir / "missing_required.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        with caplog.at_level(logging.WARNING):
            contacts = parse_csv(csv_path)

        # Should still return contacts but with warnings
        assert len(contacts) == 1
        assert any("required" in record.message.lower() for record in caplog.records)


class TestIterContacts:
    """Test the iter_contacts generator."""

    def test_iter_contacts_yields_contact_objects(self, sample_csv: Path) -> None:
        """Test that iter_contacts yields Contact objects."""
        contacts = list(iter_contacts(sample_csv))

        assert len(contacts) == 2
        assert all(isinstance(c, Contact) for c in contacts)
        assert contacts[0].last_name == "Gump"
        assert contacts[1].first_name == "Jane"

    def test_iter_contacts_with_delimiter(self, semicolon_csv: Path) -> None:
        """Test iter_contacts with custom delimiter."""
        contacts = list(iter_contacts(semicolon_csv, csv_delimiter=";"))

        assert len(contacts) == 1
        assert contacts[0].last_name == "Smith"
