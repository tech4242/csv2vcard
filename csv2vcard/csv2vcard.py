"""Main csv2vcard functionality."""

from __future__ import annotations

import logging
import warnings
from pathlib import Path

from csv2vcard.create_vcard import create_vcard
from csv2vcard.export_vcard import ensure_export_dir, export_vcard
from csv2vcard.models import VCardVersion
from csv2vcard.parse_csv import parse_csv

logger = logging.getLogger(__name__)


def csv2vcard(
    csv_filename: str | Path,
    csv_delimiter: str = ",",
    *,
    output_dir: str | Path | None = None,
    version: VCardVersion = VCardVersion.V3_0,
    strict: bool = False,
    csv_delimeter: str | None = None,  # Legacy parameter name (deprecated)
) -> list[Path]:
    """
    Convert a CSV file to vCard files.

    Args:
        csv_filename: Path to the CSV file
        csv_delimiter: Field delimiter character (default: ",")
        output_dir: Output directory (default: ./export/)
        version: vCard version to generate (default: 3.0)
        strict: Raise errors on validation issues (default: False)
        csv_delimeter: DEPRECATED - use csv_delimiter instead

    Returns:
        List of paths to created vCard files

    Example:
        >>> from csv2vcard import csv2vcard
        >>> csv2vcard.csv2vcard("contacts.csv", ",")
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

    # Ensure export directory exists
    ensure_export_dir(output_dir)

    # Parse CSV
    contacts = parse_csv(csv_filename, csv_delimiter, strict=strict)

    # Generate and export vCards
    created_files: list[Path] = []
    for contact in contacts:
        vcard = create_vcard(contact, version=version)
        output_path = export_vcard(vcard, output_dir)
        created_files.append(output_path)

    logger.info(f"Created {len(created_files)} vCard files")
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
        "p_code": "30314",
        "country": "United States of America",
    }

    ensure_export_dir(output_dir)
    vcard = create_vcard(mock_contact, version=version)

    # Print vCard for visibility (preserves original behavior)
    print(vcard["output"])

    export_vcard(vcard, output_dir)
