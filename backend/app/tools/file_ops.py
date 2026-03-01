import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Sandbox directory
BASE_DIR = Path(os.getcwd()) / "jarvis_files"
os.makedirs(BASE_DIR, exist_ok=True)

def _get_safe_path(filename: str) -> Path:
    """Ensure the path stays within the sandbox directory."""
    # Remove any directory traversal attempts
    safe_name = os.path.basename(filename)
    if not safe_name:
        raise ValueError("Invalid filename")
    return BASE_DIR / safe_name

def list_files() -> str:
    """List all files in the JARVIS sandbox."""
    try:
        files = [f.name for f in BASE_DIR.iterdir() if f.is_file()]
        if not files:
            return "The directory is empty."
        return "Files in directory:\n- " + "\n- ".join(files)
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return f"Error listing files: {e}"

def read_file(filename: str) -> str:
    """Read contents of a file in the sandbox."""
    try:
        safe_path = _get_safe_path(filename)
        if not safe_path.exists():
            return f"Error: File '{filename}' does not exist."
        with open(safe_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading {filename}: {e}")
        return f"Error reading file: {e}"

def write_file(filename: str, content: str) -> str:
    """Write contents to a file in the sandbox."""
    try:
        safe_path = _get_safe_path(filename)
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to '{filename}'."
    except Exception as e:
        logger.error(f"Error writing to {filename}: {e}")
        return f"Error writing file: {e}"

def delete_file(filename: str) -> str:
    """Delete a file from the sandbox."""
    try:
        safe_path = _get_safe_path(filename)
        if not safe_path.exists():
            return f"Error: File '{filename}' does not exist."
        os.remove(safe_path)
        return f"Successfully deleted '{filename}'."
    except Exception as e:
        logger.error(f"Error deleting {filename}: {e}")
        return f"Error deleting file: {e}"
