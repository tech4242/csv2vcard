"""Data models for csv2vcard."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class VCardVersion(Enum):
    """Supported vCard versions."""

    V3_0 = "3.0"
    V4_0 = "4.0"


# Required fields that must be present for a valid contact
REQUIRED_FIELDS: frozenset[str] = frozenset({"last_name", "first_name"})

# All supported contact fields
ALL_FIELDS: frozenset[str] = frozenset({
    "last_name",
    "first_name",
    "title",
    "org",
    "phone",
    "email",
    "website",
    "street",
    "city",
    "p_code",
    "country",
})


@dataclass
class Contact:
    """Represents a contact with validation and sanitization."""

    last_name: str
    first_name: str
    title: str = ""
    org: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    street: str = ""
    city: str = ""
    p_code: str = ""
    country: str = ""

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
            last_name=data.get("last_name", ""),
            first_name=data.get("first_name", ""),
            title=data.get("title", ""),
            org=data.get("org", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            website=data.get("website", ""),
            street=data.get("street", ""),
            city=data.get("city", ""),
            p_code=data.get("p_code", ""),
            country=data.get("country", ""),
        )

    def to_dict(self) -> dict[str, str]:
        """
        Convert to dictionary for backwards compatibility.

        Returns:
            Dictionary with all contact fields
        """
        return {
            "last_name": self.last_name,
            "first_name": self.first_name,
            "title": self.title,
            "org": self.org,
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            "street": self.street,
            "city": self.city,
            "p_code": self.p_code,
            "country": self.country,
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


@dataclass
class VCardOutput:
    """Output from vCard generation."""

    filename: str
    output: str
    name: str
    version: VCardVersion = field(default=VCardVersion.V3_0)
