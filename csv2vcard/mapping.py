"""CSV to vCard field mapping for csv2vcard."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from csv2vcard.models import ALL_FIELDS

logger = logging.getLogger(__name__)

# Default mapping: vCard field -> list of possible CSV column names
DEFAULT_MAPPING: dict[str, list[str]] = {
    # Name components
    "last_name": ["last_name", "lastname", "last", "surname", "family_name", "familyname"],
    "first_name": ["first_name", "firstname", "first", "given_name", "givenname"],
    "middle_name": ["middle_name", "middlename", "middle", "second_name"],
    "name_prefix": ["name_prefix", "prefix", "title_prefix", "honorific_prefix", "salutation"],
    "name_suffix": ["name_suffix", "suffix", "honorific_suffix", "generational"],
    # Basic info
    "nickname": ["nickname", "nick", "alias", "aka"],
    "gender": ["gender", "sex"],
    "birthday": ["birthday", "birthdate", "birth_date", "dob", "date_of_birth", "bday"],
    "anniversary": ["anniversary", "wedding_anniversary", "wedding_date"],
    # Contact
    "phone": ["phone", "telephone", "tel", "mobile", "cell", "cellphone", "phone_number"],
    "email": ["email", "e-mail", "email_address", "mail"],
    "website": ["website", "url", "web", "homepage", "webpage", "site"],
    # Organization
    "org": ["org", "organization", "organisation", "company", "employer", "business"],
    "title": ["title", "job_title", "jobtitle", "position"],
    "role": ["role", "job_role", "function", "occupation"],
    # Address
    "street": ["street", "street_address", "address", "address1", "street1"],
    "city": ["city", "locality", "town"],
    "region": ["region", "state", "province", "county", "state_province"],
    "p_code": ["p_code", "postal_code", "postalcode", "zip", "zipcode", "zip_code", "postcode"],
    "country": ["country", "country_name", "nation"],
    # Other
    "note": ["note", "notes", "comment", "comments", "remarks", "description"],
}


def load_mapping(mapping_path: str | Path | None = None) -> dict[str, list[str]]:
    """
    Load a field mapping from a JSON file or return the default mapping.

    Args:
        mapping_path: Path to JSON mapping file, or None for default

    Returns:
        Dictionary mapping vCard fields to lists of possible CSV column names

    Raises:
        ValueError: If mapping file is invalid
    """
    if mapping_path is None:
        logger.debug("Using default field mapping")
        return DEFAULT_MAPPING.copy()

    path = Path(mapping_path)
    if not path.exists():
        raise ValueError(f"Mapping file not found: {path}")

    logger.info(f"Loading custom mapping from: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            custom_mapping = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in mapping file: {e}") from e

    # Validate mapping structure
    if not isinstance(custom_mapping, dict):
        raise ValueError("Mapping must be a JSON object")

    # Merge with defaults: custom overrides default
    merged = DEFAULT_MAPPING.copy()

    for field, columns in custom_mapping.items():
        if field not in ALL_FIELDS:
            logger.warning(f"Unknown field in mapping: {field}")
            continue

        if isinstance(columns, str):
            # Allow single string as shorthand
            columns = [columns]
        elif not isinstance(columns, list):
            raise ValueError(f"Mapping for '{field}' must be a string or list of strings")

        merged[field] = columns

    return merged


def apply_mapping(
    row: dict[str, str],
    mapping: dict[str, list[str]],
) -> dict[str, str]:
    """
    Apply field mapping to a CSV row, converting column names to vCard field names.

    Args:
        row: Dictionary with CSV column names as keys
        mapping: Field mapping (vCard field -> list of CSV column names)

    Returns:
        Dictionary with vCard field names as keys
    """
    result: dict[str, str] = {}

    # Normalize row keys for case-insensitive matching
    normalized_row = {k.lower().strip(): v for k, v in row.items()}

    for vcard_field, csv_columns in mapping.items():
        for csv_col in csv_columns:
            csv_col_lower = csv_col.lower().strip()
            if csv_col_lower in normalized_row:
                value = normalized_row[csv_col_lower]
                if value:  # Only set if non-empty
                    result[vcard_field] = value
                    break  # First match wins

    return result


def create_example_mapping() -> str:
    """
    Create an example mapping JSON for documentation purposes.

    Returns:
        JSON string with example mapping
    """
    example = {
        "first_name": ["First Name", "Given Name", "FirstName"],
        "last_name": ["Last Name", "Surname", "FamilyName"],
        "email": ["Email", "E-Mail", "email_address"],
        "phone": ["Phone", "Mobile", "Tel", "Telephone"],
        "org": ["Company", "Organization", "Employer"],
        "title": ["Job Title", "Position", "Title"],
        "street": ["Address", "Street", "Street Address"],
        "city": ["City", "Town", "Locality"],
        "region": ["State", "Province", "Region"],
        "p_code": ["Zip", "Postal Code", "ZIP Code", "Postcode"],
        "country": ["Country", "Nation"],
        "birthday": ["Birthday", "Birth Date", "DOB"],
        "note": ["Notes", "Comments", "Remarks"],
    }
    return json.dumps(example, indent=2)
