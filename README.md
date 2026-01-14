<div align="center">

# csv2vcard

[![Downloads](https://static.pepy.tech/badge/csv2vcard)](https://pepy.tech/projects/csv2vcard)
[![PyPI](https://img.shields.io/pypi/v/csv2vcard.svg)](https://pypi.org/project/csv2vcard/)
[![codecov](https://codecov.io/gh/tech4242/csv2vcard/graph/badge.svg?token=VUG1OXUH45)](https://codecov.io/gh/tech4242/csv2vcard)
[![Python](https://img.shields.io/pypi/pyversions/csv2vcard.svg)](https://pypi.org/project/csv2vcard/)
[![Typed](https://img.shields.io/badge/typed-py.typed-blue.svg)](https://peps.python.org/pep-0561/)
[![Typer](https://img.shields.io/badge/CLI-Typer-2bbc8a.svg)](https://typer.tiangolo.com/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/pypi/l/csv2vcard.svg)](https://github.com/tech4242/csv2vcard/blob/master/LICENSE.txt)

</div>

A Python library for converting CSV files to vCard format (3.0 and 4.0).

Create vCards from a spreadsheet of contacts - useful for business cards, QR codes, CRM imports, or transferring contacts between systems.

## Features

- **vCard 3.0 and 4.0 support** - Generate either format
- **Custom CSV mapping** - Map any CSV column names to vCard fields
- **Batch processing** - Convert entire directories of CSV files
- **Single-file output** - Combine all contacts into one .vcf file
- **Auto-detect encoding** - Handles various file encodings
- **Command-line interface** - Convert files directly from terminal
- **Library API** - Use programmatically in your Python code
- **Type hints** - Full typing support for IDE autocomplete
- **Security** - Input validation and path traversal protection
- **Zero dependencies** - Core library uses only Python stdlib

## Installation

```bash
# Basic installation (library only)
pip install csv2vcard

# With CLI support
pip install csv2vcard[cli]

# With encoding detection
pip install csv2vcard[encoding]

# Full installation
pip install csv2vcard[all]
```

## Quick Start

### Command Line

```bash
# Convert a CSV file to vCards
csv2vcard convert contacts.csv

# Specify output directory and vCard version
csv2vcard convert contacts.csv -o ./vcards -V 4.0

# Convert all CSVs in a directory
csv2vcard convert ./csv_folder/

# Export all contacts to a single file
csv2vcard convert contacts.csv --single-vcard

# Use custom column mapping
csv2vcard convert data.csv -m mapping.json

# Show example mapping file
csv2vcard mapping

# Create a test vCard (Forrest Gump)
csv2vcard test
```

### Python Library

```python
from csv2vcard import csv2vcard, test_csv2vcard

# Basic usage - creates vCards in ./export/
csv2vcard("contacts.csv", ",")

# With options
from csv2vcard.models import VCardVersion

csv2vcard(
    "contacts.csv",
    ",",
    output_dir="./vcards",
    version=VCardVersion.V4_0,
    single_file=True,  # All contacts in one file
    mapping_file="mapping.json",  # Custom column names
)

# Convert entire directory
csv2vcard("./csv_folder/", ",", output_dir="./vcards")

# Test with sample contact
test_csv2vcard()
```

## CSV Format

Your CSV file should have column headers that match vCard fields. Use the default names or create a custom mapping.

### Default Column Names

```
last_name,first_name,middle_name,name_prefix,name_suffix,nickname,gender,birthday,anniversary,phone,email,website,org,title,role,street,city,region,p_code,country,note
```

**Required:** `last_name`, `first_name`

**Optional:** All other fields

### Example CSV

```csv
last_name,first_name,title,org,phone,email,street,city,p_code,country,birthday,note
Gump,Forrest,Shrimp Man,Bubba Gump Shrimp Co.,+1234567890,forrest@example.com,42 Plantation St.,Baytown,30314,USA,1944-06-06,Life is like a box of chocolates
Doe,Jane,Developer,Tech Corp,+0987654321,jane@example.com,123 Main St.,New York,10001,USA,,
```

### Custom Column Mapping

Create a JSON file to map your CSV column names to vCard fields:

```json
{
  "first_name": ["Given Name", "FirstName", "First"],
  "last_name": ["Surname", "FamilyName", "Last"],
  "email": ["Email Address", "E-Mail"],
  "phone": ["Phone Number", "Mobile", "Tel"]
}
```

Then use it:
```bash
csv2vcard convert data.csv -m mapping.json
```

## CLI Reference

```
csv2vcard convert [OPTIONS] SOURCE

Arguments:
  SOURCE  Path to CSV file or directory containing CSV files

Options:
  -d, --delimiter TEXT      CSV field delimiter (default: ",")
  -o, --output PATH         Output directory (default: ./export/)
  -V, --vcard-version TEXT  vCard version: 3.0 or 4.0 (default: 3.0)
  -1, --single-vcard        Export all contacts to a single .vcf file
  -m, --mapping PATH        Path to JSON mapping file
  -e, --encoding TEXT       CSV file encoding (auto-detected if not set)
  --strict                  Exit on validation errors
  -v, --verbose             Enable verbose output
  --version                 Show version and exit
  --help                    Show help message
```

## API Reference

### Main Functions

```python
from csv2vcard import csv2vcard, test_csv2vcard
from csv2vcard.models import VCardVersion

# Convert CSV to vCards
files = csv2vcard(
    csv_filename,           # Path to CSV file or directory
    csv_delimiter=",",      # Field delimiter
    output_dir=None,        # Output directory (default: ./export/)
    version=VCardVersion.V3_0,  # vCard version
    strict=False,           # Raise on validation errors
    single_file=False,      # Combine all contacts into one file
    encoding=None,          # File encoding (auto-detected)
    mapping_file=None,      # Path to JSON mapping file
)
# Returns: List[Path] of created vCard files

# Test with sample contact
test_csv2vcard(
    output_dir=None,
    version=VCardVersion.V3_0,
)
```

### Models

```python
from csv2vcard.models import Contact, VCardVersion, VCardOutput

# Create a contact programmatically
contact = Contact(
    last_name="Doe",
    first_name="John",
    middle_name="William",
    email="john@example.com",
    phone="+1234567890",
    birthday="1990-01-15",
    nickname="Johnny",
)

# Or from a dictionary
contact = Contact.from_dict({"last_name": "Doe", "first_name": "John"})

# vCard versions
VCardVersion.V3_0  # vCard 3.0 (RFC 2426)
VCardVersion.V4_0  # vCard 4.0 (RFC 6350)
```

## Supported vCard Fields

| Field | Description | Example |
|-------|-------------|---------|
| `last_name` | Family name | Doe |
| `first_name` | Given name | John |
| `middle_name` | Middle name | William |
| `name_prefix` | Honorific prefix | Dr. |
| `name_suffix` | Honorific suffix | Jr. |
| `nickname` | Nickname | Johnny |
| `gender` | Gender (M/F/O/N/U) | M |
| `birthday` | Birth date (YYYY-MM-DD) | 1990-01-15 |
| `anniversary` | Anniversary date | 2015-06-20 |
| `phone` | Phone number | +1234567890 |
| `email` | Email address | john@example.com |
| `website` | Website URL | https://example.com |
| `org` | Organization | Acme Corp |
| `title` | Job title | Developer |
| `role` | Role/function | Team Lead |
| `street` | Street address | 123 Main St |
| `city` | City | New York |
| `region` | State/province | NY |
| `p_code` | Postal code | 10001 |
| `country` | Country | USA |
| `note` | Notes | Any additional info |

## Requirements

- Python 3.9 or higher
- For CLI: `typer` (installed with `csv2vcard[cli]`)
- For encoding detection: `charset-normalizer` (installed with `csv2vcard[encoding]`)

## Development

```bash
# Clone the repository
git clone https://github.com/tech4242/csv2vcard.git
cd csv2vcard

# Install dev dependencies
pip install -e .[dev]

# Run tests
pytest

# Run tests with coverage
pytest --cov=csv2vcard --cov-report=term-missing

# Type checking
mypy csv2vcard

# Linting
ruff check csv2vcard
```

## License

MIT License - see [LICENSE.txt](LICENSE.txt)
