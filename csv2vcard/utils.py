"""Utility functions for csv2vcard."""

from __future__ import annotations

import unicodedata


def strip_accents(text: str) -> str:
    """
    Remove accents/diacritics from text.

    Uses Unicode normalization to decompose characters and then
    removes combining diacritical marks.

    Args:
        text: Input string with potential accents

    Returns:
        String with accents removed

    Examples:
        >>> strip_accents("café")
        'cafe'
        >>> strip_accents("naïve")
        'naive'
        >>> strip_accents("Müller")
        'Muller'
    """
    # Normalize to decomposed form (NFD)
    # This separates base characters from combining diacritical marks
    normalized = unicodedata.normalize("NFD", text)

    # Remove combining diacritical marks (category "Mn")
    stripped = "".join(
        char for char in normalized
        if unicodedata.category(char) != "Mn"
    )

    return stripped


def strip_accents_from_contact(contact: dict[str, str]) -> dict[str, str]:
    """
    Remove accents from all string values in a contact dictionary.

    Args:
        contact: Contact dictionary with field names as keys

    Returns:
        New dictionary with accents stripped from all string values

    Example:
        >>> contact = {"first_name": "José", "last_name": "García"}
        >>> strip_accents_from_contact(contact)
        {'first_name': 'Jose', 'last_name': 'Garcia'}
    """
    return {
        key: strip_accents(value) if isinstance(value, str) else value
        for key, value in contact.items()
    }
