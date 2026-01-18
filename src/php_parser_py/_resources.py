"""
Resource management for php-parser-py.

Handles extraction of bundled PHP-Parser zip file on first import.
"""

import hashlib
import threading
import zipfile
from pathlib import Path
from typing import Optional

# Global lock for thread-safe extraction
_extraction_lock = threading.Lock()
_extraction_done = False


def get_vendor_path() -> Path:
    """Get the path where PHP-Parser should be extracted."""
    return Path(__file__).parent / "vendor"


def get_resources_path() -> Path:
    """Get the path to the resources directory."""
    # Resources are inside the package directory
    return Path(__file__).parent / "resources"


def get_marker_file() -> Path:
    """Get the path to the extraction marker file."""
    return get_vendor_path() / ".extracted"


def calculate_zip_hash(zip_path: Path) -> str:
    """Calculate SHA256 hash of the zip file."""
    sha256_hash = hashlib.sha256()
    with open(zip_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def is_already_extracted(zip_path: Path) -> bool:
    """
    Check if PHP-Parser has already been extracted.

    Returns True if the marker file exists and the zip hash matches.
    """
    marker_file = get_marker_file()
    if not marker_file.exists():
        return False

    # Check if hash matches
    try:
        stored_hash = marker_file.read_text().strip()
        current_hash = calculate_zip_hash(zip_path)
        return stored_hash == current_hash
    except Exception:
        # If we can't read the marker or calculate hash, re-extract
        return False


def extract_php_parser(zip_path: Path, vendor_path: Path) -> None:
    """
    Extract PHP-Parser zip file to vendor directory.

    Args:
        zip_path: Path to the php-parser zip file
        vendor_path: Path where files should be extracted
    """
    # Create vendor directory if it doesn't exist
    vendor_path.mkdir(parents=True, exist_ok=True)

    # Extract the zip file
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(vendor_path)

    # Create marker file with zip hash
    zip_hash = calculate_zip_hash(zip_path)
    marker_file = get_marker_file()
    marker_file.write_text(zip_hash)


def ensure_php_parser_extracted() -> Path:
    """
    Ensure PHP-Parser is extracted and ready to use.

    This function is called on package import. It checks if PHP-Parser
    has already been extracted, and if not, extracts it in a thread-safe manner.

    Returns:
        Path to the vendor directory containing PHP-Parser

    Raises:
        FileNotFoundError: If the php-parser zip file is not found
        RuntimeError: If extraction fails
    """
    global _extraction_done

    # Fast path: already extracted in this process
    if _extraction_done:
        return get_vendor_path()

    vendor_path = get_vendor_path()
    resources_path = get_resources_path()

    # Find the php-parser zip file
    zip_files = list(resources_path.glob("php-parser-*.zip"))
    if not zip_files:
        raise FileNotFoundError(
            f"PHP-Parser zip file not found in {resources_path}. "
            f"Expected a file matching pattern 'php-parser-*.zip'"
        )

    zip_path = zip_files[0]

    # Check if already extracted (with marker file)
    if is_already_extracted(zip_path):
        _extraction_done = True
        return vendor_path

    # Thread-safe extraction
    with _extraction_lock:
        # Double-check after acquiring lock (another thread might have extracted)
        if is_already_extracted(zip_path):
            _extraction_done = True
            return vendor_path

        try:
            # Extract PHP-Parser
            extract_php_parser(zip_path, vendor_path)
            _extraction_done = True
            return vendor_path

        except Exception as e:
            raise RuntimeError(
                f"Failed to extract PHP-Parser from {zip_path}: {e}"
            ) from e


def get_php_parser_path() -> Optional[Path]:
    """
    Get the path to the extracted PHP-Parser directory.

    Returns:
        Path to PHP-Parser, or None if not yet extracted
    """
    vendor_path = get_vendor_path()
    if not vendor_path.exists():
        return None

    # Look for the php-parser directory inside vendor
    php_parser_dirs = list(vendor_path.glob("php-parser-*"))
    if php_parser_dirs:
        return php_parser_dirs[0]

    return None
