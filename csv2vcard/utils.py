"""Utility functions for csv2vcard."""

from __future__ import annotations

import re
import unicodedata
from datetime import date


def strip_accents(text: str) -> str:
    """
    Remove accents/diacritics from text.

    Uses Unicode normalization to decompose characters and then
    removes combining diacritical marks.

    Args:
        text: Input string with potential accents

    Returns:
        String with accents removed

    Examples:
        >>> strip_accents("café")
        'cafe'
        >>> strip_accents("naïve")
        'naive'
        >>> strip_accents("Müller")
        'Muller'
    """
    # Normalize to decomposed form (NFD)
    # This separates base characters from combining diacritical marks
    normalized = unicodedata.normalize("NFD", text)

    # Remove combining diacritical marks (category "Mn")
    stripped = "".join(
        char for char in normalized
        if unicodedata.category(char) != "Mn"
    )

    return stripped


def strip_accents_from_contact(contact: dict[str, str]) -> dict[str, str]:
    """
    Remove accents from all string values in a contact dictionary.

    Args:
        contact: Contact dictionary with field names as keys

    Returns:
        New dictionary with accents stripped from all string values

    Example:
        >>> contact = {"first_name": "José", "last_name": "García"}
        >>> strip_accents_from_contact(contact)
        {'first_name': 'Jose', 'last_name': 'Garcia'}
    """
    return {
        key: strip_accents(value) if isinstance(value, str) else value
        for key, value in contact.items()
    }


_ISO_DATE = re.compile(r"^(\d{4})[-/.]?(\d{2})[-/.]?(\d{2})$")
_NO_YEAR_DATE = re.compile(r"^--(\d{2})-?(\d{2})$")
_DOTTED_DATE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$")
_SLASHED_DATE = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")
_UTC_OFFSET = re.compile(r"^(?:UTC|GMT)?\s*([+-])(\d{1,2}):?(\d{2})?$", re.IGNORECASE)
_GLOBAL_PHONE = re.compile(r"^\+[\d\s().\-]+$")


def normalize_date(value: str) -> str | None:
    """
    Normalize a date to vCard basic format.

    Accepts ISO dates (1944-06-06, 19440606, 1944/06/06), dates without a
    year (--06-06), European dotted dates (06.06.1944) and slashed dates
    when the day/month order is unambiguous (13/06/1944, 06/13/1944).
    A time part after "T" or a space is ignored.

    Args:
        value: Raw date string

    Returns:
        "YYYYMMDD", "--MMDD" for dates without a year, or None if the value
        cannot be interpreted unambiguously

    Examples:
        >>> normalize_date("1944-06-06")
        '19440606'
        >>> normalize_date("--12-24")
        '--1224'
        >>> normalize_date("06/06/1944") is None
        True
    """
    value = re.split(r"[T ]", value.strip(), maxsplit=1)[0]

    if match := _NO_YEAR_DATE.match(value):
        month, day = int(match[1]), int(match[2])
        # 2000 is a leap year, so --0229 is accepted
        return f"--{month:02d}{day:02d}" if _is_valid_date(2000, month, day) else None

    if match := _ISO_DATE.match(value):
        year, month, day = int(match[1]), int(match[2]), int(match[3])
    elif match := _DOTTED_DATE.match(value):
        day, month, year = int(match[1]), int(match[2]), int(match[3])
    elif match := _SLASHED_DATE.match(value):
        first, second, year = int(match[1]), int(match[2]), int(match[3])
        if first > 12 >= second:
            day, month = first, second
        elif second > 12 >= first:
            month, day = first, second
        elif first == second:
            day = month = first
        else:
            return None  # Ambiguous: could be MM/DD or DD/MM
    else:
        return None

    return f"{year:04d}{month:02d}{day:02d}" if _is_valid_date(year, month, day) else None


def _is_valid_date(year: int, month: int, day: int) -> bool:
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def parse_geo(value: str) -> tuple[str, str] | None:
    """
    Parse geographic coordinates.

    Accepts "lat,lon", "lat;lon" and "geo:lat,lon".

    Args:
        value: Coordinate string

    Returns:
        (latitude, longitude) as strings, or None if invalid or out of range
    """
    value = value.strip()
    if value.lower().startswith("geo:"):
        value = value[4:].split(";", 1)[0]
    parts = [p.strip() for p in value.replace(";", ",").split(",")]
    if len(parts) != 2:
        return None
    try:
        lat, lon = float(parts[0]), float(parts[1])
    except ValueError:
        return None
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return None
    return parts[0], parts[1]


def parse_utc_offset(value: str) -> tuple[str, str, str] | None:
    """
    Parse a UTC offset such as "-05:00", "+0530" or "UTC+1".

    Args:
        value: Timezone string

    Returns:
        (sign, hours, minutes) zero-padded, or None if not a UTC offset
    """
    match = _UTC_OFFSET.match(value.strip())
    if not match:
        return None
    hours, minutes = int(match[2]), int(match[3] or 0)
    if hours > 14 or minutes > 59:
        return None
    return match[1], f"{hours:02d}", f"{minutes:02d}"


def phone_to_tel_uri(value: str) -> str | None:
    """
    Convert an international phone number to an RFC 3966 tel: URI.

    Only global numbers (starting with "+") can be expressed as a tel: URI
    without a phone-context, so local numbers return None.

    Args:
        value: Phone number, e.g. "+49 170 5 25 25 25"

    Returns:
        URI such as "tel:+49-170-5-25-25-25", or None

    Examples:
        >>> phone_to_tel_uri("+1 (555) 123-4567")
        'tel:+1-555-123-4567'
        >>> phone_to_tel_uri("0170 123") is None
        True
    """
    value = value.strip()
    if not _GLOBAL_PHONE.match(value) or not any(c.isdigit() for c in value):
        return None
    digits = re.sub(r"[\s().\-]+", "-", value[1:]).strip("-")
    return f"tel:+{digits}"
