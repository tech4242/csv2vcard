"""vCard export functionality for csv2vcard."""

from __future__ import annotations

import logging
import warnings
from pathlib import Path

from csv2vcard.exceptions import ExportError
from csv2vcard.models import VCardOutput
from csv2vcard.validators import validate_output_directory

logger = logging.getLogger(__name__)

# Default export directory (relative to cwd for backwards compatibility)
DEFAULT_EXPORT_DIR = Path("export")


def export_vcard(
    vcard: dict[str, str] | VCardOutput,
    output_dir: str | Path | None = None,
) -> Path:
    """
    Export a vCard to a file.

    Args:
        vcard: vCard data (dict with 'filename' and 'output' keys, or VCardOutput)
        output_dir: Output directory (default: ./export/)

    Returns:
        Path to the created file

    Raises:
        ExportError: If export fails
    """
    # Normalize vcard data
    if isinstance(vcard, VCardOutput):
        filename = vcard.filename
        output = vcard.output
        name = vcard.name
    else:
        filename = vcard["filename"]
        output = vcard["output"]
        name = vcard.get("name", filename)

    # Determine output directory
    export_path = DEFAULT_EXPORT_DIR if output_dir is None else Path(output_dir)

    # Ensure output directory exists
    ensure_export_dir(export_path)

    # Full output path
    output_file = export_path / filename

    # Security check: ensure we're not writing outside export dir
    try:
        output_file.resolve().relative_to(export_path.resolve())
    except ValueError:
        raise ExportError(
            f"Security error: attempted path traversal in filename '{filename}'"
        ) from None

    try:
        output_file.write_text(output, encoding="utf-8")
        logger.info(f"Created vCard for {name}: {output_file}")
        return output_file
    except OSError as e:
        logger.error(f"Failed to write vCard for {name}: {e}")
        raise ExportError(f"Failed to export vCard: {e}") from e


def ensure_export_dir(output_dir: str | Path | None = None) -> Path:
    """
    Ensure export directory exists, creating it if necessary.

    Args:
        output_dir: Directory path (default: ./export/)

    Returns:
        Path to the export directory

    Raises:
        ExportError: If directory cannot be created
    """
    export_path = DEFAULT_EXPORT_DIR if output_dir is None else Path(output_dir)

    try:
        validate_output_directory(export_path)
    except Exception as e:
        raise ExportError(str(e)) from e

    if not export_path.exists():
        logger.info(f"Creating export directory: {export_path}")
        try:
            export_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ExportError(f"Failed to create export directory: {e}") from e

    return export_path


# Legacy function for backwards compatibility
def check_export() -> None:
    """
    Legacy function - checks/creates export directory.

    .. deprecated:: 0.3.0
        Use :func:`ensure_export_dir` instead.
    """
    warnings.warn(
        "check_export() is deprecated, use ensure_export_dir()",
        DeprecationWarning,
        stacklevel=2,
    )
    ensure_export_dir()
