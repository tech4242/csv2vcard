"""Custom exceptions for csv2vcard."""

from __future__ import annotations


class CSV2VCardError(Exception):
    """Base exception for csv2vcard errors."""

    pass


class ValidationError(CSV2VCardError):
    """Raised when contact or input validation fails."""

    pass


class ParseError(CSV2VCardError):
    """Raised when CSV parsing fails."""

    pass


class ExportError(CSV2VCardError):
    """Raised when vCard export fails."""

    pass
