"""CSV parsing for csv2vcard."""

from __future__ import annotations

import csv
import logging
import warnings
from collections.abc import Iterator
from pathlib import Path

from csv2vcard.exceptions import ParseError, ValidationError
from csv2vcard.mapping import DEFAULT_MAPPING, apply_mapping, load_mapping
from csv2vcard.models import Contact
from csv2vcard.validators import validate_contact, validate_csv_file

logger = logging.getLogger(__name__)


def detect_encoding(filepath: Path) -> str:
    """
    Detect the encoding of a file.

    Uses charset_normalizer if available, otherwise falls back to utf-8.

    Args:
        filepath: Path to the file

    Returns:
        Detected encoding name
    """
    try:
        from charset_normalizer import from_path

        result = from_path(filepath).best()
        if result:
            encoding = result.encoding
            logger.debug(f"Detected encoding: {encoding}")
            return encoding
    except ImportError:
        logger.debug("charset_normalizer not installed, using utf-8")
    except Exception as e:
        logger.warning(f"Encoding detection failed: {e}, using utf-8")

    return "utf-8"


def find_csv_files(source: str | Path) -> list[Path]:
    """
    Find CSV files from a file or directory path.

    Args:
        source: Path to a CSV file or directory containing CSV files

    Returns:
        List of CSV file paths

    Raises:
        ValueError: If source doesn't exist or contains no CSV files
    """
    source_path = Path(source)

    if not source_path.exists():
        raise ValueError(f"Source path does not exist: {source_path}")

    if source_path.is_file():
        if source_path.suffix.lower() != ".csv":
            raise ValueError(f"Not a CSV file: {source_path}")
        return [source_path]

    if source_path.is_dir():
        csv_files = sorted(source_path.glob("*.csv"))
        if not csv_files:
            raise ValueError(f"No CSV files found in directory: {source_path}")
        logger.info(f"Found {len(csv_files)} CSV files in {source_path}")
        return csv_files

    raise ValueError(f"Invalid source path: {source_path}")


def parse_csv(
    csv_filename: str | Path,
    csv_delimiter: str = ",",
    *,
    strict: bool = False,
    encoding: str | None = None,
    mapping: dict[str, list[str]] | None = None,
) -> list[dict[str, str]]:
    """
    Parse a CSV file and return a list of contact dictionaries.

    Args:
        csv_filename: Path to the CSV file
        csv_delimiter: Field delimiter character (default: ",")
        strict: If True, raise errors on validation issues
        encoding: File encoding (auto-detected if None)
        mapping: Field mapping (uses default if None)

    Returns:
        List of contact dictionaries with vCard field names

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

    # Detect encoding if not specified
    if encoding is None:
        encoding = detect_encoding(filepath)

    # Use default mapping if not provided
    if mapping is None:
        mapping = DEFAULT_MAPPING

    logger.info(f"Parsing CSV file: {filepath} (encoding: {encoding})")

    try:
        with open(filepath, encoding=encoding, newline="", errors="replace") as f:
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

                # Create raw contact dict from CSV
                raw_contact = dict(zip(header, row))

                # Apply field mapping
                contact = apply_mapping(raw_contact, mapping)

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


def parse_csv_files(
    source: str | Path,
    csv_delimiter: str = ",",
    *,
    strict: bool = False,
    encoding: str | None = None,
    mapping_file: str | Path | None = None,
) -> list[dict[str, str]]:
    """
    Parse one or more CSV files from a file or directory path.

    Args:
        source: Path to a CSV file or directory containing CSV files
        csv_delimiter: Field delimiter character (default: ",")
        strict: If True, raise errors on validation issues
        encoding: File encoding (auto-detected if None)
        mapping_file: Path to JSON mapping file (uses default if None)

    Returns:
        List of all contact dictionaries from all CSV files

    Raises:
        ParseError: If parsing fails (only in strict mode)
        ValueError: If source path is invalid
    """
    csv_files = find_csv_files(source)
    mapping = load_mapping(mapping_file)

    all_contacts: list[dict[str, str]] = []
    for csv_file in csv_files:
        contacts = parse_csv(
            csv_file,
            csv_delimiter,
            strict=strict,
            encoding=encoding,
            mapping=mapping,
        )
        all_contacts.extend(contacts)

    logger.info(f"Total contacts parsed: {len(all_contacts)}")
    return all_contacts


def iter_contacts(
    csv_filename: str | Path,
    csv_delimiter: str = ",",
    *,
    encoding: str | None = None,
    mapping: dict[str, list[str]] | None = None,
) -> Iterator[Contact]:
    """
    Iterate over contacts in a CSV file (memory efficient).

    Args:
        csv_filename: Path to the CSV file
        csv_delimiter: Field delimiter character
        encoding: File encoding (auto-detected if None)
        mapping: Field mapping (uses default if None)

    Yields:
        Contact objects
    """
    for contact_dict in parse_csv(
        csv_filename, csv_delimiter, encoding=encoding, mapping=mapping
    ):
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
