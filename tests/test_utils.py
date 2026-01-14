"""Tests for utility functions (v0.5.0)."""

from __future__ import annotations

from csv2vcard.utils import strip_accents, strip_accents_from_contact


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
