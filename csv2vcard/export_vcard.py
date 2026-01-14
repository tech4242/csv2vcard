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


def export_vcards_combined(
    vcards: list[dict[str, str] | VCardOutput],
    output_path: str | Path,
) -> Path:
    """
    Export multiple vCards to a single .vcf file.

    Args:
        vcards: List of vCard data (dicts or VCardOutput objects)
        output_path: Full path to the output file (including filename)

    Returns:
        Path to the created file

    Raises:
        ExportError: If export fails
    """
    output_file = Path(output_path)

    # Ensure parent directory exists
    ensure_export_dir(output_file.parent)

    # Collect all vCard outputs
    outputs: list[str] = []
    for vcard in vcards:
        if isinstance(vcard, VCardOutput):
            outputs.append(vcard.output)
        else:
            outputs.append(vcard["output"])

    # Combine with newlines (each vCard already ends with newline)
    combined = "".join(outputs)

    try:
        output_file.write_text(combined, encoding="utf-8")
        logger.info(f"Created combined vCard with {len(vcards)} contacts: {output_file}")
        return output_file
    except OSError as e:
        logger.error(f"Failed to write combined vCard: {e}")
        raise ExportError(f"Failed to export combined vCard: {e}") from e


def export_vcards_split(
    vcards: list[dict[str, str] | VCardOutput],
    output_dir: str | Path,
    base_filename: str = "contacts",
    max_file_size: int | None = None,
    max_vcards_per_file: int | None = None,
) -> list[Path]:
    """
    Export vCards to multiple files, splitting by size or count.

    Args:
        vcards: List of vCard data (dicts or VCardOutput objects)
        output_dir: Output directory
        base_filename: Base name for output files (without extension)
        max_file_size: Maximum file size in bytes (approximate)
        max_vcards_per_file: Maximum number of vCards per file

    Returns:
        List of paths to created files

    Raises:
        ExportError: If export fails
        ValueError: If neither max_file_size nor max_vcards_per_file specified
    """
    if max_file_size is None and max_vcards_per_file is None:
        raise ValueError("Either max_file_size or max_vcards_per_file must be specified")

    output_path = Path(output_dir)
    ensure_export_dir(output_path)

    # Extract vCard outputs
    outputs: list[str] = []
    for vcard in vcards:
        if isinstance(vcard, VCardOutput):
            outputs.append(vcard.output)
        else:
            outputs.append(vcard["output"])

    created_files: list[Path] = []
    current_chunk: list[str] = []
    current_size = 0
    file_index = 1

    def write_chunk() -> None:
        nonlocal current_chunk, current_size, file_index
        if not current_chunk:
            return

        filename = f"{base_filename}_{file_index:03d}.vcf"
        output_file = output_path / filename
        combined = "".join(current_chunk)

        try:
            output_file.write_text(combined, encoding="utf-8")
            created_files.append(output_file)
            logger.info(f"Created split vCard with {len(current_chunk)} contacts: {output_file}")
        except OSError as e:
            raise ExportError(f"Failed to write vCard file: {e}") from e

        current_chunk = []
        current_size = 0
        file_index += 1

    for output in outputs:
        vcard_size = len(output.encode("utf-8"))

        # Check if we need to start a new file
        should_split = False

        if max_vcards_per_file is not None and len(current_chunk) >= max_vcards_per_file:
            should_split = True

        if (max_file_size is not None
                and current_size + vcard_size > max_file_size
                and current_chunk):
            # Only split if we have at least one vCard in the chunk
            should_split = True

        if should_split:
            write_chunk()

        current_chunk.append(output)
        current_size += vcard_size

    # Write any remaining vCards
    write_chunk()

    logger.info(f"Created {len(created_files)} split vCard file(s)")
    return created_files


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
