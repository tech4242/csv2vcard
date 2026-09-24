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
        assert "N:Doe;John;;;" in result["output"]
        assert "FN:John Doe" in result["output"]
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

    def test_v3_no_charset(self, sample_contact: dict[str, str]) -> None:
        """Test that vCard 3.0 doesn't use the vCard 2.1 CHARSET parameter."""
        contact = Contact.from_dict(sample_contact)
        output = _create_vcard_3(contact)

        assert "CHARSET" not in output

    def test_v3_name_format(self, sample_contact: dict[str, str]) -> None:
        """Test vCard 3.0 name format."""
        contact = Contact.from_dict(sample_contact)
        output = _create_vcard_3(contact)

        assert "N:Gump;Forrest;;;" in output
        assert "FN:Forrest Gump" in output

    def test_v3_address_format(self, sample_contact: dict[str, str]) -> None:
        """Test vCard 3.0 address format."""
        contact = Contact.from_dict(sample_contact)
        output = _create_vcard_3(contact)

        assert "ADR;TYPE=WORK:" in output

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

        # Commas separate list values and must not be escaped
        assert "CATEGORIES:Work,Friends,VIP" in result["output"]

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

        # vCard 3.0 TZ defaults to a UTC offset, so names need VALUE=text
        assert "TZ;VALUE=text:America/New_York" in result["output"]

    def test_timezone_v4(self) -> None:
        """Test timezone in vCard 4.0."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "tz": "-05:00",
        }
        result = create_vcard(contact, version=VCardVersion.V4_0)

        assert "TZ;VALUE=utc-offset:-0500" in result["output"]


def _unfold(output: str) -> str:
    """Undo RFC 6350 line folding."""
    return output.replace("\r\n ", "")


class TestSerialization:
    """Test RFC-compliant line endings, folding and escaping (v0.6.0)."""

    def test_crlf_line_endings(self, sample_contact: dict[str, str]) -> None:
        """Test that every line ends with CRLF."""
        for version in VCardVersion:
            output = create_vcard(sample_contact, version=version)["output"]
            assert output.endswith("END:VCARD\r\n")
            assert "\n" not in output.replace("\r\n", "")

    def test_long_lines_folded_at_75_octets(self) -> None:
        """Test that long lines are folded and unfold back to the original value."""
        note = "Ünïcödé " * 40
        output = create_vcard({"last_name": "Doe", "first_name": "John", "note": note})["output"]

        for line in output.split("\r\n"):
            assert len(line.encode("utf-8")) <= 75
        assert f"NOTE:{note.strip()}" in _unfold(output)

    def test_newline_in_value_cannot_inject_properties(self) -> None:
        """Test that line breaks in any field can't create extra properties."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "phone": "1\r\nEMAIL:evil@example.com",
            "website": "https://example.com\nNOTE:injected",
            "note": "line1\r\nline2",
        }
        for version in VCardVersion:
            output = create_vcard(contact, version=version)["output"]
            lines = _unfold(output).split("\r\n")
            assert not any(line.startswith("EMAIL") for line in lines)
            assert not any(line.startswith("NOTE:injected") for line in lines)

    def test_note_newlines_escaped(self) -> None:
        """Test that CRLF and LF in text become an escaped \\n."""
        contact = {"last_name": "Doe", "first_name": "John", "note": "a\r\nb\rc\nd"}
        output = create_vcard(contact)["output"]
        assert "NOTE:a\\nb\\nc\\nd" in output

    def test_prodid(self, minimal_contact: dict[str, str]) -> None:
        """Test that PRODID identifies the generator."""
        output = create_vcard(minimal_contact)["output"]
        assert "PRODID:-//tech4242//csv2vcard " in output


