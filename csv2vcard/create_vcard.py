"""vCard generation for csv2vcard."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from typing import NamedTuple

from csv2vcard._version import __version__
from csv2vcard.models import Contact, VCardOutput, VCardVersion
from csv2vcard.utils import normalize_date, parse_geo, parse_utc_offset, phone_to_tel_uri

logger = logging.getLogger(__name__)

PRODID = f"-//tech4242//csv2vcard {__version__}//EN"

# RFC 2425/2426/6350: content lines end with CRLF and are folded at 75 octets
CRLF = "\r\n"
MAX_LINE_OCTETS = 75

# (field, vCard 3.0 TYPE) - 4.0 uses the lower-case form, 2.1 separates with ";"
PHONE_TYPES = (
    ("phone", "WORK,VOICE"),
    ("phone_cell", "CELL"),
    ("phone_home", "HOME,VOICE"),
    ("phone_work", "WORK,VOICE"),
    ("phone_fax", "FAX"),
)
EMAIL_TYPES = (
    ("email", "WORK"),
    ("email_home", "HOME"),
    ("email_work", "WORK"),
)

GENDER_WORDS = {"MALE": "M", "FEMALE": "F", "OTHER": "O", "NONE": "N", "UNKNOWN": "U"}

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")  # all except TAB and LF
_ANY_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]+")
_URI = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]+:\S")
_BARE_URL = re.compile(r"^(www\.)?[\w-]+(\.[\w-]+)*\.[a-z]{2,}(/\S*)?$", re.IGNORECASE)
_DATA_URI = re.compile(
    r"^data:(?P<type>[^;,]*)(?P<params>(?:;[^;,]*)*);base64,(?P<data>.*)$",
    re.IGNORECASE | re.DOTALL,
)
_BASE64_SIGNATURES = (
    ("/9j/", "image/jpeg"),
    ("iVBOR", "image/png"),
    ("R0lGOD", "image/gif"),
    ("UklGR", "image/webp"),
)


def create_vcard(
    contact: dict[str, str] | Contact,
    version: VCardVersion = VCardVersion.V3_0,
) -> dict[str, str]:
    """
    Create a vCard from a contact.

    Args:
        contact: Contact data (dict or Contact object)
        version: vCard version to generate (2.1, 3.0 or 4.0)

    Returns:
        Dictionary with 'filename', 'output', and 'name' keys
        (backwards compatible format)
    """
    # Normalize to Contact object
    contact_obj = Contact.from_dict(contact) if isinstance(contact, dict) else contact

    if version == VCardVersion.V4_0:
        output = _create_vcard_4(contact_obj)
    elif version == VCardVersion.V2_1:
        output = _create_vcard_21(contact_obj)
    else:
        output = _create_vcard_3(contact_obj)

    # Generate safe filename (prevents path traversal)
    filename = contact_obj.get_safe_filename()
    name = contact_obj.get_formatted_name()

    logger.debug(f"Created vCard {version.value} for {name}")

    # Return dict for backwards compatibility
    return {
        "filename": filename,
        "output": output,
        "name": name,
    }


def create_vcard_typed(
    contact: dict[str, str] | Contact,
    version: VCardVersion = VCardVersion.V3_0,
) -> VCardOutput:
    """
    Create a vCard from a contact with typed return.

    Args:
        contact: Contact data (dict or Contact object)
        version: vCard version to generate (2.1, 3.0 or 4.0)

    Returns:
        VCardOutput dataclass
    """
    result = create_vcard(contact, version)
    return VCardOutput(
        filename=result["filename"],
        output=result["output"],
        name=result["name"],
        version=version,
    )


# ---------------------------------------------------------------------------
# Value encoding helpers
# ---------------------------------------------------------------------------


def _normalize_text(value: str) -> str:
    """Normalize line breaks to LF and drop other control characters."""
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    return _CONTROL_CHARS.sub("", value)


def _escape_vcard_value(value: str) -> str:
    """
    Escape special characters in vCard 3.0/4.0 text values.

    Args:
        value: Raw string value

    Returns:
        Escaped string safe for vCard (never contains a raw line break)
    """
    value = _normalize_text(value)
    # Escape backslashes first, then other special chars
    value = value.replace("\\", "\\\\")
    value = value.replace(",", "\\,")
    value = value.replace(";", "\\;")
    value = value.replace("\n", "\\n")
    return value


def _escape_list(value: str) -> str:
    """Escape a comma-separated list value (CATEGORIES, NICKNAME), keeping the separators."""
    return ",".join(_escape_vcard_value(item.strip()) for item in value.split(",") if item.strip())


def _structured(*components: str) -> str:
    """Build a structured value (N, ADR) from escaped components."""
    return ";".join(_escape_vcard_value(c) for c in components)


def _clean(value: str) -> str:
    """Make a URI-like or single-token value safe: no control characters or line breaks."""
    return _ANY_CONTROL_CHARS.sub(" ", value).strip()


def _is_uri(value: str) -> bool:
    return bool(_URI.match(value))


def _fold_line(line: str) -> str:
    """Fold a content line at 75 octets without splitting UTF-8 sequences (RFC 6350 3.2)."""
    if len(line.encode("utf-8")) <= MAX_LINE_OCTETS:
        return line
    parts: list[str] = []
    current = ""
    size = 0
    for char in line:
        char_size = len(char.encode("utf-8"))
        if size + char_size > MAX_LINE_OCTETS:
            parts.append(current)
            current = char
            size = 1 + char_size  # continuation lines start with a space
        else:
            current += char
            size += char_size
    parts.append(current)
    return (CRLF + " ").join(parts)


def _serialize(lines: list[str], *, fold: bool = True) -> str:
    """Join content lines with CRLF, folding long lines (pre-formatted lines are kept)."""
    if fold:
        lines = [line if CRLF in line else _fold_line(line) for line in lines]
    return CRLF.join(lines) + CRLF


def _typed_values(
    contact: Contact, specs: tuple[tuple[str, str], ...]
) -> Iterator[tuple[str, str]]:
    """Yield (value, types) for multi-type fields, skipping duplicate values."""
    seen: set[str] = set()
    for field_name, types in specs:
        for value in contact.values(field_name):
            value = _clean(value)
            if value and value.casefold() not in seen:
                seen.add(value.casefold())
                yield value, types


def _addresses(contact: Contact) -> Iterator[tuple[str, tuple[str, ...]]]:
    """Yield (type, ADR components) for work and home addresses that have data."""
    work = (contact.street, contact.city, contact.region, contact.p_code, contact.country)
    home = (
        contact.home_street,
        contact.home_city,
        contact.home_region,
        contact.home_p_code,
        contact.home_country,
    )
    for adr_type, (street, city, region, p_code, country) in (("WORK", work), ("HOME", home)):
        if any((street, city, region, p_code, country)):
            # ADR format: PO Box;Extended;Street;City;Region;PostalCode;Country
            yield adr_type, ("", "", street, city, region, p_code, country)


def _n_components(contact: Contact) -> tuple[str, ...]:
    # N field: LastName;FirstName;MiddleName;Prefix;Suffix
    return (
        contact.last_name,
        contact.first_name,
        contact.middle_name,
        contact.name_prefix,
        contact.name_suffix,
    )


def _date(contact: Contact, field_name: str) -> str | None:
    """Normalize a date field, logging a warning if it cannot be interpreted."""
    raw = getattr(contact, field_name)
    if not raw:
        return None
    normalized = normalize_date(raw)
    if normalized is None:
        logger.warning(
            f"{contact.get_formatted_name()}: unrecognized {field_name} '{raw}' "
            "(use YYYY-MM-DD)"
        )
    return normalized


def _social_profiles(contact: Contact) -> Iterator[str]:
    for value in contact.values("social_profile"):
        value = _clean(value)
        if _BARE_URL.match(value):
            value = f"https://{value}"
        if _is_uri(value):
            yield value
        else:
            logger.warning(
                f"{contact.get_formatted_name()}: social_profile '{value}' is not a URL, skipped"
            )


def _geo(contact: Contact) -> tuple[str, str] | None:
    if not contact.geo:
        return None
    coords = parse_geo(contact.geo)
    if coords is None:
        logger.warning(f"{contact.get_formatted_name()}: invalid geo '{contact.geo}', skipped")
    return coords


class _Media(NamedTuple):
    """A PHOTO, LOGO or KEY value: either a URI or inline base64 data."""

    uri: str | None
    media_type: str
    data: str


def _parse_media(value: str, default_type: str) -> _Media:
    value = value.strip()
    match = _DATA_URI.match(value)
    if match:
        media_type = match["type"] or default_type
        return _Media(None, media_type.lower(), re.sub(r"\s+", "", match["data"]))
    if _is_uri(value):
        return _Media(_clean(value), "", "")
    data = re.sub(r"\s+", "", value)
    for signature, media_type in _BASE64_SIGNATURES:
        if data.startswith(signature):
            return _Media(None, media_type, data)
    return _Media(None, default_type, data)


def _v3_type(media_type: str) -> str:
    """Map a media type to the vCard 2.1/3.0 TYPE parameter (image/png -> PNG)."""
    if "pgp" in media_type:
        return "PGP"
    if "pkix" in media_type or "x509" in media_type:
        return "X509"
    return media_type.rsplit("/", 1)[-1].upper()


def _is_armored_key(value: str) -> bool:
    return value.lstrip().startswith("-----BEGIN")


# ---------------------------------------------------------------------------
# vCard 3.0
# ---------------------------------------------------------------------------


def _create_vcard_3(contact: Contact) -> str:
    """
    Generate vCard 3.0 format (RFC 2426).

    Args:
        contact: Contact object

    Returns:
        vCard 3.0 formatted string
    """
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"PRODID:{PRODID}",
    ]

    lines.append(f"N:{_structured(*_n_components(contact))}")
    lines.append(f"FN:{_escape_vcard_value(contact.get_formatted_name())}")

    if contact.is_organization:
        # Apple Contacts extension: display the card as a company
        lines.append("X-ABSHOWAS:COMPANY")

    # Optional fields - only include if non-empty
    if contact.nickname:
        lines.append(f"NICKNAME:{_escape_list(contact.nickname)}")

    if contact.gender:
        # vCard 3.0 doesn't have GENDER, use X-GENDER extension
        lines.append(f"X-GENDER:{_escape_vcard_value(contact.gender)}")

    for field_name, prop in (("birthday", "BDAY"), ("anniversary", "X-ANNIVERSARY")):
        date = _date(contact, field_name)
        if date and date.startswith("--"):
            # vCard 3.0 has no year-less dates; Apple's convention is year 1604
            lines.append(f"{prop};X-APPLE-OMIT-YEAR=1604:1604-{date[2:4]}-{date[4:6]}")
        elif date:
            lines.append(f"{prop}:{date[:4]}-{date[4:6]}-{date[6:8]}")

    if contact.title:
        lines.append(f"TITLE:{_escape_vcard_value(contact.title)}")

    if contact.role:
        lines.append(f"ROLE:{_escape_vcard_value(contact.role)}")

    if contact.org:
        lines.append(f"ORG:{_escape_vcard_value(contact.org)}")

    for value, types in _typed_values(contact, PHONE_TYPES):
        lines.append(f"TEL;TYPE={types}:{_escape_vcard_value(value)}")

    for value, types in _typed_values(contact, EMAIL_TYPES):
        lines.append(f"EMAIL;TYPE={types}:{_escape_vcard_value(value)}")

    for value in contact.values("website"):
        lines.append(f"URL;TYPE=WORK:{_clean(value)}")

    for adr_type, components in _addresses(contact):
        lines.append(f"ADR;TYPE={adr_type}:{_structured(*components)}")

    if contact.photo:
        lines.append(_format_media_field_v3("PHOTO", contact.photo))
    if contact.logo:
        lines.append(_format_media_field_v3("LOGO", contact.logo))

    if contact.categories:
        lines.append(f"CATEGORIES:{_escape_list(contact.categories)}")

    geo = _geo(contact)
    if geo:
        # vCard 3.0 GEO format: lat;lon
        lines.append(f"GEO:{geo[0]};{geo[1]}")

    if contact.tz:
        offset = parse_utc_offset(contact.tz)
        if offset:
            lines.append(f"TZ:{offset[0]}{offset[1]}:{offset[2]}")
        else:
            lines.append(f"TZ;VALUE=text:{_escape_vcard_value(contact.tz)}")

    if contact.key:
        lines.append(_format_key_field_v3(contact.key))

    for profile in _social_profiles(contact):
        # Apple Contacts extension (SOCIALPROFILE is only standard in vCard 4.0)
        lines.append(f"X-SOCIALPROFILE:{profile}")

    if contact.note:
        lines.append(f"NOTE:{_escape_vcard_value(contact.note)}")

    for name, value in contact.extensions.items():
        lines.append(f"{name}:{_escape_vcard_value(value)}")

    lines.append(f"REV:{Contact.generate_rev()}")
    lines.append(f"UID:{contact.generate_uid()}")
    lines.append("END:VCARD")
    return _serialize(lines)


def _format_media_field_v3(field_name: str, value: str) -> str:
    """Format PHOTO or LOGO field for vCard 3.0."""
    media = _parse_media(value, "image/jpeg")
    if media.uri:
        return f"{field_name};VALUE=URI:{media.uri}"
    return f"{field_name};ENCODING=b;TYPE={_v3_type(media.media_type)}:{media.data}"


def _format_key_field_v3(value: str) -> str:
    """Format KEY field for vCard 3.0."""
    if _is_armored_key(value):
        return f"KEY;TYPE=PGP;VALUE=text:{_escape_vcard_value(value.strip())}"
    media = _parse_media(value, "application/pgp-keys")
    if media.uri:
        return f"KEY;VALUE=URI:{media.uri}"
    return f"KEY;ENCODING=b;TYPE={_v3_type(media.media_type)}:{media.data}"


# ---------------------------------------------------------------------------
# vCard 4.0
# ---------------------------------------------------------------------------


def _create_vcard_4(contact: Contact) -> str:
    """
    Generate vCard 4.0 format (RFC 6350, plus RFC 9554 properties).

    Args:
        contact: Contact object

    Returns:
        vCard 4.0 formatted string
    """
    lines = [
        "BEGIN:VCARD",
        "VERSION:4.0",
        f"PRODID:{PRODID}",
    ]

    if contact.is_organization:
        lines.append("KIND:org")

    # Note: CHARSET is not used in vCard 4.0 (UTF-8 is mandatory)
    lines.append(f"N:{_structured(*_n_components(contact))}")
    lines.append(f"FN:{_escape_vcard_value(contact.get_formatted_name())}")

    if contact.nickname:
        lines.append(f"NICKNAME:{_escape_list(contact.nickname)}")

    if contact.gender:
        # vCard 4.0 GENDER format: single letter (M/F/O/N/U) or ;text
        gender = contact.gender.upper()
        gender = GENDER_WORDS.get(gender, gender)
        if gender in ("M", "F", "O", "N", "U"):
            lines.append(f"GENDER:{gender}")
        else:
            lines.append(f"GENDER:;{_escape_vcard_value(contact.gender)}")

    for field_name, prop in (("birthday", "BDAY"), ("anniversary", "ANNIVERSARY")):
        raw = getattr(contact, field_name)
        date = _date(contact, field_name)
        if date:
            # vCard 4.0 format: YYYYMMDD or --MMDD
            lines.append(f"{prop}:{date}")
        elif raw:
            # vCard 4.0 allows free-form text dates, so nothing is lost
            lines.append(f"{prop};VALUE=text:{_escape_vcard_value(raw)}")

    if contact.pronouns:
        lines.append(f"PRONOUNS:{_escape_vcard_value(contact.pronouns)}")

    if contact.language:
        lines.append(f"LANG:{_clean(contact.language)}")

    if contact.title:
        lines.append(f"TITLE:{_escape_vcard_value(contact.title)}")

    if contact.role:
        lines.append(f"ROLE:{_escape_vcard_value(contact.role)}")

    if contact.org:
        lines.append(f"ORG:{_escape_vcard_value(contact.org)}")

    for value, types in _typed_values(contact, PHONE_TYPES):
        tel_uri = phone_to_tel_uri(value)
        if tel_uri:
            lines.append(f"TEL;TYPE={types.lower()};VALUE=uri:{tel_uri}")
        else:
            # Local numbers can't be tel: URIs without a phone-context; use text
            lines.append(f"TEL;TYPE={types.lower()}:{_escape_vcard_value(value)}")

    for value, types in _typed_values(contact, EMAIL_TYPES):
        lines.append(f"EMAIL;TYPE={types.lower()}:{_escape_vcard_value(value)}")

    for value in contact.values("website"):
        lines.append(f"URL;TYPE=work:{_clean(value)}")

    for adr_type, components in _addresses(contact):
        lines.append(f"ADR;TYPE={adr_type.lower()}:{_structured(*components)}")

    if contact.photo:
        lines.append(_format_media_field_v4("PHOTO", contact.photo))
    if contact.logo:
        lines.append(_format_media_field_v4("LOGO", contact.logo))

    if contact.categories:
        lines.append(f"CATEGORIES:{_escape_list(contact.categories)}")

    geo = _geo(contact)
    if geo:
        # vCard 4.0 GEO format: geo:lat,lon
        lines.append(f"GEO:geo:{geo[0]},{geo[1]}")

    if contact.tz:
        offset = parse_utc_offset(contact.tz)
        if offset:
            lines.append(f"TZ;VALUE=utc-offset:{offset[0]}{offset[1]}{offset[2]}")
        else:
            lines.append(f"TZ:{_escape_vcard_value(contact.tz)}")

    if contact.key:
        lines.append(_format_key_field_v4(contact.key))

    for profile in _social_profiles(contact):
        lines.append(f"SOCIALPROFILE:{profile}")

    if contact.note:
        lines.append(f"NOTE:{_escape_vcard_value(contact.note)}")

    for name, value in contact.extensions.items():
        lines.append(f"{name}:{_escape_vcard_value(value)}")

    lines.append(f"REV:{Contact.generate_rev()}")
    lines.append(f"UID:urn:uuid:{contact.generate_uid()}")
    lines.append("END:VCARD")
    return _serialize(lines)


def _format_media_field_v4(field_name: str, value: str) -> str:
    """Format PHOTO or LOGO field for vCard 4.0 (inline data as a data: URI)."""
    media = _parse_media(value, "image/jpeg")
    if media.uri:
        return f"{field_name}:{media.uri}"
    return f"{field_name}:data:{media.media_type};base64,{media.data}"


def _format_key_field_v4(value: str) -> str:
    """Format KEY field for vCard 4.0."""
    if _is_armored_key(value):
        return f"KEY;VALUE=text:{_escape_vcard_value(value.strip())}"
    media = _parse_media(value, "application/pgp-keys")
    if media.uri:
        return f"KEY:{media.uri}"
    return f"KEY:data:{media.media_type};base64,{media.data}"


# ---------------------------------------------------------------------------
# vCard 2.1
# ---------------------------------------------------------------------------


def _escape_21(value: str) -> str:
    """Escape a vCard 2.1 component: only semicolons are escaped."""
    return _normalize_text(value).replace(";", "\\;")


def _qp_encode(text: str) -> list[str]:
    """
    Quoted-printable encode text into atoms, one per character.

    Keeping a character's =XX sequences in one atom means soft line breaks
    never split a multi-byte UTF-8 character, which line-based parsers choke on.
    """
    text = text.replace("\n", "\r\n")
    atoms: list[str] = []
    for index, char in enumerate(text):
        is_last = index == len(text) - 1
        if ("!" <= char <= "~" and char != "=") or (char in "\t " and not is_last):
            atoms.append(char)
        else:
            atoms.append("".join(f"={byte:02X}" for byte in char.encode("utf-8")))
    return atoms


def _prop_21(name: str, value: str, *, force_qp: bool = False) -> str:
    """
    Build a vCard 2.1 text property, switching to quoted-printable if needed.

    vCard 2.1 has no RFC 2425 line folding, so non-ASCII, multi-line or long
    values are quoted-printable encoded with soft line breaks instead.
    """
    line = f"{name}:{value}"
    if not force_qp and value.isascii() and "\n" not in value and len(line) <= MAX_LINE_OCTETS:
        return line

    lines: list[str] = []
    current = f"{name};CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE:"
    for atom in _qp_encode(value):
        if len(current) + len(atom) > MAX_LINE_OCTETS:  # leave room for the soft break
            lines.append(current + "=")
            # A leading space would read as RFC 2425 line folding, so encode it
            current = {" ": "=20", "\t": "=09"}.get(atom, atom)
        else:
            current += atom
    lines.append(current)
    return CRLF.join(lines)


def _base64_21(prefix: str, data: str) -> str:
    """Format inline base64 data the vCard 2.1 way: indented lines, then a blank line."""
    chunks = [data[i:i + 72] for i in range(0, len(data), 72)] or [""]
    return CRLF.join([prefix + chunks[0], *("  " + chunk for chunk in chunks[1:])]) + CRLF


def _create_vcard_21(contact: Contact) -> str:
    """
    Generate vCard 2.1 format (for legacy Outlook, car kits and feature phones).

    Args:
        contact: Contact object

    Returns:
        vCard 2.1 formatted string
    """
    lines = [
        "BEGIN:VCARD",
        "VERSION:2.1",
    ]

    lines.append(_prop_21("N", ";".join(_escape_21(c) for c in _n_components(contact))))
    lines.append(_prop_21("FN", _normalize_text(contact.get_formatted_name())))

    if contact.nickname:
        lines.append(_prop_21("NICKNAME", _normalize_text(contact.nickname)))

    if contact.gender:
        lines.append(_prop_21("X-GENDER", _normalize_text(contact.gender)))

    for field_name, prop in (("birthday", "BDAY"), ("anniversary", "X-ANNIVERSARY")):
        date = _date(contact, field_name)
        if date and not date.startswith("--"):
            lines.append(f"{prop}:{date}")

    for field_name, prop in (("title", "TITLE"), ("role", "ROLE")):
        value = getattr(contact, field_name)
        if value:
            lines.append(_prop_21(prop, _normalize_text(value)))

    if contact.org:
        lines.append(_prop_21("ORG", _escape_21(contact.org)))

    for value, types in _typed_values(contact, PHONE_TYPES):
        lines.append(f"TEL;{types.replace(',', ';')}:{value}")

    for value, types in _typed_values(contact, EMAIL_TYPES):
        lines.append(f"EMAIL;INTERNET;{types}:{value}")

    for value in contact.values("website"):
        lines.append(f"URL;WORK:{_clean(value)}")

    for adr_type, components in _addresses(contact):
        lines.append(_prop_21(f"ADR;{adr_type}", ";".join(_escape_21(c) for c in components)))

    for field_name, prop in (("photo", "PHOTO"), ("logo", "LOGO")):
        value = getattr(contact, field_name)
        if value:
            media = _parse_media(value, "image/jpeg")
            if media.uri:
                lines.append(f"{prop};VALUE=URL:{media.uri}")
            else:
                prefix = f"{prop};ENCODING=BASE64;{_v3_type(media.media_type)}:"
                lines.append(_base64_21(prefix, media.data))

    if contact.categories:
        lines.append(_prop_21("CATEGORIES", _normalize_text(contact.categories)))

    geo = _geo(contact)
    if geo:
        lines.append(f"GEO:{geo[0]},{geo[1]}")

    if contact.tz:
        # vCard 2.1 TZ only supports UTC offsets
        offset = parse_utc_offset(contact.tz)
        if offset:
            lines.append(f"TZ:{offset[0]}{offset[1]}:{offset[2]}")

    if contact.key:
        if _is_armored_key(contact.key):
            lines.append(_prop_21("KEY;PGP", _normalize_text(contact.key.strip()), force_qp=True))
        else:
            media = _parse_media(contact.key, "application/pgp-keys")
            if media.uri:
                lines.append(f"KEY;VALUE=URL:{media.uri}")
            else:
                prefix = f"KEY;ENCODING=BASE64;{_v3_type(media.media_type)}:"
                lines.append(_base64_21(prefix, media.data))

    for profile in _social_profiles(contact):
        lines.append(f"X-SOCIALPROFILE:{profile}")

    if contact.note:
        lines.append(_prop_21("NOTE", _normalize_text(contact.note)))

    for name, value in contact.extensions.items():
        lines.append(_prop_21(name, _normalize_text(value)))

    lines.append(f"REV:{Contact.generate_rev()}")
    lines.append(f"UID:{contact.generate_uid()}")
    lines.append("END:VCARD")
    return _serialize(lines, fold=False)
