"""
Secure File Serving Router
Handles file downloads with path validation and security checks
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Base directory for processed files
BASE_DIR = Path(__file__).parent.parent / "processed"

def sanitize_path(path_str: str) -> Path:
    """
    Sanitize and validate file path to prevent directory traversal attacks
    
    Args:
        path_str: Input path string
        
    Returns:
        Validated Path object
        
    Raises:
        HTTPException: If path is invalid or contains malicious patterns
    """
    # Remove any null bytes
    path_str = path_str.replace('\x00', '')
    
    # Check for directory traversal attempts
    dangerous_patterns = [
        '..',  # Parent directory
        '~',   # Home directory
        '$',   # Environment variables
        '|',   # Command injection
        ';',   # Command chaining
        '&',   # Command chaining
        '`',   # Command substitution
        '\n',  # Newline injection
        '\r',  # Carriage return injection
    ]
    
    for pattern in dangerous_patterns:
        if pattern in path_str:
            logger.warning(f"🚨 Malicious path detected: {path_str}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid path: contains forbidden pattern '{pattern}'"
            )
    
    # Convert to Path and resolve
    try:
        # Handle both absolute and relative paths
        if path_str.startswith('/api/files/'):
            path_str = path_str.replace('/api/files/', '')
        
        # Create path relative to BASE_DIR
        file_path = BASE_DIR / path_str
        
        # Resolve to absolute path
        resolved_path = file_path.resolve()
        
        # Ensure the resolved path is within BASE_DIR
        if not str(resolved_path).startswith(str(BASE_DIR.resolve())):
            logger.warning(f"🚨 Path traversal attempt: {path_str} -> {resolved_path}")
            raise HTTPException(
                status_code=403,
                detail="Access denied: path outside allowed directory"
            )
        
        # Check if file exists
        if not resolved_path.exists():
            logger.warning(f"📁 File not found: {resolved_path}")
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {path_str}"
            )
        
        # Check if it's a file (not a directory)
        if not resolved_path.is_file():
            logger.warning(f"🚨 Attempted to access directory: {resolved_path}")
            raise HTTPException(
                status_code=400,
                detail="Path must point to a file, not a directory"
            )
        
        logger.info(f"✅ Validated path: {resolved_path}")
        return resolved_path
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Path validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid path: {str(e)}"
        )


def get_media_type(file_path: Path) -> str:
    """
    Determine media type based on file extension
    
    Args:
        file_path: Path to file
        
    Returns:
        Media type string
    """
    extension = file_path.suffix.lower()
    
    media_types = {
        '.csv': 'text/csv',
        '.json': 'application/json',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.xls': 'application/vnd.ms-excel',
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.log': 'text/plain',
        '.html': 'text/html',
        '.htm': 'text/html',
    }
    
    return media_types.get(extension, 'application/octet-stream')


@router.get("/files/{file_path:path}")
async def download_file(file_path: str):
    """
    Secure file download endpoint with path validation
    
    Args:
        file_path: Relative path to file within processed directory
        
    Returns:
        FileResponse with the requested file
        
    Security:
        - Path sanitization
        - Directory traversal prevention
        - File existence validation
        - Access control (within BASE_DIR only)
    """
    try:
        # Sanitize and validate path
        validated_path = sanitize_path(file_path)
        
        # Get appropriate media type
        media_type = get_media_type(validated_path)
        
        # Get filename for download
        filename = validated_path.name
        
        logger.info(f"📥 Serving file: {filename} ({validated_path})")
        
        # Return file response
        return FileResponse(
            path=str(validated_path),
            media_type=media_type,
            filename=filename,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Content-Type-Options": "nosniff",  # Prevent MIME sniffing
                "X-Frame-Options": "DENY",  # Prevent clickjacking
                "Cache-Control": "no-cache, no-store, must-revalidate",  # No caching
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ File download error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading file: {str(e)}"
        )


@router.get("/files/validate/{file_path:path}")
async def validate_file_path(file_path: str):
    """
    Validate if a file path exists and is accessible
    
    Args:
        file_path: Relative path to file
        
    Returns:
        Validation result with file info
    """
    try:
        validated_path = sanitize_path(file_path)
        
        return {
            "valid": True,
            "path": str(validated_path.relative_to(BASE_DIR)),
            "filename": validated_path.name,
            "size": validated_path.stat().st_size,
            "exists": True
        }
        
    except HTTPException as e:
        return {
            "valid": False,
            "error": e.detail,
            "exists": False
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "exists": False
        }