class TestListValues:
    """Test list-valued properties (v0.6.0)."""

    def test_categories_v4_not_escaped(self) -> None:
        """Test that category separators are kept and values escaped."""
        contact = {"last_name": "Doe", "first_name": "John", "categories": "Work, VIP;Gold"}
        output = create_vcard(contact, version=VCardVersion.V4_0)["output"]
        assert "CATEGORIES:Work,VIP\\;Gold" in output

    def test_nickname_list(self) -> None:
        """Test that multiple nicknames stay separate."""
        contact = {"last_name": "Doe", "first_name": "Robert", "nickname": "Bob,Rob"}
        assert "NICKNAME:Bob,Rob" in create_vcard(contact)["output"]


class TestVCard4Compliance:
    """Test vCard 4.0 value formats (v0.6.0)."""

    def test_tel_uri_has_no_spaces(self, sample_contact: dict[str, str]) -> None:
        """Test that international numbers become valid tel: URIs."""
        output = create_vcard(sample_contact, version=VCardVersion.V4_0)["output"]
        assert "TEL;TYPE=work,voice;VALUE=uri:tel:+49-170-5-25-25-25" in output

    def test_local_number_is_text(self) -> None:
        """Test that numbers without a country code are written as text."""
        contact = {"last_name": "Doe", "first_name": "John", "phone_cell": "0170 123456"}
        output = create_vcard(contact, version=VCardVersion.V4_0)["output"]
        assert "TEL;TYPE=cell:0170 123456" in output
        assert "tel:0170" not in output

    def test_photo_base64_is_data_uri(self) -> None:
        """Test that inline photos use a data: URI instead of ENCODING=b."""
        contact = {"last_name": "Doe", "first_name": "John", "photo": "iVBORw0KGgo="}
        output = create_vcard(contact, version=VCardVersion.V4_0)["output"]
        assert "PHOTO:data:image/png;base64,iVBORw0KGgo=" in _unfold(output)
        assert "ENCODING" not in output

    def test_key_base64_is_data_uri(self) -> None:
        """Test that inline keys use a data: URI."""
        contact = {"last_name": "Doe", "first_name": "John", "key": "mQENBFabc="}
        output = create_vcard(contact, version=VCardVersion.V4_0)["output"]
        assert "KEY:data:application/pgp-keys;base64,mQENBFabc=" in output

    def test_armored_key_is_text(self) -> None:
        """Test that ASCII-armored keys are kept as escaped text."""
        key = "-----BEGIN PGP PUBLIC KEY BLOCK-----\nmQENBF\n-----END PGP PUBLIC KEY BLOCK-----"
        contact = {"last_name": "Doe", "first_name": "John", "key": key}
        output = _unfold(create_vcard(contact, version=VCardVersion.V4_0)["output"])
        assert "KEY;VALUE=text:-----BEGIN PGP PUBLIC KEY BLOCK-----\\nmQENBF\\n" in output

    def test_gender_words_normalized(self) -> None:
        """Test that full gender words map to RFC 6350 codes."""
        contact = {"last_name": "Doe", "first_name": "Jane", "gender": "Female"}
        output = create_vcard(contact, version=VCardVersion.V4_0)["output"]
        assert "GENDER:F\r\n" in output

    def test_unparseable_date_kept_as_text(self) -> None:
        """Test that ambiguous dates are preserved with VALUE=text."""
        contact = {"last_name": "Doe", "first_name": "John", "birthday": "06/07/1990"}
        output = create_vcard(contact, version=VCardVersion.V4_0)["output"]
        assert "BDAY;VALUE=text:06/07/1990" in output

    def test_dates_basic_format(self) -> None:
        """Test that dates are written in basic format, year-less as --MMDD."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "birthday": "24.12.1990",
            "anniversary": "--06-15",
        }
        output = create_vcard(contact, version=VCardVersion.V4_0)["output"]
        assert "BDAY:19901224" in output
        assert "ANNIVERSARY:--0615" in output

    def test_invalid_geo_skipped(self) -> None:
        """Test that invalid coordinates are not written."""
        contact = {"last_name": "Doe", "first_name": "John", "geo": "Berlin"}
        output = create_vcard(contact, version=VCardVersion.V4_0)["output"]
        assert "GEO" not in output

    def test_kind_org(self) -> None:
        """Test that organization-only rows become KIND:org cards."""
        contact = {"org": "Acme Inc."}
        result = create_vcard(contact, version=VCardVersion.V4_0)
        assert "KIND:org" in result["output"]
        assert "FN:Acme Inc." in result["output"]
        assert result["filename"] == "acme_inc.vcf"

    def test_rfc9554_properties(self) -> None:
        """Test PRONOUNS, SOCIALPROFILE and LANG."""
        contact = {
            "last_name": "Doe",
            "first_name": "Alex",
            "pronouns": "they/them",
            "language": "en",
            "social_profile": "https://mastodon.social/@alex",
            "social_profile_2": "github.com/alex",
        }
        output = create_vcard(contact, version=VCardVersion.V4_0)["output"]
        assert "PRONOUNS:they/them" in output
        assert "LANG:en" in output
        assert "SOCIALPROFILE:https://mastodon.social/@alex" in output
        assert "SOCIALPROFILE:https://github.com/alex" in output


class TestVCard3Compliance:
    """Test vCard 3.0 value formats (v0.6.0)."""

    def test_data_uri_photo(self) -> None:
        """Test that a data: URI photo is split into TYPE and raw base64."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "photo": "data:image/png;base64,iVBORw0KGgo=",
        }
        output = create_vcard(contact)["output"]
        assert "PHOTO;ENCODING=b;TYPE=PNG:iVBORw0KGgo=" in output

    def test_dates(self) -> None:
        """Test ISO dates, and Apple's convention for dates without a year."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "birthday": "19901224",
            "anniversary": "--06-15",
        }
        output = create_vcard(contact)["output"]
        assert "BDAY:1990-12-24" in output
        assert "X-ANNIVERSARY;X-APPLE-OMIT-YEAR=1604:1604-06-15" in output

    def test_invalid_date_skipped(self) -> None:
        """Test that unrecognized dates are not written as invalid BDAY values."""
        contact = {"last_name": "Doe", "first_name": "John", "birthday": "sometime"}
        assert "BDAY" not in create_vcard(contact)["output"]

    def test_utc_offset_tz(self) -> None:
        """Test that UTC offsets are written without VALUE=text."""
        contact = {"last_name": "Doe", "first_name": "John", "tz": "+0530"}
        assert "TZ:+05:30" in create_vcard(contact)["output"]

    def test_org_only_shows_as_company(self) -> None:
        """Test Apple's company display hint for organization-only rows."""
        output = create_vcard({"org": "Acme"})["output"]
        assert "X-ABSHOWAS:COMPANY" in output
        assert "FN:Acme" in output

    def test_social_profile_extension(self) -> None:
        """Test that social profiles use Apple's X-SOCIALPROFILE in 3.0."""
        contact = {"last_name": "Doe", "first_name": "John", "social_profile": "https://x.com/jd"}
        assert "X-SOCIALPROFILE:https://x.com/jd" in create_vcard(contact)["output"]


