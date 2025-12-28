"""Main csv2vcard functionality."""

from __future__ import annotations

import logging
import warnings
from pathlib import Path

from csv2vcard.create_vcard import create_vcard
from csv2vcard.export_vcard import ensure_export_dir, export_vcard, export_vcards_combined
from csv2vcard.mapping import load_mapping
from csv2vcard.models import VCardVersion
from csv2vcard.parse_csv import find_csv_files, parse_csv

logger = logging.getLogger(__name__)


def csv2vcard(
    csv_filename: str | Path,
    csv_delimiter: str = ",",
    *,
    output_dir: str | Path | None = None,
    version: VCardVersion = VCardVersion.V3_0,
    strict: bool = False,
    single_file: bool = False,
    encoding: str | None = None,
    mapping_file: str | Path | None = None,
    csv_delimeter: str | None = None,  # Legacy parameter name (deprecated)
) -> list[Path]:
    """
    Convert a CSV file or directory to vCard files.

    Args:
        csv_filename: Path to the CSV file or directory containing CSV files
        csv_delimiter: Field delimiter character (default: ",")
        output_dir: Output directory (default: ./export/)
        version: vCard version to generate (default: 3.0)
        strict: Raise errors on validation issues (default: False)
        single_file: Export all contacts to a single .vcf file (default: False)
        encoding: File encoding (auto-detected if None)
        mapping_file: Path to JSON mapping file (uses default if None)
        csv_delimeter: DEPRECATED - use csv_delimiter instead

    Returns:
        List of paths to created vCard files

    Example:
        >>> from csv2vcard import csv2vcard
        >>> csv2vcard("contacts.csv", ",")
        [PosixPath('export/smith_john.vcf'), PosixPath('export/doe_jane.vcf')]
    """
    # Handle deprecated parameter name
    if csv_delimeter is not None:
        warnings.warn(
            "Parameter 'csv_delimeter' is deprecated, use 'csv_delimiter'",
            DeprecationWarning,
            stacklevel=2,
        )
        csv_delimiter = csv_delimeter

    logger.info(f"Converting CSV to vCard: {csv_filename}")

    # Find all CSV files (supports both file and directory input)
    try:
        csv_files = find_csv_files(csv_filename)
    except ValueError as e:
        logger.error(str(e))
        if strict:
            raise
        return []

    # Load mapping
    mapping = load_mapping(mapping_file)

    # Ensure export directory exists
    output_path = Path(output_dir) if output_dir else Path("export")
    ensure_export_dir(output_path)

    # Parse all CSV files and generate vCards
    all_vcards: list[dict[str, str]] = []
    for csv_file in csv_files:
        contacts = parse_csv(
            csv_file,
            csv_delimiter,
            strict=strict,
            encoding=encoding,
            mapping=mapping,
        )
        for contact in contacts:
            vcard = create_vcard(contact, version=version)
            all_vcards.append(vcard)

    if not all_vcards:
        logger.warning("No contacts found to convert")
        return []

    # Export vCards
    created_files: list[Path] = []

    if single_file:
        # Export all to single file
        combined_filename = "contacts.vcf"
        combined_path = output_path / combined_filename
        output_file = export_vcards_combined(all_vcards, combined_path)
        created_files.append(output_file)
    else:
        # Export to separate files
        for vcard in all_vcards:
            output_file = export_vcard(vcard, output_path)
            created_files.append(output_file)

    logger.info(f"Created {len(created_files)} vCard file(s)")
    return created_files


def test_csv2vcard(
    output_dir: str | Path | None = None,
    version: VCardVersion = VCardVersion.V3_0,
) -> None:
    """
    Test csv2vcard with a mock Forrest Gump contact.

    Args:
        output_dir: Output directory (default: ./export/)
        version: vCard version to generate (default: 3.0)
    """
    mock_contact = {
        "last_name": "Gump",
        "first_name": "Forrest",
        "title": "Shrimp Man",
        "org": "Bubba Gump Shrimp Co.",
        "phone": "+49 170 5 25 25 25",
        "email": "forrestgump@example.com",
        "website": "https://www.linkedin.com/in/forrestgump",
        "street": "42 Plantation St.",
        "city": "Baytown",
        "region": "LA",
        "p_code": "30314",
        "country": "United States of America",
        "nickname": "Gumpy",
        "birthday": "1944-06-06",
        "note": "Life is like a box of chocolates.",
    }

    ensure_export_dir(output_dir)
    vcard = create_vcard(mock_contact, version=version)

    # Print vCard for visibility (preserves original behavior)
    print(vcard["output"])

    export_vcard(vcard, output_dir)
