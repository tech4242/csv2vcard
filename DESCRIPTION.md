# csv2vcard

A Python library for converting CSV files to vCard format (3.0 and 4.0).

Create vCards from a spreadsheet of contacts - useful for business cards, QR codes, CRM imports, or transferring contacts between systems.

## Features

- **vCard 3.0 and 4.0 support** - Generate either format
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
```

## Quick Start

### Command Line

```bash
# Convert a CSV file to vCards
csv2vcard convert contacts.csv

# Specify output directory and vCard version
csv2vcard convert contacts.csv -o ./vcards -V 4.0

# Use semicolon delimiter
csv2vcard convert contacts.csv -d ";"

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
)

# Test with sample contact
test_csv2vcard()
```

## CSV Format

Your CSV file should have these column headers:

```
last_name,first_name,title,org,phone,email,website,street,city,p_code,country
```

**Required columns:** `last_name`, `first_name`

**Optional columns:** `title`, `org`, `phone`, `email`, `website`, `street`, `city`, `p_code`, `country`

### Example CSV

```csv
last_name,first_name,title,org,phone,email,website,street,city,p_code,country
Gump,Forrest,Shrimp Man,Bubba Gump Shrimp Co.,+1234567890,forrest@example.com,https://example.com,42 Plantation St.,Baytown,30314,USA
Doe,Jane,Developer,Tech Corp,+0987654321,jane@example.com,https://jane.dev,123 Main St.,New York,10001,USA
```

## CLI Reference

```
csv2vcard convert [OPTIONS] CSV_FILE

Options:
  -d, --delimiter TEXT      CSV field delimiter (default: ",")
  -o, --output PATH         Output directory (default: ./export/)
  -V, --vcard-version TEXT  vCard version: 3.0 or 4.0 (default: 3.0)
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
    csv_filename,           # Path to CSV file
    csv_delimiter=",",      # Field delimiter
    output_dir=None,        # Output directory (default: ./export/)
    version=VCardVersion.V3_0,  # vCard version
    strict=False,           # Raise on validation errors
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
    email="john@example.com",
)

# Or from a dictionary
contact = Contact.from_dict({"last_name": "Doe", "first_name": "John"})

# vCard versions
VCardVersion.V3_0  # vCard 3.0 (RFC 2426)
VCardVersion.V4_0  # vCard 4.0 (RFC 6350)
```

## Requirements

- Python 3.9 or higher
- For CLI: `typer` (installed with `csv2vcard[cli]`)

## License

MIT License - see [LICENSE.txt](LICENSE.txt)
