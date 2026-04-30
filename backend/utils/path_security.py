"""
Path Security Utilities
Prevent directory traversal and path injection attacks
"""

from pathlib import Path, PurePath
from typing import Union
from fastapi import HTTPException


def safe_get_run_dir(run_dir_input: str, allowed_base: Union[str, Path]) -> Path:
    """
    Safely resolve a run directory path while preventing traversal attacks
    
    Args:
        run_dir_input: User-provided run directory path
        allowed_base: Base directory that all paths must be within
        
    Returns:
        Resolved Path object
        
    Raises:
        HTTPException: If path is invalid or outside allowed base
    """
    allowed_base = Path(allowed_base).resolve()
    
    # Reject empty paths
    if not run_dir_input or not run_dir_input.strip():
        raise HTTPException(status_code=400, detail="Invalid path: empty run directory")
    
    # Parse the input path
    requested_path = PurePath(run_dir_input)
    
    # Reject absolute paths
    if requested_path.is_absolute():
        raise HTTPException(status_code=400, detail="Invalid path: absolute paths not allowed")
    
    # Reject paths with parent directory references
    if ".." in requested_path.parts:
        raise HTTPException(status_code=400, detail="Invalid path: parent directory references not allowed")
    
    # Construct the full path
    full_path = (allowed_base / run_dir_input).resolve()
    
    # Verify the final path is within the allowed base
    try:
        full_path.relative_to(allowed_base)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid path: directory outside allowed location"
        )
    
    return full_path


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename to prevent injection attacks
    
    Args:
        filename: Original filename
        max_length: Maximum length for filename
        
    Returns:
        Sanitized filename
    """
    # Remove path separators
    filename = filename.replace("/", "_").replace("\\", "_")
    
    # Remove null bytes and control characters
    filename = "".join(char for char in filename if ord(char) >= 32)
    
    # Limit length
    filename = filename[:max_length]
    
    # Ensure not empty
    if not filename:
        filename = "file"
    
    return filename
