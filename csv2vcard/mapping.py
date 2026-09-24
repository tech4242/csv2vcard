"""CSV to vCard field mapping for csv2vcard."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from csv2vcard.models import ALL_FIELDS, EXTENSION_PREFIX, MULTI_VALUE_FIELDS

logger = logging.getLogger(__name__)

# Default mapping: vCard field -> list of possible CSV column names.
# Column names are matched case-insensitively, treating spaces, hyphens and
# underscores alike ("First Name" matches "first_name").
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
    "pronouns": ["pronouns", "pronoun"],
    "language": ["language", "lang", "preferred_language"],
    # Contact - single (backwards compatible)
    "phone": ["phone", "telephone", "tel", "phone_number"],
    "email": ["email", "e-mail", "email_address", "e-mail_address", "mail"],
    "website": ["website", "url", "web", "homepage", "webpage", "web_page", "site"],
    # Contact - multi-type phone (v0.5.0)
    "phone_cell": [
        "phone_cell", "cell_phone", "mobile_phone", "mobile", "cell", "cellphone",
    ],
    "phone_home": ["phone_home", "home_phone", "personal_phone"],
    "phone_work": ["phone_work", "work_phone", "business_phone", "office_phone"],
    "phone_fax": ["phone_fax", "fax", "fax_number", "business_fax"],
    # Contact - multi-type email (v0.5.0)
    "email_home": ["email_home", "home_email", "personal_email"],
    "email_work": ["email_work", "work_email", "business_email", "office_email"],
    # Social profile URL - RFC 9554 (v0.6.0)
    "social_profile": ["social_profile", "social_profiles", "social", "social_url", "profile_url"],
    # Organization
    "org": ["org", "organization", "organisation", "company", "employer", "business"],
    "title": ["title", "job_title", "jobtitle", "position"],
    "role": ["role", "job_role", "function", "occupation"],
    # Address (default/work)
    "street": [
        "street", "street_address", "address", "address1", "street1", "work_street",
        "business_street",
    ],
    "city": ["city", "locality", "town", "work_city", "business_city"],
    "region": [
        "region", "state", "province", "county", "state_province", "work_state",
        "business_state",
    ],
    "p_code": [
        "p_code", "postal_code", "postalcode", "zip", "zipcode", "zip_code", "postcode",
        "business_postal_code",
    ],
    "country": [
        "country", "country_name", "nation", "work_country", "business_country",
        "business_country_region",
    ],
    # Address - home (v0.5.0)
    # Support both "home_street" and "street_home" naming conventions
    "home_street": [
        "home_street", "street_home", "home_address", "personal_street", "home_street_address",
    ],
    "home_city": ["home_city", "city_home", "personal_city"],
    "home_region": [
        "home_region", "region_home", "home_state", "state_home", "home_province", "personal_state",
    ],
    "home_p_code": [
        "home_p_code", "p_code_home", "home_postal_code", "home_zip", "zip_home", "personal_zip",
    ],
    "home_country": [
        "home_country", "country_home", "personal_country", "home_country_region",
    ],
    # Media (v0.5.0)
    "photo": ["photo", "picture", "image", "avatar", "photo_url"],
    "logo": ["logo", "company_logo", "org_logo", "logo_url"],
    # New vCard fields (v0.5.0)
    "categories": ["categories", "category", "tags", "groups", "labels"],
    "geo": ["geo", "coordinates", "lat_lon", "latlng", "gps"],
    "tz": ["tz", "timezone", "time_zone"],
    "key": ["key", "public_key", "pgp_key", "gpg_key"],
    # Other
    "note": ["note", "notes", "comment", "comments", "remarks", "description"],
    "uid": ["uid", "contact_id", "external_id"],
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


def normalize_column_name(name: str) -> str:
    """
    Normalize a CSV column name for matching.

    Lower-cases the name and collapses runs of spaces, hyphens and other
    punctuation into single underscores.

    Examples:
        >>> normalize_column_name(" First Name ")
        'first_name'
        >>> normalize_column_name("E-mail 2")
        'e_mail_2'
    """
    return re.sub(r"[^0-9a-z]+", "_", name.strip().lower()).strip("_")


def apply_mapping(
    row: dict[str, str],
    mapping: dict[str, list[str]],
    *,
    keep_unmapped: bool = False,
) -> dict[str, str]:
    """
    Apply field mapping to a CSV row, converting column names to vCard field names.

    Single-value fields take the first matching non-empty column. Multi-value
    fields (phones, emails, websites, social profiles) collect every matching
    column, including numbered variants such as "email_2" or "Phone 3"; the
    extra values are returned as "<field>_2", "<field>_3", ...

    Args:
        row: Dictionary with CSV column names as keys
        mapping: Field mapping (vCard field -> list of CSV column names)
        keep_unmapped: Also return non-empty columns that match no field,
            as extension properties ("Department" -> "X-DEPARTMENT")

    Returns:
        Dictionary with vCard field names as keys
    """
    result: dict[str, str] = {}

    # Normalize row keys for case- and separator-insensitive matching
    normalized_row: dict[str, str] = {}
    for key, value in row.items():
        normalized_row.setdefault(normalize_column_name(key), value)
    consumed: set[str] = set()

    for vcard_field, csv_columns in mapping.items():
        aliases = [normalize_column_name(c) for c in csv_columns]
        consumed.update(a for a in aliases if a in normalized_row)

        if vcard_field in MULTI_VALUE_FIELDS:
            values = _collect_values(normalized_row, aliases, consumed)
            if values:
                result[vcard_field] = values[0]
                for index, value in enumerate(values[1:], start=2):
                    result[f"{vcard_field}_{index}"] = value
            continue

        for alias in aliases:
            value = normalized_row.get(alias, "").strip()
            if value:  # Only set if non-empty
                result[vcard_field] = value
                break  # First match wins

    if keep_unmapped:
        for column, value in normalized_row.items():
            prop = EXTENSION_PREFIX + column.upper().replace("_", "-")
            if column not in consumed and value.strip() and column:
                result.setdefault(prop, value.strip())

    return result


def _collect_values(
    normalized_row: dict[str, str],
    aliases: list[str],
    consumed: set[str],
) -> list[str]:
    """Collect all values of a multi-value field: exact aliases first, then numbered columns."""
    values = [normalized_row[a].strip() for a in aliases if a in normalized_row]

    numbered: list[tuple[int, str]] = []
    for alias in aliases:
        pattern = re.compile(re.escape(alias) + r"_?(\d+)")
        for column, value in normalized_row.items():
            match = pattern.fullmatch(column)
            if match and column not in consumed:
                consumed.add(column)
                numbered.append((int(match[1]), value.strip()))
    values.extend(value for _, value in sorted(numbered, key=lambda item: item[0]))

    return list(dict.fromkeys(v for v in values if v))


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
