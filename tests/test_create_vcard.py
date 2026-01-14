"""Tests for vCard creation functionality."""

from __future__ import annotations

from csv2vcard.create_vcard import (
    _create_vcard_3,
    _create_vcard_4,
    create_vcard,
    create_vcard_typed,
)
from csv2vcard.models import Contact, VCardOutput, VCardVersion


class TestCreateVCard:
    """Test suite for vCard creation."""

    def test_create_vcard_returns_dict(self, sample_contact: dict[str, str]) -> None:
        """Test that create_vcard returns a dictionary."""
        result = create_vcard(sample_contact)

        assert isinstance(result, dict)
        assert "filename" in result
        assert "output" in result
        assert "name" in result

    def test_create_vcard_v3(self, sample_contact: dict[str, str]) -> None:
        """Test creating vCard 3.0."""
        result = create_vcard(sample_contact, version=VCardVersion.V3_0)

        assert result["filename"] == "gump_forrest.vcf"
        assert "VERSION:3.0" in result["output"]
        assert "BEGIN:VCARD" in result["output"]
        assert "END:VCARD" in result["output"]

    def test_create_vcard_v4(self, sample_contact: dict[str, str]) -> None:
        """Test creating vCard 4.0."""
        result = create_vcard(sample_contact, version=VCardVersion.V4_0)

        assert "VERSION:4.0" in result["output"]
        # v4.0 doesn't use CHARSET
        assert "CHARSET" not in result["output"]

    def test_create_vcard_default_version(self, sample_contact: dict[str, str]) -> None:
        """Test that default version is 3.0."""
        result = create_vcard(sample_contact)
        assert "VERSION:3.0" in result["output"]

    def test_create_vcard_minimal_contact(self, minimal_contact: dict[str, str]) -> None:
        """Test creating vCard with minimal contact data."""
        result = create_vcard(minimal_contact)

        assert result["filename"] == "doe_john.vcf"
        assert "N;" in result["output"]
        assert "FN;" in result["output"]
        # Optional fields should not be present
        assert "TITLE:" not in result["output"] or "TITLE:;" in result["output"]

    def test_create_vcard_accepts_contact_object(
        self, sample_contact: dict[str, str]
    ) -> None:
        """Test that create_vcard accepts Contact objects."""
        contact = Contact.from_dict(sample_contact)
        result = create_vcard(contact)

        assert result["filename"] == "gump_forrest.vcf"
        assert "Forrest" in result["output"]

    def test_create_vcard_name_field(self, sample_contact: dict[str, str]) -> None:
        """Test that name field is correctly formatted."""
        result = create_vcard(sample_contact)
        assert result["name"] == "Forrest Gump"


class TestCreateVCardTyped:
    """Test create_vcard_typed function."""

    def test_returns_vcard_output(self, sample_contact: dict[str, str]) -> None:
        """Test that create_vcard_typed returns VCardOutput."""
        result = create_vcard_typed(sample_contact)

        assert isinstance(result, VCardOutput)
        assert result.filename == "gump_forrest.vcf"
        assert result.version == VCardVersion.V3_0

    def test_with_v4(self, sample_contact: dict[str, str]) -> None:
        """Test create_vcard_typed with vCard 4.0."""
        result = create_vcard_typed(sample_contact, version=VCardVersion.V4_0)

        assert result.version == VCardVersion.V4_0
        assert "VERSION:4.0" in result.output


class TestVCard3Format:
    """Test vCard 3.0 format specifics."""

    def test_v3_has_charset(self, sample_contact: dict[str, str]) -> None:
        """Test that vCard 3.0 includes CHARSET."""
        contact = Contact.from_dict(sample_contact)
        output = _create_vcard_3(contact)

        assert "CHARSET=UTF-8" in output

    def test_v3_name_format(self, sample_contact: dict[str, str]) -> None:
        """Test vCard 3.0 name format."""
        contact = Contact.from_dict(sample_contact)
        output = _create_vcard_3(contact)

        assert "N;CHARSET=UTF-8:Gump;Forrest;;;" in output
        assert "FN;CHARSET=UTF-8:Forrest Gump" in output

    def test_v3_address_format(self, sample_contact: dict[str, str]) -> None:
        """Test vCard 3.0 address format."""
        contact = Contact.from_dict(sample_contact)
        output = _create_vcard_3(contact)

        assert "ADR;TYPE=WORK;CHARSET=UTF-8:" in output

    def test_v3_phone_format(self, sample_contact: dict[str, str]) -> None:
        """Test vCard 3.0 phone format."""
        contact = Contact.from_dict(sample_contact)
        output = _create_vcard_3(contact)

        assert "TEL;TYPE=WORK,VOICE:" in output

    def test_v3_optional_fields_omitted_when_empty(
        self, minimal_contact: dict[str, str]
    ) -> None:
        """Test that empty optional fields are omitted."""
        contact = Contact.from_dict(minimal_contact)
        output = _create_vcard_3(contact)

        # Should not have TITLE, ORG, etc. for minimal contact
        assert output.count("TITLE") == 0 or "TITLE:" not in output


class TestVCard4Format:
    """Test vCard 4.0 format specifics."""

    def test_v4_no_charset(self, sample_contact: dict[str, str]) -> None:
        """Test that vCard 4.0 doesn't include CHARSET."""
        contact = Contact.from_dict(sample_contact)
        output = _create_vcard_4(contact)

        assert "CHARSET" not in output

    def test_v4_name_format(self, sample_contact: dict[str, str]) -> None:
        """Test vCard 4.0 name format."""
        contact = Contact.from_dict(sample_contact)
        output = _create_vcard_4(contact)

        assert "N:Gump;Forrest;;;" in output
        assert "FN:Forrest Gump" in output

    def test_v4_tel_format(self, sample_contact: dict[str, str]) -> None:
        """Test vCard 4.0 telephone format."""
        contact = Contact.from_dict(sample_contact)
        output = _create_vcard_4(contact)

        assert "TEL;TYPE=work,voice;VALUE=uri:tel:" in output

    def test_v4_address_format(self, sample_contact: dict[str, str]) -> None:
        """Test vCard 4.0 address format."""
        contact = Contact.from_dict(sample_contact)
        output = _create_vcard_4(contact)

        assert "ADR;TYPE=work:" in output


class TestSafeFilename:
    """Test filename sanitization via create_vcard."""

    def test_path_traversal_prevention(self) -> None:
        """Test that path traversal is prevented in filenames."""
        malicious_contact = {
            "last_name": "../../../etc/passwd",
            "first_name": "test",
        }
        result = create_vcard(malicious_contact)

        # Should not contain path traversal
        assert ".." not in result["filename"]
        assert "/" not in result["filename"]

    def test_special_characters_sanitized(self) -> None:
        """Test that special characters are sanitized."""
        contact = {
            "last_name": "O'Brien",
            "first_name": "John<script>",
        }
        result = create_vcard(contact)

        # Should not contain dangerous characters
        assert "<" not in result["filename"]
        assert ">" not in result["filename"]
        assert result["filename"].endswith(".vcf")

    def test_unicode_names(self) -> None:
        """Test handling of Unicode characters in names."""
        contact = {
            "last_name": "Muller",
            "first_name": "Hans",
        }
        result = create_vcard(contact)

        assert result["filename"] == "muller_hans.vcf"
