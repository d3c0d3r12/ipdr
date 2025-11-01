"""
Secure File Upload Implementation
Prevents common file upload vulnerabilities
"""

import hashlib
import magic
import uuid
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
import logging

logger = logging.getLogger(__name__)

# Configuration
ALLOWED_MIME_TYPES = ['text/html', 'application/xhtml+xml']
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
UPLOAD_QUARANTINE = Path("/var/police/quarantine")
UPLOAD_PROCESSED = Path("/var/police/uploads")
ALLOWED_EXTENSIONS = ['.html', '.htm']

class SecureFileUpload:
    """Handles secure file uploads with validation"""
    
    def __init__(self):
        # Ensure directories exist
        UPLOAD_QUARANTINE.mkdir(parents=True, exist_ok=True)
        UPLOAD_PROCESSED.mkdir(parents=True, exist_ok=True)
        
        # Set restrictive permissions
        os.chmod(UPLOAD_QUARANTINE, 0o700)
        os.chmod(UPLOAD_PROCESSED, 0o700)
    
    def validate_file(
        self, 
        file: UploadFile, 
        user: str
    ) -> Tuple[bytes, dict]:
        """
        Comprehensive file validation
        Returns: (file_content, metadata)
        """
        
        # 1. Validate filename extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            logger.warning(f"Invalid file extension: {file_ext} from user {user}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Only {', '.join(ALLOWED_EXTENSIONS)} allowed"
            )
        
        # 2. Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"File too large: {file_size} bytes from user {user}")
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # 3. Read content
        content = file.file.read()
        file.file.seek(0)
        
        # 4. Validate MIME type (magic bytes)
        try:
            mime = magic.from_buffer(content, mime=True)
        except Exception as e:
            logger.error(f"MIME detection failed: {e}")
            raise HTTPException(status_code=400, detail="Could not determine file type")
        
        if mime not in ALLOWED_MIME_TYPES:
            logger.warning(f"Invalid MIME type: {mime} from user {user}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type detected: {mime}"
            )
        
        # 5. Content validation - check for required table
        try:
            html_text = content.decode('utf-8', errors='replace')
        except Exception as e:
            logger.error(f"Failed to decode HTML: {e}")
            raise HTTPException(status_code=400, detail="Invalid HTML encoding")
        
        if 'ip activity' not in html_text.lower():
            logger.warning(f"Missing IP ACTIVITY table from user {user}")
            raise HTTPException(
                status_code=400, 
                detail="File does not contain required IP ACTIVITY table"
            )
        
        # 6. Check for malicious patterns
        malicious_patterns = [
            '<script',
            'javascript:',
            'onerror=',
            'onload=',
            '<iframe',
            '<object',
            '<embed',
            'eval(',
            'document.cookie'
        ]
        
        html_lower = html_text.lower()
        for pattern in malicious_patterns:
            if pattern in html_lower:
                logger.warning(f"Malicious pattern detected: {pattern} from user {user}")
                # Don't reject, but log for investigation
                # raise HTTPException(status_code=400, detail="Suspicious content detected")
        
        # 7. Calculate hash
        file_hash = hashlib.sha256(content).hexdigest()
        
        # 8. Generate metadata
        metadata = {
            'original_filename': file.filename,
            'size': file_size,
            'mime_type': mime,
            'hash': file_hash,
            'uploaded_by': user,
            'uploaded_at': datetime.utcnow().isoformat(),
            'uuid': str(uuid.uuid4())
        }
        
        logger.info(f"File validated: {metadata['uuid']} by {user}")
        
        return content, metadata
    
    def save_to_quarantine(
        self, 
        content: bytes, 
        metadata: dict
    ) -> Path:
        """Save file to quarantine for inspection"""
        
        quarantine_path = UPLOAD_QUARANTINE / f"{metadata['uuid']}.html"
        
        # Write file
        with open(quarantine_path, 'wb') as f:
            f.write(content)
        
        # Set restrictive permissions (owner read/write only)
        os.chmod(quarantine_path, 0o600)
        
        # Write metadata
        metadata_path = UPLOAD_QUARANTINE / f"{metadata['uuid']}.json"
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        os.chmod(metadata_path, 0o600)
        
        logger.info(f"File saved to quarantine: {quarantine_path}")
        
        return quarantine_path
    
    def move_to_processed(
        self, 
        quarantine_path: Path, 
        metadata: dict
    ) -> Path:
        """Move validated file from quarantine to processed"""
        
        processed_path = UPLOAD_PROCESSED / f"{metadata['uuid']}.html"
        
        # Move file
        import shutil
        shutil.move(str(quarantine_path), str(processed_path))
        
        # Move metadata
        quarantine_meta = UPLOAD_QUARANTINE / f"{metadata['uuid']}.json"
        processed_meta = UPLOAD_PROCESSED / f"{metadata['uuid']}.json"
        if quarantine_meta.exists():
            shutil.move(str(quarantine_meta), str(processed_meta))
        
        logger.info(f"File moved to processed: {processed_path}")
        
        return processed_path
    
    def process_upload(
        self, 
        file: UploadFile, 
        user: str
    ) -> dict:
        """
        Complete secure upload process
        Returns: metadata with file paths
        """
        
        # Validate file
        content, metadata = self.validate_file(file, user)
        
        # Save to quarantine
        quarantine_path = self.save_to_quarantine(content, metadata)
        
        # Additional security checks could go here
        # (antivirus scan, sandbox execution, etc.)
        
        # Move to processed
        processed_path = self.move_to_processed(quarantine_path, metadata)
        
        # Update metadata with paths
        metadata['quarantine_path'] = str(quarantine_path)
        metadata['processed_path'] = str(processed_path)
        
        # Log to audit trail
        self._log_upload_event(metadata)
        
        return metadata
    
    def _log_upload_event(self, metadata: dict):
        """Log upload event to audit trail"""
        import json
        
        audit_log = Path("/var/log/police-intel/uploads.log")
        audit_log.parent.mkdir(parents=True, exist_ok=True)
        
        with open(audit_log, 'a') as f:
            f.write(json.dumps(metadata) + '\n')
        
        logger.info(f"Upload logged: {metadata['uuid']}")


# CSV Injection Prevention
def sanitize_for_csv(value):
    """
    Prevent CSV injection attacks
    Prefixes dangerous characters with single quote
    """
    if not isinstance(value, str):
        return value
    
    if not value:
        return value
    
    # Dangerous characters that can trigger formula execution
    dangerous_chars = ['=', '+', '-', '@', '\t', '\r', '\n']
    
    if value[0] in dangerous_chars:
        return "'" + value
    
    return value


def export_safe_csv(data: list, output_path: Path):
    """
    Export CSV with injection prevention
    """
    import csv
    
    if not data:
        return
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for row in data:
            # Sanitize each field
            sanitized_row = {
                key: sanitize_for_csv(value) 
                for key, value in row.items()
            }
            writer.writerow(sanitized_row)
    
    logger.info(f"Safe CSV exported: {output_path}")


# Usage Example
"""
from fastapi import APIRouter, UploadFile, File, Depends
from .security import SecureFileUpload
from .auth import get_current_user

router = APIRouter()
secure_upload = SecureFileUpload()

@router.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        metadata = secure_upload.process_upload(file, current_user['username'])
        
        return {
            "status": "success",
            "uuid": metadata['uuid'],
            "hash": metadata['hash'],
            "size": metadata['size']
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload processing failed")
"""
