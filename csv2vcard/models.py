"""Data models for csv2vcard."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class VCardVersion(Enum):
    """Supported vCard versions."""

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
    "photo",  # URL or base64-encoded image
    "logo",   # URL or base64-encoded image
    # New vCard fields (v0.5.0)
    "categories",  # Comma-separated list
    "geo",         # latitude,longitude
    "tz",          # Timezone
    "key",         # Public key URL or base64
    # Other
    "note",
})


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
    birthday: str = ""  # YYYY-MM-DD or YYYYMMDD
    anniversary: str = ""  # YYYY-MM-DD or YYYYMMDD

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
    photo: str = ""  # URL or base64-encoded image
    logo: str = ""   # URL or base64-encoded image

    # New vCard fields (v0.5.0)
    categories: str = ""  # Comma-separated list
    geo: str = ""         # latitude,longitude (e.g., "37.386013,-122.082932")
    tz: str = ""          # Timezone (e.g., "-05:00" or "America/New_York")
    key: str = ""         # Public key URL or base64

    # Other
    note: str = ""

    def __post_init__(self) -> None:
        """Validate and sanitize contact data after initialization."""
        # Strip whitespace from all string fields
        for field_name in ALL_FIELDS:
            value = getattr(self, field_name, "")
            if isinstance(value, str):
                setattr(self, field_name, value.strip())

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Contact:
        """
        Create Contact from dictionary, providing defaults for missing fields.

        Args:
            data: Dictionary with contact field values

        Returns:
            Contact instance
        """
        return cls(
            # Name components
            last_name=data.get("last_name", ""),
            first_name=data.get("first_name", ""),
            middle_name=data.get("middle_name", ""),
            name_prefix=data.get("name_prefix", ""),
            name_suffix=data.get("name_suffix", ""),
            # Basic info
            nickname=data.get("nickname", ""),
            gender=data.get("gender", ""),
            birthday=data.get("birthday", ""),
            anniversary=data.get("anniversary", ""),
            # Contact - single
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            website=data.get("website", ""),
            # Contact - multi-type phone (v0.5.0)
            phone_cell=data.get("phone_cell", ""),
            phone_home=data.get("phone_home", ""),
            phone_work=data.get("phone_work", ""),
            phone_fax=data.get("phone_fax", ""),
            # Contact - multi-type email (v0.5.0)
            email_home=data.get("email_home", ""),
            email_work=data.get("email_work", ""),
            # Organization
            org=data.get("org", ""),
            title=data.get("title", ""),
            role=data.get("role", ""),
            # Address (default/work)
            street=data.get("street", ""),
            city=data.get("city", ""),
            region=data.get("region", ""),
            p_code=data.get("p_code", ""),
            country=data.get("country", ""),
            # Address - home (v0.5.0)
            home_street=data.get("home_street", ""),
            home_city=data.get("home_city", ""),
            home_region=data.get("home_region", ""),
            home_p_code=data.get("home_p_code", ""),
            home_country=data.get("home_country", ""),
            # Media (v0.5.0)
            photo=data.get("photo", ""),
            logo=data.get("logo", ""),
            # New vCard fields (v0.5.0)
            categories=data.get("categories", ""),
            geo=data.get("geo", ""),
            tz=data.get("tz", ""),
            key=data.get("key", ""),
            # Other
            note=data.get("note", ""),
        )

    def to_dict(self) -> dict[str, str]:
        """
        Convert to dictionary for backwards compatibility.

        Returns:
            Dictionary with all contact fields
        """
        return {
            # Name components
            "last_name": self.last_name,
            "first_name": self.first_name,
            "middle_name": self.middle_name,
            "name_prefix": self.name_prefix,
            "name_suffix": self.name_suffix,
            # Basic info
            "nickname": self.nickname,
            "gender": self.gender,
            "birthday": self.birthday,
            "anniversary": self.anniversary,
            # Contact - single
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            # Contact - multi-type phone (v0.5.0)
            "phone_cell": self.phone_cell,
            "phone_home": self.phone_home,
            "phone_work": self.phone_work,
            "phone_fax": self.phone_fax,
            # Contact - multi-type email (v0.5.0)
            "email_home": self.email_home,
            "email_work": self.email_work,
            # Organization
            "org": self.org,
            "title": self.title,
            "role": self.role,
            # Address (default/work)
            "street": self.street,
            "city": self.city,
            "region": self.region,
            "p_code": self.p_code,
            "country": self.country,
            # Address - home (v0.5.0)
            "home_street": self.home_street,
            "home_city": self.home_city,
            "home_region": self.home_region,
            "home_p_code": self.home_p_code,
            "home_country": self.home_country,
            # Media (v0.5.0)
            "photo": self.photo,
            "logo": self.logo,
            # New vCard fields (v0.5.0)
            "categories": self.categories,
            "geo": self.geo,
            "tz": self.tz,
            "key": self.key,
            # Other
            "note": self.note,
        }

    def get_safe_filename(self) -> str:
        """
        Generate a sanitized filename safe for filesystem use.

        Prevents path traversal attacks and removes unsafe characters.

        Returns:
            Safe filename ending in .vcf
        """
        # Remove or replace unsafe characters (keep only alphanumeric, underscore, hyphen)
        safe_last = re.sub(r"[^\w\-]", "_", self.last_name.lower())
        safe_first = re.sub(r"[^\w\-]", "_", self.first_name.lower())

        # Prevent path traversal
        safe_last = safe_last.replace("..", "_").strip("_.")
        safe_first = safe_first.replace("..", "_").strip("_.")

        # Ensure we have something valid
        safe_last = safe_last or "unknown"
        safe_first = safe_first or "contact"

        return f"{safe_last}_{safe_first}.vcf"

    def get_formatted_name(self) -> str:
        """
        Get the formatted full name (FN field).

        Returns:
            Formatted name string
        """
        parts = []
        if self.name_prefix:
            parts.append(self.name_prefix)
        if self.first_name:
            parts.append(self.first_name)
        if self.middle_name:
            parts.append(self.middle_name)
        if self.last_name:
            parts.append(self.last_name)
        if self.name_suffix:
            parts.append(self.name_suffix)
        return " ".join(parts) or "Unknown"

    def generate_uid(self) -> str:
        """
        Generate a unique identifier for this contact.

        Returns:
            UUID string
        """
        return str(uuid.uuid4())

    @staticmethod
    def generate_rev() -> str:
        """
        Generate a revision timestamp (REV field).

        Returns:
            ISO 8601 timestamp string
        """
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


@dataclass
class VCardOutput:
    """Output from vCard generation."""

    filename: str
    output: str
    name: str
    version: VCardVersion = field(default=VCardVersion.V3_0)
