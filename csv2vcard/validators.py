"""Input validation for csv2vcard."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from csv2vcard.exceptions import ValidationError
from csv2vcard.models import REQUIRED_FIELDS

logger = logging.getLogger(__name__)

# Valid vCard 4.0 gender values (single character)
VALID_GENDER_VALUES = frozenset({"M", "F", "O", "N", "U"})

# Email validation regex (RFC 5322 simplified)
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def validate_contact(contact: dict[str, str], strict: bool = False) -> list[str]:
    """
    Validate a contact dictionary.

    Args:
        contact: Dictionary of contact fields
        strict: If True, raise ValidationError on missing required fields

    Returns:
        List of warning messages (empty if valid)

    Raises:
        ValidationError: If strict=True and required fields are missing
    """
    warnings: list[str] = []

    # Check for missing required fields
    missing_required = REQUIRED_FIELDS - set(contact.keys())
    if missing_required:
        msg = f"Missing required fields: {', '.join(sorted(missing_required))}"
        if strict:
            raise ValidationError(msg)
        warnings.append(msg)

    # Check for empty required fields
    for field_name in REQUIRED_FIELDS:
        if field_name in contact and not contact[field_name].strip():
            msg = f"Required field '{field_name}' is empty"
            if strict:
                raise ValidationError(msg)
            warnings.append(msg)

    # Validate email format if provided
    email = contact.get("email", "").strip()
    if email and not validate_email(email):
        warnings.append(f"Invalid email format: {email}")

    # Validate multi-type emails (v0.5.0)
    for email_field in ("email_home", "email_work"):
        email_val = contact.get(email_field, "").strip()
        if email_val and not validate_email(email_val):
            warnings.append(f"Invalid email format in {email_field}: {email_val}")

    # Validate gender (v0.5.0)
    gender = contact.get("gender", "").strip()
    if gender and not validate_gender(gender):
        warnings.append(f"Invalid gender value: {gender}")

    # Validate geo coordinates (v0.5.0)
    geo = contact.get("geo", "").strip()
    if geo and not validate_geo(geo):
        warnings.append(f"Invalid geo coordinates: {geo}")

    return warnings


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address string

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid-email")
        False
    """
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email))


def validate_gender(gender: str) -> bool:
    """
    Validate vCard 4.0 gender value.

    Valid values per RFC 6350:
    - M: Male
    - F: Female
    - O: Other
    - N: None/not applicable
    - U: Unknown

    Also accepts full words for user convenience.

    Args:
        gender: Gender string

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_gender("M")
        True
        >>> validate_gender("Female")
        True
        >>> validate_gender("invalid")
        False
    """
    if not gender:
        return False

    upper = gender.upper()

    # Accept single letter codes
    if upper in VALID_GENDER_VALUES:
        return True

    # Accept common full words
    valid_words = {
        "MALE": True,
        "FEMALE": True,
        "OTHER": True,
        "NONE": True,
        "UNKNOWN": True,
    }
    return upper in valid_words


def validate_geo(geo: str) -> bool:
    """
    Validate geographic coordinates.

    Expected format: "latitude,longitude" where:
    - latitude: -90.0 to 90.0
    - longitude: -180.0 to 180.0

    Args:
        geo: Coordinate string (e.g., "37.386013,-122.082932")

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_geo("37.386013,-122.082932")
        True
        >>> validate_geo("91.0,0.0")
        False
        >>> validate_geo("invalid")
        False
    """
    if not geo:
        return False

    # Allow semicolon separator (vCard 3.0 format) or comma (common format)
    parts = geo.replace(";", ",").split(",")

    if len(parts) != 2:
        return False

    try:
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
    except ValueError:
        return False

    # Check valid ranges
    if not (-90.0 <= lat <= 90.0):
        return False
    return -180.0 <= lon <= 180.0


def validate_csv_file(filepath: Path, strict: bool = False) -> None:
    """
    Validate that a CSV file exists and is readable.

    Args:
        filepath: Path to CSV file
        strict: If True, raise ValidationError on issues

    Raises:
        ValidationError: If file doesn't exist or isn't readable
    """
    if not filepath.exists():
        raise ValidationError(f"CSV file not found: {filepath}")

    if not filepath.is_file():
        raise ValidationError(f"Path is not a file: {filepath}")

    if filepath.suffix.lower() != ".csv":
        msg = f"File does not have .csv extension: {filepath}"
        if strict:
            raise ValidationError(msg)
        logger.warning(msg)


def validate_output_directory(output_dir: Path) -> None:
    """
    Validate output directory path.

    Args:
        output_dir: Path to output directory

    Raises:
        ValidationError: If path exists but is not a directory
    """
    if output_dir.exists() and not output_dir.is_dir():
        raise ValidationError(f"Output path exists but is not a directory: {output_dir}")


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string for use in filenames.

    Args:
        name: Raw string to sanitize

    Returns:
        Sanitized string safe for filesystem use
    """
    # Remove/replace dangerous characters
    safe = re.sub(r"[^\w\-]", "_", name.lower())
    # Remove path traversal attempts
    safe = safe.replace("..", "_").strip("_.")
    return safe or "unknown"
