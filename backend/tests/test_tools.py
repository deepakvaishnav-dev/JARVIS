import pytest
from app.tools.file_ops import _get_safe_path, BASE_DIR

def test_file_ops_sandbox_traversal():
    """Verify that the _get_safe_path prevents directory traversal attacks."""
    
    # Attempt to go up one directory
    malicious_path = "../../../windows/system32/cmd.exe"
    
    # _get_safe_path strips the path and only uses the basename
    safe_target = _get_safe_path(malicious_path)
    
    # It should forcefully place it inside the BASE_DIR
    assert str(BASE_DIR) in str(safe_target)
    assert "cmd.exe" in str(safe_target)
    assert "system32" not in str(safe_target)
    
def test_file_ops_empty_filename():
    """Verify that an empty filename raises a value error instead of manipulating the root dir."""
    with pytest.raises(ValueError):
        _get_safe_path("")
