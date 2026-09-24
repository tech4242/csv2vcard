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


def _resolve_encoding(filepath: Path, encoding: str | None) -> str:
    """Pick the encoding to read with, so a UTF-8 byte order mark is always removed."""
    if encoding is None:
        encoding = detect_encoding(filepath)
    # Excel's "CSV UTF-8" export starts with a BOM; "utf-8-sig" strips it
    if encoding.lower().replace("_", "-") in ("utf-8", "utf8", "ascii"):
        return "utf-8-sig"
    return encoding


def _iter_contact_dicts(
    filepath: Path,
    csv_delimiter: str,
    *,
    strict: bool,
    encoding: str | None,
    mapping: dict[str, list[str]] | None,
    keep_unmapped: bool,
) -> Iterator[dict[str, str]]:
    """
    Stream contact dictionaries from a CSV file.

    Raises:
        ValidationError: If the file is invalid (non-strict callers handle this)
        ParseError: On empty files, malformed rows or read errors (strict mode)
    """
    validate_csv_file(filepath, strict=strict)

    encoding = _resolve_encoding(filepath, encoding)

    # Use default mapping if not provided
    if mapping is None:
        mapping = DEFAULT_MAPPING

    logger.info(f"Parsing CSV file: {filepath} (encoding: {encoding})")

    try:
        # Strict mode fails on undecodable bytes instead of silently replacing them
        errors = "strict" if strict else "replace"
        with open(filepath, encoding=encoding, newline="", errors=errors) as f:
            reader = csv.reader(f, delimiter=csv_delimiter)

            try:
                header = next(reader)
            except StopIteration:
                logger.error(f"CSV file is empty: {filepath}")
                if strict:
                    raise ParseError(f"CSV file is empty: {filepath}") from None
                return

            # Normalize header names (strip whitespace and any leftover BOM)
            header = [col.strip().lstrip("\ufeff").strip() for col in header]
            logger.debug(f"CSV headers: {header}")

            count = 0
            for row_num, row in enumerate(reader, start=2):
                if not any(cell.strip() for cell in row):
                    continue  # Skip blank lines

                if len(row) != len(header):
                    msg = f"Row {row_num} has {len(row)} columns, expected {len(header)}"
                    if strict:
                        raise ParseError(f"{filepath}: {msg}")
                    logger.warning(f"{msg}, skipped")
                    continue

                if any("\ufffd" in cell for cell in row):
                    logger.warning(
                        f"Row {row_num} contains bytes that are invalid in {encoding} "
                        "(replaced with U+FFFD); try --encoding"
                    )

                # Create raw contact dict from CSV
                raw_contact = dict(zip(header, row, strict=True))

                # Apply field mapping
                contact = apply_mapping(raw_contact, mapping, keep_unmapped=keep_unmapped)

                validation_warnings = validate_contact(contact, strict=strict)
                for warning in validation_warnings:
                    logger.warning(f"Row {row_num}: {warning}")

                count += 1
                yield contact

            logger.info(f"Parsed {count} contacts from {filepath}")

    except (csv.Error, UnicodeDecodeError) as e:
        logger.error(f"CSV parsing error in {filepath}: {e}")
        if strict:
            raise ParseError(f"Failed to parse CSV: {e}") from e
    except OSError as e:
        logger.error(f"I/O error reading {filepath}: {e}")
        if strict:
            raise ParseError(f"Failed to read CSV file: {e}") from e


def parse_csv(
    csv_filename: str | Path,
    csv_delimiter: str = ",",
    *,
    strict: bool = False,
    encoding: str | None = None,
    mapping: dict[str, list[str]] | None = None,
    keep_unmapped: bool = False,
) -> list[dict[str, str]]:
    """
    Parse a CSV file and return a list of contact dictionaries.

    Args:
        csv_filename: Path to the CSV file
        csv_delimiter: Field delimiter character (default: ",")
        strict: If True, raise errors on validation issues, malformed rows
            and undecodable bytes
        encoding: File encoding (auto-detected if None)
        mapping: Field mapping (uses default if None)
        keep_unmapped: Keep unmapped columns as X- extension properties

    Returns:
        List of contact dictionaries with vCard field names

    Raises:
        ParseError: If file cannot be parsed (only in strict mode)
        ValidationError: If strict=True and validation fails
    """
    return list(iter_contact_dicts(
        csv_filename,
        csv_delimiter,
        strict=strict,
        encoding=encoding,
        mapping=mapping,
        keep_unmapped=keep_unmapped,
    ))


def iter_contact_dicts(
    csv_filename: str | Path,
    csv_delimiter: str = ",",
    *,
    strict: bool = False,
    encoding: str | None = None,
    mapping: dict[str, list[str]] | None = None,
    keep_unmapped: bool = False,
) -> Iterator[dict[str, str]]:
    """
    Iterate over contact dictionaries in a CSV file without loading it all.

    Takes the same arguments as :func:`parse_csv`.

    Yields:
        Contact dictionaries with vCard field names
    """
    filepath = Path(csv_filename)
    try:
        yield from _iter_contact_dicts(
            filepath,
            csv_delimiter,
            strict=strict,
            encoding=encoding,
            mapping=mapping,
            keep_unmapped=keep_unmapped,
        )
    except ValidationError:
        if strict:
            raise
        logger.error(f"CSV validation failed: {filepath}")


def parse_csv_files(
    source: str | Path,
    csv_delimiter: str = ",",
    *,
    strict: bool = False,
    encoding: str | None = None,
    mapping_file: str | Path | None = None,
    keep_unmapped: bool = False,
) -> list[dict[str, str]]:
    """
    Parse one or more CSV files from a file or directory path.

    Args:
        source: Path to a CSV file or directory containing CSV files
        csv_delimiter: Field delimiter character (default: ",")
        strict: If True, raise errors on validation issues
        encoding: File encoding (auto-detected if None)
        mapping_file: Path to JSON mapping file (uses default if None)
        keep_unmapped: Keep unmapped columns as X- extension properties

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
            keep_unmapped=keep_unmapped,
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
    keep_unmapped: bool = False,
) -> Iterator[Contact]:
    """
    Iterate over contacts in a CSV file (memory efficient: rows are streamed).

    Args:
        csv_filename: Path to the CSV file
        csv_delimiter: Field delimiter character
        encoding: File encoding (auto-detected if None)
        mapping: Field mapping (uses default if None)
        keep_unmapped: Keep unmapped columns as X- extension properties

    Yields:
        Contact objects
    """
    for contact_dict in iter_contact_dicts(
        csv_filename,
        csv_delimiter,
        encoding=encoding,
        mapping=mapping,
        keep_unmapped=keep_unmapped,
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
