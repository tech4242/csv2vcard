"""csv2vcard - Convert CSV files to vCard format (2.1, 3.0 and 4.0)."""

# For backwards compatibility, users can still do:
#   from csv2vcard import csv2vcard
#   csv2vcard.csv2vcard("file.csv", ",")
# This works because Python allows importing submodules directly.
#
# For cleaner new API, also expose the main functions:
from csv2vcard._version import __version__
from csv2vcard.csv2vcard import csv2vcard, test_csv2vcard

__all__ = [
    "csv2vcard",
    "test_csv2vcard",
    "__version__",
]
