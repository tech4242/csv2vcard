"""Command-line interface for csv2vcard."""

import logging
import sys
from pathlib import Path
from typing import Optional

# Check if typer is available
try:
    from typing import Annotated

    import typer

    HAS_TYPER = True
except ImportError:
    HAS_TYPER = False
    typer = None  # type: ignore


def _check_typer() -> None:
    """Check if Typer is available and exit with message if not."""
    if not HAS_TYPER:
        print("CLI requires 'typer' package. Install with: pip install csv2vcard[cli]")
        sys.exit(1)


if HAS_TYPER:
    from csv2vcard import __version__
    from csv2vcard.csv2vcard import csv2vcard as csv2vcard_func
    from csv2vcard.csv2vcard import test_csv2vcard as test_csv2vcard_func
    from csv2vcard.mapping import create_example_mapping
    from csv2vcard.models import VCardVersion

    app = typer.Typer(
        name="csv2vcard",
        help="Convert CSV files to vCard format (3.0 and 4.0).",
        add_completion=False,
    )

    def version_callback(value: bool) -> None:
        """Show version and exit."""
        if value:
            print(f"csv2vcard version {__version__}")
            raise typer.Exit()

    @app.command()
    def convert(
        source: Annotated[
            Path,
            typer.Argument(
                help="Path to CSV file or directory containing CSV files",
                exists=True,
            ),
        ],
        delimiter: Annotated[
            str,
            typer.Option(
                "--delimiter",
                "-d",
                help="CSV field delimiter character",
            ),
        ] = ",",
        output_dir: Annotated[
            Optional[Path],
            typer.Option(
                "--output",
                "-o",
                help="Output directory for vCard files (default: ./export/)",
            ),
        ] = None,
        vcard_version: Annotated[
            str,
            typer.Option(
                "--vcard-version",
                "-V",
                help="vCard version to generate: 3.0 or 4.0",
            ),
        ] = "3.0",
        single_file: Annotated[
            bool,
            typer.Option(
                "--single-vcard",
                "-1",
                help="Export all contacts to a single .vcf file",
            ),
        ] = False,
        mapping_file: Annotated[
            Optional[Path],
            typer.Option(
                "--mapping",
                "-m",
                help="Path to JSON mapping file for custom CSV column names",
            ),
        ] = None,
        encoding: Annotated[
            Optional[str],
            typer.Option(
                "--encoding",
                "-e",
                help="CSV file encoding (auto-detected if not specified)",
            ),
        ] = None,
        strict: Annotated[
            bool,
            typer.Option(
                "--strict",
                help="Exit on validation errors",
            ),
        ] = False,
        verbose: Annotated[
            bool,
            typer.Option(
                "--verbose",
                "-v",
                help="Enable verbose output",
            ),
        ] = False,
        version: Annotated[
            Optional[bool],
            typer.Option(
                "--version",
                callback=version_callback,
                is_eager=True,
                help="Show version and exit",
            ),
        ] = None,
    ) -> None:
        """
        Convert CSV file(s) to vCard files.

        Examples:

            csv2vcard convert contacts.csv

            csv2vcard convert contacts.csv -d ";" -o ./vcards -V 4.0

            csv2vcard convert ./csv_folder/ --single-vcard -o ./output

            csv2vcard convert data.csv -m mapping.json
        """
        # Configure logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(levelname)s: %(message)s",
        )

        # Parse vCard version
        try:
            vc_version = VCardVersion(vcard_version)
        except ValueError:
            typer.echo(f"Error: Invalid vCard version '{vcard_version}'. Use 3.0 or 4.0.")
            raise typer.Exit(code=1) from None

        try:
            files = csv2vcard_func(
                source,
                delimiter,
                output_dir=output_dir,
                version=vc_version,
                strict=strict,
                single_file=single_file,
                encoding=encoding,
                mapping_file=mapping_file,
            )
            if files:
                typer.echo(f"Successfully created {len(files)} vCard file(s).")
                for f in files:
                    typer.echo(f"  - {f}")
            else:
                typer.echo("No vCard files were created. Check your CSV file.")
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1) from None

    @app.command()
    def test(
        output_dir: Annotated[
            Optional[Path],
            typer.Option(
                "--output",
                "-o",
                help="Output directory for the test vCard",
            ),
        ] = None,
        vcard_version: Annotated[
            str,
            typer.Option(
                "--vcard-version",
                "-V",
                help="vCard version to generate: 3.0 or 4.0",
            ),
        ] = "3.0",
    ) -> None:
        """
        Create a test vCard (Forrest Gump example).

        This is useful for verifying the installation works correctly.
        """
        try:
            vc_version = VCardVersion(vcard_version)
        except ValueError:
            typer.echo(f"Error: Invalid vCard version '{vcard_version}'. Use 3.0 or 4.0.")
            raise typer.Exit(code=1) from None

        test_csv2vcard_func(output_dir=output_dir, version=vc_version)
        typer.echo("Test vCard created successfully.")

    @app.command(name="mapping")
    def show_mapping() -> None:
        """
        Show an example mapping file for custom CSV columns.

        The mapping file is a JSON file that maps vCard fields to
        possible CSV column names. Copy this output to a .json file
        and customize for your CSV format.
        """
        typer.echo(create_example_mapping())

else:
    # Fallback app when Typer is not installed
    def app() -> None:
        """Fallback CLI without Typer."""
        _check_typer()


if __name__ == "__main__":
    if HAS_TYPER:
        app()
    else:
        _check_typer()
