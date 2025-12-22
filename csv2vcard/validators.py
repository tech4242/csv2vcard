"""Input validation for csv2vcard."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from csv2vcard.exceptions import ValidationError
from csv2vcard.models import REQUIRED_FIELDS

logger = logging.getLogger(__name__)


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
    if email and not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        warnings.append(f"Invalid email format: {email}")

    return warnings


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
