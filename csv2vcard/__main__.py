"""Enable running as `python -m csv2vcard`."""

from __future__ import annotations

import sys


def main() -> None:
    """Entry point for python -m csv2vcard."""
    try:
        from csv2vcard.cli import app
        app()
    except ImportError:
        print("CLI requires optional dependencies. Install with: pip install csv2vcard[cli]")
        sys.exit(1)


if __name__ == "__main__":
    main()
