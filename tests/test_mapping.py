"""Tests for field mapping functionality."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from csv2vcard.mapping import (
    DEFAULT_MAPPING,
    apply_mapping,
    create_example_mapping,
    load_mapping,
)


class TestLoadMapping:
    """Test suite for load_mapping function."""

    def test_load_default_mapping(self) -> None:
        """Test loading default mapping when no file provided."""
        mapping = load_mapping(None)

        assert "first_name" in mapping
        assert "last_name" in mapping
        assert "email" in mapping
        assert isinstance(mapping["first_name"], list)

    def test_load_custom_mapping(self, temp_dir: Path) -> None:
        """Test loading custom mapping from JSON file."""
        custom_mapping = {
            "first_name": ["Given Name", "FirstName"],
            "email": ["EmailAddress"],
        }
        mapping_file = temp_dir / "mapping.json"
        mapping_file.write_text(json.dumps(custom_mapping))

        mapping = load_mapping(mapping_file)

        assert mapping["first_name"] == ["Given Name", "FirstName"]
        assert mapping["email"] == ["EmailAddress"]
        # Default fields should still be present
        assert "last_name" in mapping

    def test_load_mapping_single_string(self, temp_dir: Path) -> None:
        """Test that single string values are converted to lists."""
        custom_mapping = {
            "first_name": "GivenName",  # Single string
        }
        mapping_file = temp_dir / "mapping.json"
        mapping_file.write_text(json.dumps(custom_mapping))

        mapping = load_mapping(mapping_file)

        assert mapping["first_name"] == ["GivenName"]

    def test_load_mapping_nonexistent_file(self, temp_dir: Path) -> None:
        """Test error when mapping file doesn't exist."""
        with pytest.raises(ValueError, match="not found"):
            load_mapping(temp_dir / "nonexistent.json")

    def test_load_mapping_invalid_json(self, temp_dir: Path) -> None:
        """Test error when mapping file contains invalid JSON."""
        mapping_file = temp_dir / "invalid.json"
        mapping_file.write_text("not valid json")

        with pytest.raises(ValueError, match="Invalid JSON"):
            load_mapping(mapping_file)

    def test_load_mapping_invalid_structure(self, temp_dir: Path) -> None:
        """Test error when mapping is not an object."""
        mapping_file = temp_dir / "invalid.json"
        mapping_file.write_text(json.dumps(["list", "not", "object"]))

        with pytest.raises(ValueError, match="must be a JSON object"):
            load_mapping(mapping_file)


class TestApplyMapping:
    """Test suite for apply_mapping function."""

    def test_apply_default_mapping(self) -> None:
        """Test applying default mapping to a row."""
        row = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
        }
        result = apply_mapping(row, DEFAULT_MAPPING)

        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["email"] == "john@example.com"

    def test_apply_mapping_case_insensitive(self) -> None:
        """Test that mapping is case-insensitive."""
        row = {
            "First_Name": "John",
            "LAST_NAME": "Doe",
            "Email": "john@example.com",
        }
        result = apply_mapping(row, DEFAULT_MAPPING)

        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["email"] == "john@example.com"

    def test_apply_mapping_alternate_names(self) -> None:
        """Test that alternate column names are recognized."""
        row = {
            "firstname": "John",  # Alternate spelling
            "surname": "Doe",  # Alternate name
            "e-mail": "john@example.com",  # With hyphen
        }
        result = apply_mapping(row, DEFAULT_MAPPING)

        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["email"] == "john@example.com"

    def test_apply_mapping_first_match_wins(self) -> None:
        """Test that first matching column wins."""
        mapping = {"email": ["primary_email", "email"]}
        row = {
            "primary_email": "primary@example.com",
            "email": "secondary@example.com",
        }
        result = apply_mapping(row, mapping)

        assert result["email"] == "primary@example.com"

    def test_apply_mapping_empty_values_skipped(self) -> None:
        """Test that empty values are not included."""
        row = {
            "first_name": "John",
            "last_name": "",  # Empty
        }
        result = apply_mapping(row, DEFAULT_MAPPING)

        assert result["first_name"] == "John"
        assert "last_name" not in result


