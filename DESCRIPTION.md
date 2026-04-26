# csv2vcard

A Python library for converting CSV files to vCard format (3.0 and 4.0).

Create vCards from a spreadsheet of contacts - useful for business cards, QR codes, CRM imports, or transferring contacts between systems.

## Features

- **vCard 3.0 and 4.0 support** - Generate either format
- **Custom CSV mapping** - Map any CSV column names to vCard fields
- **Batch processing** - Convert entire directories of CSV files
- **Single-file output** - Combine all contacts into one .vcf file
- **File splitting** - Split output by size (`--max-vcard-file-size`) or contact count (`--max-vcards-per-file`)
- **Multi-type fields** - Multiple phones (`phone_cell`, `phone_home`, `phone_work`, `phone_fax`), emails (`email_home`, `email_work`), and addresses (work + home)
- **Media embedding** - Embed photos, logos, and keys (base64 or URL)
- **Accent stripping** - Remove diacritics for compatibility (`--strip-accents`)
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

# Split output into multiple files (max 100 contacts per file)
csv2vcard convert contacts.csv --max-vcards-per-file 100

# Split output by file size (max 1MB per file)
csv2vcard convert contacts.csv --max-vcard-file-size 1048576

# Strip accents for compatibility
csv2vcard convert contacts.csv --strip-accents

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
    strip_accents=True,  # Remove diacritics
    max_vcards_per_file=100,  # Split into multiple files
)

# Convert entire directory
csv2vcard("./csv_folder/", ",", output_dir="./vcards")

# Test with sample contact
test_csv2vcard()
```

## CSV Format

Your CSV file should have column headers that match vCard fields. Use the default names or create a custom mapping.

### Default Column Names

**Required:** `last_name`, `first_name`

**Basic fields:**
```
last_name, first_name, middle_name, name_prefix, name_suffix, nickname, gender, birthday, anniversary, org, title, role, note
```

**Contact fields (single):**
```
phone, email, website
```

**Multi-type phone:**
```
phone_cell, phone_home, phone_work, phone_fax
```

**Multi-type email:**
```
email_home, email_work
```

**Work address:**
```
street, city, region, p_code, country
```

**Home address:**
```
home_street, home_city, home_region, home_p_code, home_country
```

**Media:**
```
photo, logo, key
```

**Additional fields:**
```
categories, geo, tz
```

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
  -d, --delimiter TEXT          CSV field delimiter (default: ",")
  -o, --output PATH             Output directory (default: ./export/)
  -V, --vcard-version TEXT      vCard version: 3.0 or 4.0 (default: 3.0)
  -1, --single-vcard            Export all contacts to a single .vcf file
  -m, --mapping PATH            Path to JSON mapping file
  -e, --encoding TEXT           CSV file encoding (auto-detected if not set)
  -a, --strip-accents           Remove accents/diacritics from contact fields
  --max-vcard-file-size INT     Split output by file size (bytes)
  --max-vcards-per-file INT     Split output by contact count
  --strict                      Exit on validation errors
  -v, --verbose                 Enable verbose output
  --version                     Show version and exit
  --help                        Show help message
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
    strip_accents=False,    # Remove diacritics
    max_file_size=None,     # Split by file size (bytes)
    max_vcards_per_file=None,  # Split by contact count
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

## Requirements

- Python 3.9 or higher
- For CLI: `typer` (installed with `csv2vcard[cli]`)
- For encoding detection: `charset-normalizer` (installed with `csv2vcard[encoding]`)

## License

MIT License - see [LICENSE.txt](LICENSE.txt)
