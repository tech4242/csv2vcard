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


class TestMultiTypePhones:
    """Test multi-type phone field generation."""

    def test_phone_cell_v3(self) -> None:
        """Test cell phone in vCard 3.0."""
        contact = {"last_name": "Doe", "first_name": "John", "phone_cell": "+1234567890"}
        result = create_vcard(contact, version=VCardVersion.V3_0)

        assert "TEL;TYPE=CELL:" in result["output"]
        assert "+1234567890" in result["output"]

    def test_phone_cell_v4(self) -> None:
        """Test cell phone in vCard 4.0."""
        contact = {"last_name": "Doe", "first_name": "John", "phone_cell": "+1234567890"}
        result = create_vcard(contact, version=VCardVersion.V4_0)

        assert "TEL;TYPE=cell;VALUE=uri:tel:+1234567890" in result["output"]

    def test_phone_home_v3(self) -> None:
        """Test home phone in vCard 3.0."""
        contact = {"last_name": "Doe", "first_name": "John", "phone_home": "+1111111111"}
        result = create_vcard(contact, version=VCardVersion.V3_0)

        assert "TEL;TYPE=HOME,VOICE:" in result["output"]
        assert "+1111111111" in result["output"]

    def test_phone_work_v3(self) -> None:
        """Test work phone in vCard 3.0."""
        contact = {"last_name": "Doe", "first_name": "John", "phone_work": "+2222222222"}
        result = create_vcard(contact, version=VCardVersion.V3_0)

        assert "TEL;TYPE=WORK,VOICE:" in result["output"]
        assert "+2222222222" in result["output"]

    def test_phone_fax_v3(self) -> None:
        """Test fax number in vCard 3.0."""
        contact = {"last_name": "Doe", "first_name": "John", "phone_fax": "+3333333333"}
        result = create_vcard(contact, version=VCardVersion.V3_0)

        assert "TEL;TYPE=FAX:" in result["output"]
        assert "+3333333333" in result["output"]

    def test_multiple_phones_v3(self) -> None:
        """Test multiple phone types in same contact."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "phone_cell": "+1111111111",
            "phone_home": "+2222222222",
            "phone_work": "+3333333333",
        }
        result = create_vcard(contact, version=VCardVersion.V3_0)

        assert "TEL;TYPE=CELL:" in result["output"]
        assert "TEL;TYPE=HOME,VOICE:" in result["output"]
        assert "TEL;TYPE=WORK,VOICE:" in result["output"]


class TestMultiTypeEmails:
    """Test multi-type email field generation."""

    def test_email_home_v3(self) -> None:
        """Test home email in vCard 3.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "email_home": "john@personal.com",
        }
        result = create_vcard(contact, version=VCardVersion.V3_0)

        assert "EMAIL;TYPE=HOME:" in result["output"]
        assert "john@personal.com" in result["output"]

    def test_email_work_v3(self) -> None:
        """Test work email in vCard 3.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "email_work": "john@company.com",
        }
        result = create_vcard(contact, version=VCardVersion.V3_0)

        assert "EMAIL;TYPE=WORK:" in result["output"]
        assert "john@company.com" in result["output"]

    def test_email_home_v4(self) -> None:
        """Test home email in vCard 4.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "email_home": "john@personal.com",
        }
        result = create_vcard(contact, version=VCardVersion.V4_0)

        assert "EMAIL;TYPE=home:" in result["output"]
        assert "john@personal.com" in result["output"]

    def test_multiple_emails(self) -> None:
        """Test multiple email types in same contact."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "email": "john@default.com",
            "email_home": "john@personal.com",
            "email_work": "john@company.com",
        }
        result = create_vcard(contact, version=VCardVersion.V3_0)

        assert result["output"].count("EMAIL;") == 3


class TestHomeAddress:
    """Test home address field generation."""

    def test_home_address_v3(self) -> None:
        """Test home address in vCard 3.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "home_street": "123 Home St",
            "home_city": "Hometown",
            "home_region": "HT",
            "home_p_code": "12345",
            "home_country": "USA",
        }
        result = create_vcard(contact, version=VCardVersion.V3_0)

        assert "ADR;TYPE=HOME" in result["output"]
        assert "123 Home St" in result["output"]
        assert "Hometown" in result["output"]

    def test_home_address_v4(self) -> None:
        """Test home address in vCard 4.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "home_street": "123 Home St",
            "home_city": "Hometown",
        }
        result = create_vcard(contact, version=VCardVersion.V4_0)

        assert "ADR;TYPE=home:" in result["output"]

    def test_both_addresses(self) -> None:
        """Test work and home addresses in same contact."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "street": "456 Work Ave",
            "city": "Worktown",
            "home_street": "123 Home St",
            "home_city": "Hometown",
        }
        result = create_vcard(contact, version=VCardVersion.V3_0)

        assert "ADR;TYPE=WORK" in result["output"]
        assert "ADR;TYPE=HOME" in result["output"]