class TestMultiValueAndExtensions:
    """Test numbered multi-value fields and X- extensions (v0.6.0)."""

    def test_numbered_values(self) -> None:
        """Test that email_2 / phone_cell_2 produce extra properties."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "email": "a@example.com",
            "email_2": "b@example.com",
            "phone_cell": "+111",
            "phone_cell_2": "+222",
        }
        output = create_vcard(contact)["output"]
        assert "EMAIL;TYPE=WORK:a@example.com" in output
        assert "EMAIL;TYPE=WORK:b@example.com" in output
        assert output.count("TEL;TYPE=CELL:") == 2

    def test_duplicate_values_written_once(self) -> None:
        """Test that the same email in two columns is written once."""
        contact = {
            "last_name": "Doe",
            "first_name": "John",
            "email": "a@example.com",
            "email_work": "A@example.com",
        }
        assert create_vcard(contact)["output"].count("EMAIL") == 1

    def test_extensions(self) -> None:
        """Test that X- keys are written as escaped extension properties."""
        contact = {"last_name": "Doe", "first_name": "John", "X-DEPARTMENT": "R&D, Berlin"}
        output = create_vcard(contact)["output"]
        assert "X-DEPARTMENT:R&D\\, Berlin" in output


class TestUID:
    """Test deterministic UIDs (v0.6.0)."""

    def test_uid_is_stable(self, sample_contact: dict[str, str]) -> None:
        """Test that the same contact always gets the same UID."""
        first = Contact.from_dict(sample_contact).generate_uid()
        second = Contact.from_dict(sample_contact).generate_uid()
        assert first == second

    def test_uid_differs_between_contacts(self) -> None:
        """Test that different contacts get different UIDs."""
        a = Contact.from_dict({"last_name": "Doe", "first_name": "John"}).generate_uid()
        b = Contact.from_dict({"last_name": "Doe", "first_name": "Jane"}).generate_uid()
        assert a != b

    def test_uid_field_used(self) -> None:
        """Test that a UUID in the uid column is kept as-is."""
        uid = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        output = create_vcard({"last_name": "Doe", "uid": uid}, version=VCardVersion.V4_0)
        assert f"UID:urn:uuid:{uid}" in output["output"]

    def test_non_uuid_uid_hashed(self) -> None:
        """Test that non-UUID source IDs become stable UUIDs."""
        a = Contact.from_dict({"uid": "crm-42"}).generate_uid()
        b = Contact.from_dict({"uid": "crm-42", "last_name": "Changed"}).generate_uid()
        assert a == b


class TestVCard21:
    """Test vCard 2.1 output (v0.6.0)."""

    def test_basic_structure(self, sample_contact: dict[str, str]) -> None:
        """Test 2.1 version line and parameter style."""
        output = create_vcard(sample_contact, version=VCardVersion.V2_1)["output"]
        assert "VERSION:2.1" in output
        assert "TEL;WORK;VOICE:+49 170 5 25 25 25" in output
        assert "EMAIL;INTERNET;WORK:forrestgump@example.com" in output
        assert "N:Gump;Forrest;;;" in output

    def test_non_ascii_quoted_printable(self) -> None:
        """Test that non-ASCII text is quoted-printable encoded."""
        contact = {"last_name": "Müller", "first_name": "Jürgen"}
        output = create_vcard(contact, version=VCardVersion.V2_1)["output"]
        assert "N;CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE:M=C3=BCller;J=C3=BCrgen;;;" in output

    def test_quoted_printable_soft_breaks(self) -> None:
        """Test that long values use QP soft line breaks of at most 76 chars."""
        contact = {"last_name": "Doe", "first_name": "John", "note": "é" * 100}
        output = create_vcard(contact, version=VCardVersion.V2_1)["output"]
        note_lines = output.split("NOTE;", 1)[1].split("\r\nREV")[0].split("\r\n")
        assert len(note_lines) > 1
        assert all(len(line) <= 76 for line in note_lines)
        assert all(line.endswith("=") for line in note_lines[:-1])

    def test_multiline_note(self) -> None:
        """Test that line breaks are encoded, not written raw."""
        contact = {"last_name": "Doe", "first_name": "John", "note": "a\nb"}
        output = create_vcard(contact, version=VCardVersion.V2_1)["output"]
        assert "NOTE;CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE:a=0D=0Ab" in output

    def test_base64_photo(self) -> None:
        """Test 2.1 inline photo layout: indented continuation and a blank line."""
        data = "iVBOR" + "A" * 200
        contact = {"last_name": "Doe", "first_name": "John", "photo": data}
        output = create_vcard(contact, version=VCardVersion.V2_1)["output"]
        assert "PHOTO;ENCODING=BASE64;PNG:iVBOR" in output
        block = output.split("PHOTO;", 1)[1].split("\r\n\r\n")[0]
        assert "".join(line.strip() for line in block.split(":", 1)[1].split("\r\n")) == data
