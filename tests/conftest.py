"""Pytest fixtures for csv2vcard tests."""

from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_contact() -> dict[str, str]:
    """Return a sample contact dictionary with all fields populated."""
    return {
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


@pytest.fixture
def minimal_contact() -> dict[str, str]:
    """Return a minimal contact with only required fields."""
    return {
        "last_name": "Doe",
        "first_name": "John",
    }


@pytest.fixture
def sample_csv(temp_dir: Path) -> Path:
    """Create a sample CSV file with valid contacts."""
    csv_content = """last_name,first_name,title,org,phone,email,street,city,p_code,country
Gump,Forrest,Shrimp Man,Bubba Gump,+1234567890,forrest@ex.com,42 Main,Baytown,30314,USA
Doe,Jane,Developer,Tech Corp,+0987654321,jane@ex.com,123 Main St.,NYC,10001,USA
"""
    csv_path = temp_dir / "contacts.csv"
    csv_path.write_text(csv_content, encoding="utf-8")
    return csv_path


@pytest.fixture
def unicode_csv(temp_dir: Path) -> Path:
    """Create a CSV file with Unicode characters."""
    csv_content = """last_name,first_name,title,org,phone,email,website,street,city,p_code,country
Mueller,Hans,Ingenieur,Firma GmbH,+49123456,hans@ex.de,https://ex.de,Strasse 1,Munchen,80331,DE
Dupont,Marie,Directrice,Societe SA,+33123456,marie@ex.fr,https://ex.fr,Rue Paix,Paris,75001,FR
"""
    csv_path = temp_dir / "unicode_contacts.csv"
    csv_path.write_text(csv_content, encoding="utf-8")
    return csv_path


@pytest.fixture
def semicolon_csv(temp_dir: Path) -> Path:
    """Create a CSV file with semicolon delimiter."""
    csv_content = """last_name;first_name;title;org;phone;email;website;street;city;p_code;country
Smith;John;CEO;Acme Inc;+1555123;john@acme.com;https://acme.com;100 Main St;Boston;02101;USA
"""
    csv_path = temp_dir / "semicolon.csv"
    csv_path.write_text(csv_content, encoding="utf-8")
    return csv_path


@pytest.fixture
def malformed_csv(temp_dir: Path) -> Path:
    """Create a malformed CSV file with mismatched columns."""
    csv_content = """last_name,first_name,title
Gump,Forrest
Missing,Fields,Too,Many,Extra,Columns
"""
    csv_path = temp_dir / "malformed.csv"
    csv_path.write_text(csv_content, encoding="utf-8")
    return csv_path


@pytest.fixture
def empty_csv(temp_dir: Path) -> Path:
    """Create an empty CSV file."""
    csv_path = temp_dir / "empty.csv"
    csv_path.write_text("", encoding="utf-8")
    return csv_path


@pytest.fixture
def header_only_csv(temp_dir: Path) -> Path:
    """Create a CSV file with only headers."""
    csv_path = temp_dir / "header_only.csv"
    csv_path.write_text("last_name,first_name,title\n", encoding="utf-8")
    return csv_path