class TestCreateExampleMapping:
    """Test suite for create_example_mapping function."""

    def test_returns_valid_json(self) -> None:
        """Test that example mapping is valid JSON."""
        example = create_example_mapping()
        parsed = json.loads(example)

        assert isinstance(parsed, dict)
        assert "first_name" in parsed
        assert "last_name" in parsed

    def test_example_mapping_structure(self) -> None:
        """Test structure of example mapping."""
        example = create_example_mapping()
        parsed = json.loads(example)

        # All values should be lists
        for _field, columns in parsed.items():
            assert isinstance(columns, list)
            assert all(isinstance(c, str) for c in columns)


class TestDefaultMapping:
    """Test suite for DEFAULT_MAPPING constant."""

    def test_contains_all_fields(self) -> None:
        """Test that default mapping covers all vCard fields."""
        from csv2vcard.models import ALL_FIELDS

        for field in ALL_FIELDS:
            assert field in DEFAULT_MAPPING, f"Missing default mapping for: {field}"

    def test_all_values_are_lists(self) -> None:
        """Test that all mapping values are lists."""
        for field, columns in DEFAULT_MAPPING.items():
            assert isinstance(columns, list), f"{field} mapping is not a list"
            assert len(columns) > 0, f"{field} mapping is empty"


class TestMappingV060:
    """Test column normalization, multi-value columns and passthrough (v0.6.0)."""

    def test_spaces_and_hyphens_match(self) -> None:
        """Test that 'First Name' / 'E-Mail Address' match default aliases."""
        row = {"First Name": "John", "Last Name": "Doe", "E-mail Address": "j@example.com"}
        result = apply_mapping(row, DEFAULT_MAPPING)
        assert result == {"first_name": "John", "last_name": "Doe", "email": "j@example.com"}

    def test_mobile_is_cell_phone(self) -> None:
        """Test that 'mobile' maps to phone_cell only (not also to phone)."""
        result = apply_mapping({"mobile": "+111"}, DEFAULT_MAPPING)
        assert result == {"phone_cell": "+111"}

    def test_location_not_geo(self) -> None:
        """Test that a 'location' column (usually a place name) isn't used as GEO."""
        assert "geo" not in apply_mapping({"location": "Berlin"}, DEFAULT_MAPPING)

    def test_numbered_columns(self) -> None:
        """Test that numbered columns become extra values in order."""
        row = {"Email 3": "c@x.com", "email": "a@x.com", "Email 2": "b@x.com", "Phone2": "+2"}
        result = apply_mapping(row, DEFAULT_MAPPING)
        assert result["email"] == "a@x.com"
        assert result["email_2"] == "b@x.com"
        assert result["email_3"] == "c@x.com"
        assert result["phone"] == "+2"

    def test_multi_value_collects_all_aliases(self) -> None:
        """Test that all matching alias columns are kept for multi-value fields."""
        row = {"website": "https://a.com", "homepage": "https://b.com"}
        result = apply_mapping(row, DEFAULT_MAPPING)
        assert result["website"] == "https://a.com"
        assert result["website_2"] == "https://b.com"

    def test_keep_unmapped(self) -> None:
        """Test that unmapped non-empty columns become X- properties."""
        row = {"first_name": "John", "Cost Center": "42", "Empty": "", "last_name": "Doe"}
        result = apply_mapping(row, DEFAULT_MAPPING, keep_unmapped=True)
        assert result["X-COST-CENTER"] == "42"
        assert "X-EMPTY" not in result
        assert "X-FIRST-NAME" not in result

    def test_unmapped_dropped_by_default(self) -> None:
        """Test that unmapped columns are dropped unless requested."""
        result = apply_mapping({"first_name": "John", "Cost Center": "42"}, DEFAULT_MAPPING)
        assert result == {"first_name": "John"}
