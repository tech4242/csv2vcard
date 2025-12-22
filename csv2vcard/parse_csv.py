"""CSV parsing for csv2vcard."""

from __future__ import annotations

import csv
import logging
import warnings
from collections.abc import Iterator
from pathlib import Path

from csv2vcard.exceptions import ParseError, ValidationError
from csv2vcard.models import Contact
from csv2vcard.validators import validate_contact, validate_csv_file

logger = logging.getLogger(__name__)


def parse_csv(
    csv_filename: str | Path,
    csv_delimiter: str = ",",
    *,
    strict: bool = False,
) -> list[dict[str, str]]:
    """
    Parse a CSV file and return a list of contact dictionaries.

    Args:
        csv_filename: Path to the CSV file
        csv_delimiter: Field delimiter character (default: ",")
        strict: If True, raise errors on validation issues

    Returns:
        List of contact dictionaries

    Raises:
        ParseError: If file cannot be parsed (only in strict mode)
        ValidationError: If strict=True and validation fails
    """
    filepath = Path(csv_filename)

    try:
        validate_csv_file(filepath, strict=strict)
    except ValidationError:
        if strict:
            raise
        logger.error(f"CSV validation failed: {filepath}")
        return []

    logger.info(f"Parsing CSV file: {filepath}")

    try:
        with open(filepath, encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f, delimiter=csv_delimiter)

            try:
                header = next(reader)
            except StopIteration:
                logger.error(f"CSV file is empty: {filepath}")
                if strict:
                    raise ParseError(f"CSV file is empty: {filepath}") from None
                return []

            # Normalize header names (strip whitespace)
            header = [col.strip() for col in header]
            logger.debug(f"CSV headers: {header}")

            contacts: list[dict[str, str]] = []
            for row_num, row in enumerate(reader, start=2):
                if len(row) != len(header):
                    logger.warning(
                        f"Row {row_num} has {len(row)} columns, expected {len(header)}"
                    )
                    continue

                contact = dict(zip(header, row))
                validation_warnings = validate_contact(contact, strict=strict)
                for warning in validation_warnings:
                    logger.warning(f"Row {row_num}: {warning}")

                contacts.append(contact)

            logger.info(f"Parsed {len(contacts)} contacts from CSV")
            return contacts

    except csv.Error as e:
        logger.error(f"CSV parsing error: {e}")
        if strict:
            raise ParseError(f"Failed to parse CSV: {e}") from e
        return []
    except OSError as e:
        logger.error(f"I/O error reading {filepath}: {e}")
        if strict:
            raise ParseError(f"Failed to read CSV file: {e}") from e
        return []


def iter_contacts(
    csv_filename: str | Path,
    csv_delimiter: str = ",",
) -> Iterator[Contact]:
    """
    Iterate over contacts in a CSV file (memory efficient).

    Args:
        csv_filename: Path to the CSV file
        csv_delimiter: Field delimiter character

    Yields:
        Contact objects
    """
    for contact_dict in parse_csv(csv_filename, csv_delimiter):
        yield Contact.from_dict(contact_dict)


# Legacy function signature for backwards compatibility
def _parse_csv_legacy(csv_filename: str, csv_delimeter: str) -> list[dict[str, str]]:
    """
    Legacy wrapper - maintained for backwards compatibility.

    .. deprecated:: 0.3.0
        Use :func:`parse_csv` with csv_delimiter parameter instead.
    """
    warnings.warn(
        "parse_csv with 'csv_delimeter' (typo) is deprecated, use 'csv_delimiter'",
        DeprecationWarning,
        stacklevel=3,
    )
    return parse_csv(csv_filename, csv_delimeter)
