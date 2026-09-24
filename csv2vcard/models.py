"""Data models for csv2vcard."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from enum import Enum


class VCardVersion(Enum):
    """Supported vCard versions."""

    V2_1 = "2.1"
    V3_0 = "3.0"
    V4_0 = "4.0"


# Required fields that must be present for a valid contact
REQUIRED_FIELDS: frozenset[str] = frozenset({"last_name", "first_name"})

# All supported contact fields (v0.5.0 expanded)
ALL_FIELDS: frozenset[str] = frozenset({
    # Name components
    "last_name",
    "first_name",
    "middle_name",
    "name_prefix",
    "name_suffix",
    # Basic info
    "nickname",
    "gender",
    "birthday",
    "anniversary",
    "pronouns",   # RFC 9554 (v0.6.0)
    "language",   # Preferred language, e.g. "en" (v0.6.0)
    # Contact - single (backwards compatible)
    "phone",
    "email",
    "website",
    # Contact - multi-type phone (v0.5.0)
    "phone_cell",
    "phone_home",
    "phone_work",
    "phone_fax",
    # Contact - multi-type email (v0.5.0)
    "email_home",
    "email_work",
    # Social profile URL - RFC 9554 (v0.6.0)
    "social_profile",
    # Organization
    "org",
    "title",
    "role",
    # Address (default/work)
    "street",
    "city",
    "region",
    "p_code",
    "country",
    # Address - home (v0.5.0)
    "home_street",
    "home_city",
    "home_region",
    "home_p_code",
    "home_country",
    # Media (v0.5.0)
    "photo",  # URL, data: URI or base64-encoded image
    "logo",   # URL, data: URI or base64-encoded image
    # New vCard fields (v0.5.0)
    "categories",  # Comma-separated list
    "geo",         # latitude,longitude
    "tz",          # Timezone
    "key",         # Public key URL or base64
    # Other
    "note",
    "uid",  # Stable identifier from the source system (v0.6.0)
})

# Fields that may hold several values (v0.6.0). Extra values are passed in
# contact dicts as "<field>_2", "<field>_3", ... (e.g. "email_2").
MULTI_VALUE_FIELDS: frozenset[str] = frozenset({
    "phone",
    "phone_cell",
    "phone_home",
    "phone_work",
    "phone_fax",
    "email",
    "email_home",
    "email_work",
    "website",
    "social_profile",
})

# Prefix marking unmapped CSV columns passed through as vCard extension properties
EXTENSION_PREFIX = "X-"

_NUMBERED_KEY = re.compile(r"^(?P<field>[a-z_]+)_(?P<index>\d+)$")

# Namespace for deterministic UIDs, so re-converting the same CSV yields the same UIDs
UID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/tech4242/csv2vcard")


@dataclass
class Contact:
    """Represents a contact with validation and sanitization."""

    # Name components (N field)
    last_name: str = ""
    first_name: str = ""
    middle_name: str = ""
    name_prefix: str = ""  # e.g., "Mr.", "Dr."
    name_suffix: str = ""  # e.g., "Jr.", "III"

    # Basic info
    nickname: str = ""
    gender: str = ""  # M, F, O, N, U or full words
    birthday: str = ""  # YYYY-MM-DD, YYYYMMDD, --MM-DD, DD.MM.YYYY, ...
    anniversary: str = ""  # same formats as birthday
    pronouns: str = ""  # e.g., "they/them" (v0.6.0)
    language: str = ""  # e.g., "en", "de-AT" (v0.6.0)

    # Contact - single (backwards compatible)
    phone: str = ""
    email: str = ""
    website: str = ""

    # Contact - multi-type phone (v0.5.0)
    phone_cell: str = ""
    phone_home: str = ""
    phone_work: str = ""
    phone_fax: str = ""

    # Contact - multi-type email (v0.5.0)
    email_home: str = ""
    email_work: str = ""

    # Social profile URL (v0.6.0)
    social_profile: str = ""

    # Organization
    org: str = ""
    title: str = ""
    role: str = ""

    # Address (default/work ADR field)
    street: str = ""
    city: str = ""
    region: str = ""  # state/province
    p_code: str = ""
    country: str = ""

    # Address - home (v0.5.0)
    home_street: str = ""
    home_city: str = ""
    home_region: str = ""
    home_p_code: str = ""
    home_country: str = ""

    # Media (v0.5.0)
    photo: str = ""  # URL, data: URI or base64-encoded image
    logo: str = ""   # URL, data: URI or base64-encoded image

    # New vCard fields (v0.5.0)
    categories: str = ""  # Comma-separated list
    geo: str = ""         # latitude,longitude (e.g., "37.386013,-122.082932")
    tz: str = ""          # Timezone (e.g., "-05:00" or "America/New_York")
    key: str = ""         # Public key URL or base64

    # Other
    note: str = ""
    uid: str = ""  # Source-system identifier; hashed into a stable UUID (v0.6.0)

    # Additional values for MULTI_VALUE_FIELDS, e.g. {"email": ["second@example.com"]}
    extra_values: dict[str, list[str]] = field(default_factory=dict)
    # Extension properties, e.g. {"X-DEPARTMENT": "Sales"}
    extensions: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and sanitize contact data after initialization."""
        # Strip whitespace from all string fields
        for field_name in ALL_FIELDS:
            value = getattr(self, field_name, "")
            if isinstance(value, str):
                setattr(self, field_name, value.strip())
        self.extra_values = {
            name: [v.strip() for v in values if v.strip()]
            for name, values in self.extra_values.items()
        }
        self.extensions = {
            name: value.strip() for name, value in self.extensions.items() if value.strip()
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Contact:
        """
        Create Contact from dictionary, providing defaults for missing fields.

        Besides the standard field names, the dictionary may contain numbered
        keys for multi-value fields ("email_2", "phone_cell_3", ...) and
        extension properties ("X-DEPARTMENT").

        Args:
            data: Dictionary with contact field values

        Returns:
            Contact instance
        """
        values = {name: data.get(name, "") for name in ALL_FIELDS}

        numbered: dict[str, list[tuple[int, str]]] = {}
        extensions: dict[str, str] = {}
        for key, value in data.items():
            if key.startswith(EXTENSION_PREFIX):
                extensions[key] = value
                continue
            match = _NUMBERED_KEY.match(key)
            if match and match["field"] in MULTI_VALUE_FIELDS:
                numbered.setdefault(match["field"], []).append((int(match["index"]), value))

        extra_values = {
            name: [value for _, value in sorted(items)] for name, items in numbered.items()
        }
        return cls(**values, extra_values=extra_values, extensions=extensions)

    def to_dict(self) -> dict[str, str]:
        """
        Convert to dictionary for backwards compatibility.

        Returns:
            Dictionary with all contact fields (plus numbered and extension keys)
        """
        result = {f.name: getattr(self, f.name) for f in fields(self) if f.name in ALL_FIELDS}
        for name, extra in self.extra_values.items():
            for index, value in enumerate(extra, start=2):
                result[f"{name}_{index}"] = value
        result.update(self.extensions)
        return result

    def values(self, field_name: str) -> list[str]:
        """
        Get all non-empty values of a field (primary value first).

        Args:
            field_name: Contact field name

        Returns:
            List of values, deduplicated in order
        """
        candidates = [getattr(self, field_name), *self.extra_values.get(field_name, [])]
        return list(dict.fromkeys(v for v in candidates if v))

    @property
    def is_organization(self) -> bool:
        """True if the contact represents an organization rather than a person."""
        return bool(self.org) and not (self.first_name or self.middle_name or self.last_name)

    def get_safe_filename(self) -> str:
        """
        Generate a sanitized filename safe for filesystem use.

        Prevents path traversal attacks and removes unsafe characters.

        Returns:
            Safe filename ending in .vcf
        """
        if self.is_organization:
            return f"{_sanitize_filename_part(self.org) or 'unknown'}.vcf"

        # Ensure we have something valid
        safe_last = _sanitize_filename_part(self.last_name) or "unknown"
        safe_first = _sanitize_filename_part(self.first_name) or "contact"

        return f"{safe_last}_{safe_first}.vcf"

    def get_formatted_name(self) -> str:
        """
        Get the formatted full name (FN field).

        Returns:
            Formatted name string
        """
        parts = [
            self.name_prefix,
            self.first_name,
            self.middle_name,
            self.last_name,
            self.name_suffix,
        ]
        return " ".join(p for p in parts if p) or self.org or "Unknown"

    def generate_uid(self) -> str:
        """
        Generate a stable unique identifier for this contact.

        Uses the ``uid`` field when set (kept as-is if it is a UUID, otherwise
        hashed into one). Without it, the UID is derived from the name,
        organization and primary email, so converting the same CSV again
        yields the same UIDs and re-imports update instead of duplicating.

        Returns:
            UUID string
        """
        if self.uid:
            try:
                return str(uuid.UUID(self.uid))
            except ValueError:
                return str(uuid.uuid5(UID_NAMESPACE, f"uid:{self.uid}"))

        emails = self.values("email") + self.values("email_work") + self.values("email_home")
        identity = "|".join(
            part.casefold()
            for part in (
                self.first_name,
                self.middle_name,
                self.last_name,
                self.org,
                emails[0] if emails else "",
            )
        )
        return str(uuid.uuid5(UID_NAMESPACE, f"contact:{identity}"))

    @staticmethod
    def generate_rev() -> str:
        """
        Generate a revision timestamp (REV field).

        Returns:
            ISO 8601 timestamp string
        """
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sanitize_filename_part(value: str) -> str:
    """Keep only alphanumerics, underscores and hyphens; prevent path traversal."""
    safe = re.sub(r"[^\w\-]", "_", value.lower())
    return safe.replace("..", "_").strip("_.")


@dataclass
class VCardOutput:
    """Output from vCard generation."""

    filename: str
    output: str
    name: str
    version: VCardVersion = field(default=VCardVersion.V3_0)