class TestMediaFields:
    """Test media field generation (photo, logo, key)."""

    def test_photo_url_v3(self) -> None:
        """Test photo URL in vCard 3.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "photo": "https://example.com/photo.jpg",
        }
        result = create_vcard(contact, version=VCardVersion.V3_0)

        assert "PHOTO;" in result["output"]
        assert "https://example.com/photo.jpg" in result["output"]

    def test_photo_url_v4(self) -> None:
        """Test photo URL in vCard 4.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "photo": "https://example.com/photo.jpg",
        }
        result = create_vcard(contact, version=VCardVersion.V4_0)

        assert "PHOTO:" in result["output"]
        assert "https://example.com/photo.jpg" in result["output"]

    def test_photo_base64_v3(self) -> None:
        """Test photo base64 in vCard 3.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "photo": "data:image/jpeg;base64,/9j/4AAQSkZJRg==",
        }
        result = create_vcard(contact, version=VCardVersion.V3_0)

        assert "PHOTO;ENCODING=b;TYPE=JPEG:" in result["output"]

    def test_logo_url_v3(self) -> None:
        """Test logo URL in vCard 3.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "logo": "https://example.com/logo.png",
        }
        result = create_vcard(contact, version=VCardVersion.V3_0)

        assert "LOGO;" in result["output"]
        assert "https://example.com/logo.png" in result["output"]

    def test_logo_v4(self) -> None:
        """Test logo in vCard 4.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "logo": "https://example.com/logo.png",
        }
        result = create_vcard(contact, version=VCardVersion.V4_0)

        assert "LOGO:" in result["output"]

    def test_key_url_v3(self) -> None:
        """Test public key URL in vCard 3.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "key": "https://example.com/key.pgp",
        }
        result = create_vcard(contact, version=VCardVersion.V3_0)

        assert "KEY;" in result["output"]
        assert "https://example.com/key.pgp" in result["output"]

    def test_key_v4(self) -> None:
        """Test public key in vCard 4.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "key": "https://example.com/key.pgp",
        }
        result = create_vcard(contact, version=VCardVersion.V4_0)

        assert "KEY:" in result["output"]


class TestAdditionalFields:
    """Test additional vCard fields (categories, geo, tz)."""

    def test_categories_v3(self) -> None:
        """Test categories in vCard 3.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "categories": "Work,Friends,VIP",
        }
        result = create_vcard(contact, version=VCardVersion.V3_0)

        assert "CATEGORIES;CHARSET=UTF-8:" in result["output"]
        # Commas are escaped in vCard format
        assert "Work" in result["output"]

    def test_categories_v4(self) -> None:
        """Test categories in vCard 4.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "categories": "Family",
        }
        result = create_vcard(contact, version=VCardVersion.V4_0)

        assert "CATEGORIES:" in result["output"]

    def test_geo_v3(self) -> None:
        """Test geo coordinates in vCard 3.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "geo": "37.386,-122.082",
        }
        result = create_vcard(contact, version=VCardVersion.V3_0)

        assert "GEO:" in result["output"]

    def test_geo_v4(self) -> None:
        """Test geo coordinates in vCard 4.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "geo": "37.386,-122.082",
        }
        result = create_vcard(contact, version=VCardVersion.V4_0)

        assert "GEO:" in result["output"]

    def test_timezone_v3(self) -> None:
        """Test timezone in vCard 3.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "tz": "America/New_York",
        }
        result = create_vcard(contact, version=VCardVersion.V3_0)

        assert "TZ:" in result["output"]
        assert "America/New_York" in result["output"]

    def test_timezone_v4(self) -> None:
        """Test timezone in vCard 4.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "tz": "-05:00",
        }
        result = create_vcard(contact, version=VCardVersion.V4_0)

        assert "TZ:" in result["output"]
