# Changelog

## 0.6.0

### Fixed

- **Contacts with the same name no longer overwrite each other.** Files are suffixed (`smith_john_2.vcf`, ...) instead of silently replaced.
- **Excel "CSV UTF-8" files work.** The byte order mark no longer corrupts the first column, which previously dropped every contact's last name.
- **Line breaks in a cell can no longer inject properties.** All values are escaped or sanitized, including `\r`.
- **Output follows the vCard specs:** CRLF line endings (also on Windows) and line folding at 75 octets.
- **vCard 4.0:**
  - Inline `PHOTO`, `LOGO` and `KEY` use `data:` URIs (`ENCODING=b` is not valid in 4.0).
  - Phone numbers are valid `tel:` URIs; local numbers without a country code are written as text.
  - `CATEGORIES` and `NICKNAME` keep their list separators instead of collapsing into one value.
- **vCard 3.0:**
  - The vCard 2.1 `CHARSET=UTF-8` parameter is no longer emitted.
  - `data:` URI photos are converted properly.
  - Time zone names use `VALUE=text`.
- **Invalid values are skipped with a warning** instead of being written: geo coordinates, and dates in 3.0.
- **`iter_contacts` streams rows** instead of loading the whole file first.
- **`test_csv2vcard` is no longer collected by pytest** as a test.

### Added

- **vCard 2.1 output** (`-V 2.1`) for legacy Outlook, car kits and feature phones, with quoted-printable encoding for non-ASCII text.
- **RFC 9554 properties in vCard 4.0:** `PRONOUNS` and `SOCIALPROFILE`, plus `LANG`. Columns: `pronouns`, `social_profile`, `language`.
- **Stable UIDs:** UIDs come from the name, organization and email, or from a `uid` / `contact_id` / `external_id` column. Re-importing a re-converted CSV updates contacts instead of duplicating them.
- **Multiple values per field:** numbered columns such as `email_2` or `Phone 3` for phones, emails, websites and social profiles.
- **`--keep-unmapped` / `keep_unmapped=True`:** writes columns that match no field as `X-` properties.
- **Organization-only rows** become company cards (`KIND:org` in 4.0, `X-ABSHOWAS:COMPANY` in 3.0).
- **`PRODID`** is written in 3.0 and 4.0.
- **More date formats:** `DD.MM.YYYY`, unambiguous slashed dates, and dates without a year (`--MM-DD`).
- **`csv2vcard --version`** works without a subcommand.
- **`--strict`** now also fails on malformed rows and undecodable bytes.

### Changed

- **Column headers match loosely:** case-insensitive, and spaces, hyphens and underscores are treated alike (`First Name` = `first_name`).
- **`mobile`, `cell` and `cellphone` columns now map to `phone_cell`** (`TEL;TYPE=CELL`) instead of the default work phone.
- **A `location` column is no longer treated as geo coordinates.**
- **Multi-value fields keep every matching column**, not just the first.
- **Python 3.10+ is required**; Python 3.9 is end-of-life. Python 3.14 is supported.

### Packaging and CI

- **Removed the stale `setup.py`**; `pyproject.toml` is the only build configuration. setuptools >= 77 is required.
- **CI runs mypy** and tests Python 3.10 to 3.14.
- **Releases publish through PyPI Trusted Publishing** (no API token); `action-gh-release` is updated to v2.
