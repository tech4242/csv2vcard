"""Tests for utility functions (v0.5.0)."""

from __future__ import annotations

import pytest

from csv2vcard.utils import (
    normalize_date,
    parse_geo,
    parse_utc_offset,
    phone_to_tel_uri,
    strip_accents,
    strip_accents_from_contact,
)


class TestStripAccents:
    """Test suite for strip_accents function."""

    def test_simple_accents(self) -> None:
        """Test removal of simple accents."""
        assert strip_accents("café") == "cafe"
        assert strip_accents("naïve") == "naive"
        assert strip_accents("résumé") == "resume"

    def test_german_umlauts(self) -> None:
        """Test removal of German umlauts."""
        assert strip_accents("Müller") == "Muller"
        assert strip_accents("Köln") == "Koln"
        assert strip_accents("Größe") == "Große"  # ß is preserved (not a diacritic)

    def test_spanish_accents(self) -> None:
        """Test removal of Spanish accents."""
        assert strip_accents("José") == "Jose"
        assert strip_accents("García") == "Garcia"
        assert strip_accents("señor") == "senor"

    def test_french_accents(self) -> None:
        """Test removal of French accents."""
        assert strip_accents("français") == "francais"
        assert strip_accents("être") == "etre"
        assert strip_accents("garçon") == "garcon"

    def test_no_accents(self) -> None:
        """Test string without accents."""
        assert strip_accents("hello") == "hello"
        assert strip_accents("John Doe") == "John Doe"

    def test_empty_string(self) -> None:
        """Test empty string."""
        assert strip_accents("") == ""

    def test_mixed_content(self) -> None:
        """Test string with mixed ASCII and accented characters."""
        assert strip_accents("Hello, José!") == "Hello, Jose!"
        assert strip_accents("123 café street") == "123 cafe street"


class TestStripAccentsFromContact:
    """Test suite for strip_accents_from_contact function."""

    def test_contact_with_accents(self) -> None:
        """Test stripping accents from contact dictionary."""
        contact = {
            "first_name": "José",
            "last_name": "García",
            "city": "München",
        }
        result = strip_accents_from_contact(contact)

        assert result["first_name"] == "Jose"
        assert result["last_name"] == "Garcia"
        assert result["city"] == "Munchen"

    def test_contact_without_accents(self) -> None:
        """Test contact without accents."""
        contact = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
        }
        result = strip_accents_from_contact(contact)

        assert result == contact

    def test_empty_contact(self) -> None:
        """Test empty contact dictionary."""
        result = strip_accents_from_contact({})
        assert result == {}

    def test_preserves_all_keys(self) -> None:
        """Test that all keys are preserved."""
        contact = {
            "first_name": "José",
            "last_name": "García",
            "email": "jose@example.com",
            "phone": "+1234567890",
        }
        result = strip_accents_from_contact(contact)

        assert set(result.keys()) == set(contact.keys())


class TestNormalizeDate:
    """Test date normalization (v0.6.0)."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("1944-06-06", "19440606"),
            ("19440606", "19440606"),
            ("1944/06/06", "19440606"),
            ("1944-06-06T10:00:00Z", "19440606"),
            ("06.06.1944", "19440606"),
            ("24/12/1990", "19901224"),
            ("12/24/1990", "19901224"),
            ("05/05/1990", "19900505"),
            ("--12-24", "--1224"),
            ("--0229", "--0229"),
        ],
    )
    def test_valid(self, value: str, expected: str) -> None:
        assert normalize_date(value) == expected

    @pytest.mark.parametrize("value", ["06/07/1990", "1990-02-30", "tomorrow", "", "--13-01"])
    def test_invalid_or_ambiguous(self, value: str) -> None:
        assert normalize_date(value) is None


class TestPhoneToTelUri:
    """Test tel: URI conversion (v0.6.0)."""

    def test_global_number(self) -> None:
        assert phone_to_tel_uri("+1 (555) 123-4567") == "tel:+1-555-123-4567"

    def test_local_number(self) -> None:
        assert phone_to_tel_uri("0170 1234") is None

    def test_extension_not_supported(self) -> None:
        assert phone_to_tel_uri("+1 555 1234 ext. 5") is None


class TestParseHelpers:
    """Test geo and UTC offset parsing (v0.6.0)."""

    def test_geo_formats(self) -> None:
        assert parse_geo("37.38,-122.08") == ("37.38", "-122.08")
        assert parse_geo("37.38;-122.08") == ("37.38", "-122.08")
        assert parse_geo("geo:37.38,-122.08") == ("37.38", "-122.08")
        assert parse_geo("Berlin") is None
        assert parse_geo("91,0") is None

    def test_utc_offset(self) -> None:
        assert parse_utc_offset("-05:00") == ("-", "05", "00")
        assert parse_utc_offset("+0530") == ("+", "05", "30")
        assert parse_utc_offset("UTC+1") == ("+", "01", "00")
        assert parse_utc_offset("America/New_York") is None
