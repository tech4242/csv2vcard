"""Tests for data models."""

from __future__ import annotations

import pytest

from csv2vcard.models import ALL_FIELDS, REQUIRED_FIELDS, Contact, VCardOutput, VCardVersion


class TestContact:
    """Test suite for Contact dataclass."""

    def test_create_contact_from_dict(self, sample_contact: dict[str, str]) -> None:
        """Test creating Contact from dictionary."""
        contact = Contact.from_dict(sample_contact)

        assert contact.last_name == "Gump"
        assert contact.first_name == "Forrest"
        assert contact.title == "Shrimp Man"
        assert contact.org == "Bubba Gump Shrimp Co."

    def test_contact_with_missing_fields(self) -> None:
        """Test Contact provides defaults for missing optional fields."""
        contact = Contact.from_dict({"last_name": "Doe", "first_name": "John"})

        assert contact.last_name == "Doe"
        assert contact.first_name == "John"
        assert contact.title == ""
        assert contact.org == ""
        assert contact.email == ""

    def test_contact_to_dict(self, sample_contact: dict[str, str]) -> None:
        """Test converting Contact back to dictionary."""
        contact = Contact.from_dict(sample_contact)
        result = contact.to_dict()

        assert result["last_name"] == "Gump"
        assert result["first_name"] == "Forrest"
        assert len(result) == len(ALL_FIELDS)

    def test_contact_strips_whitespace(self) -> None:
        """Test that Contact strips whitespace from fields."""
        contact = Contact.from_dict({
            "last_name": "  Doe  ",
            "first_name": "  John  ",
        })

        assert contact.last_name == "Doe"
        assert contact.first_name == "John"

    def test_get_safe_filename(self) -> None:
        """Test safe filename generation."""
        contact = Contact.from_dict({"last_name": "Doe", "first_name": "John"})

        assert contact.get_safe_filename() == "doe_john.vcf"

    def test_get_safe_filename_special_chars(self) -> None:
        """Test filename sanitization with special characters."""
        contact = Contact.from_dict({
            "last_name": "O'Brien",
            "first_name": "Mary-Jane",
        })
        filename = contact.get_safe_filename()

        assert "'" not in filename
        assert filename.endswith(".vcf")

    def test_get_safe_filename_path_traversal(self) -> None:
        """Test that path traversal is prevented in filenames."""
        contact = Contact.from_dict({
            "last_name": "../../../etc/passwd",
            "first_name": "test",
        })
        filename = contact.get_safe_filename()

        assert ".." not in filename
        assert "/" not in filename
        assert filename.endswith(".vcf")

    def test_get_safe_filename_empty_names(self) -> None:
        """Test filename generation with empty names."""
        contact = Contact.from_dict({"last_name": "", "first_name": ""})
        filename = contact.get_safe_filename()

        assert filename == "unknown_contact.vcf"


class TestVCardVersion:
    """Test suite for VCardVersion enum."""

    def test_version_values(self) -> None:
        """Test vCard version values."""
        assert VCardVersion.V3_0.value == "3.0"
        assert VCardVersion.V4_0.value == "4.0"

    def test_version_from_string(self) -> None:
        """Test creating version from string."""
        assert VCardVersion("3.0") == VCardVersion.V3_0
        assert VCardVersion("4.0") == VCardVersion.V4_0

    def test_invalid_version(self) -> None:
        """Test invalid version raises ValueError."""
        with pytest.raises(ValueError):
            VCardVersion("2.0")


class TestVCardOutput:
    """Test suite for VCardOutput dataclass."""

    def test_vcard_output_creation(self) -> None:
        """Test creating VCardOutput."""
        output = VCardOutput(
            filename="test.vcf",
            output="BEGIN:VCARD\nEND:VCARD\n",
            name="Test Contact",
            version=VCardVersion.V3_0,
        )

        assert output.filename == "test.vcf"
        assert output.name == "Test Contact"
        assert output.version == VCardVersion.V3_0

    def test_vcard_output_default_version(self) -> None:
        """Test VCardOutput defaults to v3.0."""
        output = VCardOutput(
            filename="test.vcf",
            output="content",
            name="Test",
        )

        assert output.version == VCardVersion.V3_0


class TestConstants:
    """Test module constants."""

    def test_required_fields(self) -> None:
        """Test REQUIRED_FIELDS contains expected fields."""
        assert "last_name" in REQUIRED_FIELDS
        assert "first_name" in REQUIRED_FIELDS
        assert len(REQUIRED_FIELDS) == 2

    def test_all_fields(self) -> None:
        """Test ALL_FIELDS contains all expected fields."""
        expected = {
            # Name components
            "last_name", "first_name", "middle_name", "name_prefix", "name_suffix",
            # Basic info
            "nickname", "gender", "birthday", "anniversary",
            # Contact
            "phone", "email", "website",
            # Organization
            "org", "title", "role",
            # Address
            "street", "city", "region", "p_code", "country",
            # Other
            "note",
        }
        assert expected == ALL_FIELDS
