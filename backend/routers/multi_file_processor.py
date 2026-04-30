"""
Multi-File HTML Processor Router
Handles uploading and processing multiple HTML files with Steps 1-4 automation
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse, StreamingResponse
from database import get_session
from routers.auth_secure import get_current_user
from models.investigation import INVESTIGATIONS_COLLECTION
from pathlib import Path
from typing import List
import asyncio
import logging
from datetime import datetime
import re
from bs4 import BeautifulSoup
import pandas as pd
import io
import zipfile
import tempfile

logger = logging.getLogger(__name__)

router = APIRouter()

# Import cloud storage service and auto processor
try:
    from services.auto_processor import start_auto_processing
    AUTO_PROCESSING_AVAILABLE = True
except Exception as e:
    logger.warning(f"Auto processing not available: {e}")
    AUTO_PROCESSING_AVAILABLE = False
try:
    from services.cloud_storage_service import CloudStorageService
except Exception as e:
    logger.warning(f"Cloud storage service not available: {e}")
    CloudStorageService = None


def extract_html_from_zip(zip_content: bytes, zip_filename: str) -> List[dict]:
    """
    Extract all HTML files from ZIP (recursively walks through all folders)
    
    Args:
        zip_content: ZIP file content as bytes
        zip_filename: Original ZIP filename
    
    Returns:
        List of dicts with 'filename' and 'content' for each HTML file
    """
    html_files = []
    
    try:
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
            # Walk through all files in ZIP (including nested folders)
            for file_info in zf.infolist():
                # Skip directories
                if file_info.is_dir():
                    continue
                
                filename = file_info.filename
                
                # Check if it's an HTML file
                if filename.lower().endswith(('.html', '.htm')):
                    try:
                        # Read HTML content
                        html_content = zf.read(file_info.filename)
                        
                        # Get just the filename (remove path)
                        base_filename = Path(filename).name
                        
                        html_files.append({
                            'filename': base_filename,
                            'content': html_content,
                            'path_in_zip': filename
                        })
                        
                        logger.info(f"📄 Found HTML in ZIP: {filename}")
                        
                    except Exception as e:
                        logger.error(f"Error reading {filename} from ZIP: {e}")
                        continue
        
        logger.info(f"✅ Extracted {len(html_files)} HTML files from {zip_filename}")
        
    except zipfile.BadZipFile:
        logger.error(f"❌ Invalid ZIP file: {zip_filename}")
    except Exception as e:
        logger.error(f"❌ Error extracting ZIP {zip_filename}: {e}")
    
    return html_files


def extract_filename_base(filename: str) -> str:
    """
    Extract base name from HTML filename
    bharatkumarumma.SubscriberInfo.html → bharatkumarumma
    """
    # Remove extension
    base = filename.rsplit('.', 1)[0]
    
    # If has .SubscriberInfo or similar, take first part
    if '.' in base:
        base = base.split('.')[0]
    
    # Sanitize
    base = re.sub(r'[^\w\-]', '_', base)
    
    return base


def extract_ips_from_html(html_content: str) -> tuple:
    """
    Extract IP data and email from HTML file
    Returns tuple: (ip_data_list, email)
    ip_data_list: List of {timestamp, ip} dictionaries
    email: Extracted email address or None
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        ip_data = []
        
        # Extract email from HTML (more precise pattern)
        email = None
        # Match email but stop at word boundaries or special chars
        email_pattern = r'\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b'
        all_text = soup.get_text()
        email_matches = re.findall(email_pattern, all_text)
        if email_matches:
            # Clean up email - remove any trailing text
            email = email_matches[0].strip()
            # Additional cleanup: remove common suffixes
            email = re.sub(r'(Alternate|Primary|Secondary|Email)$', '', email, flags=re.IGNORECASE).strip()
            logger.info(f"📧 Extracted email: {email}")
        
        # Method 1: Extract from IP ACTIVITY table with timestamps
        tables = soup.find_all('table')
        
        for table in tables:
            # Check if this is the IP ACTIVITY table
            rows = table.find_all('tr')
            if not rows:
                continue
            
            # Check header row
            header_cells = rows[0].find_all(['th', 'td'])
            header_text = ' '.join([cell.get_text().strip().lower() for cell in header_cells])
            
            # If this is IP ACTIVITY table
            if 'timestamp' in header_text and 'ip address' in header_text:
                logger.info(f"📊 Found IP ACTIVITY table")
                
                # Process data rows
                for row in rows[1:]:  # Skip header
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        timestamp_text = cells[0].get_text().strip()
                        ip_text = cells[1].get_text().strip()
                        
                        # Parse timestamp (format: 2025-07-04 14:49:25 Z)
                        try:
                            # Remove ' Z' and convert to YYYYMMDDHHMMSS
                            timestamp_clean = timestamp_text.replace(' Z', '').replace('-', '').replace(':', '').replace(' ', '')
                            if len(timestamp_clean) >= 14:
                                timestamp_formatted = timestamp_clean[:14]
                            else:
                                timestamp_formatted = datetime.now().strftime('%Y%m%d%H%M%S')
                        except:
                            timestamp_formatted = datetime.now().strftime('%Y%m%d%H%M%S')
                        
                        # Validate IP
                        if ip_text and ip_text != '0.0.0.0' and not ip_text.startswith('127.'):
                            ip_data.append({
                                'timestamp': timestamp_formatted,
                                'ip': ip_text
                            })
        
        # Method 2: Fallback - extract all IPs with current timestamp
        if len(ip_data) == 0:
            logger.info(f"⚠️ No IP ACTIVITY table found, using fallback extraction")
            
            # IPv4 pattern
            ipv4_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            # IPv6 pattern
            ipv6_pattern = r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
            
            # Find all IPs
            ipv4_matches = re.findall(ipv4_pattern, all_text)
            ipv6_matches = re.findall(ipv6_pattern, all_text)
            all_ips = ipv4_matches + ipv6_matches
            
            current_time = datetime.now().strftime('%Y%m%d%H%M%S')
            for ip in all_ips:
                if ip and ip != '0.0.0.0' and not ip.startswith('127.'):
                    ip_data.append({
                        'timestamp': current_time,
                        'ip': ip
                    })
        
        # DO NOT remove duplicates - preserve all IPs as they appear in HTML
        logger.info(f"✅ Extracted {len(ip_data)} IPs (duplicates preserved)")
        return ip_data, email
        
    except Exception as e:
        logger.error(f"Error extracting IPs from HTML: {e}")
        return [], None


async def check_duplicate_filename(db, fir_number: str, base_filename: str) -> str:
    """
    Check if filename exists and return unique name
    bharatkumarumma → bharatkumarumma_1, bharatkumarumma_2, etc.
    """
    # Get all investigations for this FIR with similar names
    cursor = db[INVESTIGATIONS_COLLECTION].find(
        {
            "fir_number": fir_number,
            "investigation_name": {"$regex": f"^{re.escape(base_filename)}"},
        },
        {"investigation_name": 1},
    )
    existing = await cursor.to_list(length=None)
    
    if not existing:
        return base_filename
    
    # Find highest number
    max_num = 0
    for inv in existing:
        name = inv["investigation_name"]
        if name == base_filename:
            max_num = max(max_num, 0)
        elif name.startswith(base_filename + '_'):
            try:
                num = int(name.split('_')[-1])
                max_num = max(max_num, num)
            except:
                pass
    
    return f"{base_filename}_{max_num + 1}" if max_num >= 0 and existing else base_filename


@router.post("/upload-html-files")
async def upload_html_files(
    files: List[UploadFile] = File(...),
    fir_number: str = Form(...),
    db=Depends(get_session)
):
    """
    Upload multiple HTML or ZIP files and start automatic processing (Steps 1-4)
    
    Supports:
    - HTML files (.html, .htm)
    - ZIP files (.zip) - extracts all HTML files recursively
    
    Steps performed automatically:
    1. Extract IPs from HTML → original_log.csv
    2. Lookup IPs → ip_lookup_results.csv
    3. Merge data → Master_file.csv
    4. Remove header → fully_fixed.csv
    
    Returns investigation IDs for tracking
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 999:
            raise HTTPException(status_code=400, detail="Maximum 999 files allowed")
        
        logger.info(f"🚀 Processing {len(files)} files for FIR {fir_number}")
        
        investigations = []
        
        # First, collect all HTML files (from direct uploads and ZIPs)
        html_files_to_process = []
        
        for file in files:
            file_content = await file.read()
            
            # Check if it's a ZIP file
            if file.filename.lower().endswith('.zip'):
                logger.info(f"📦 Extracting ZIP file: {file.filename}")
                
                # Extract HTML files from ZIP
                extracted_htmls = extract_html_from_zip(file_content, file.filename)
                
                if not extracted_htmls:
                    logger.warning(f"⚠️  No HTML files found in {file.filename}")
                    investigations.append({
                        'filename': file.filename,
                        'success': False,
                        'error': 'No HTML files found in ZIP'
                    })
                    continue
                
                # Add all extracted HTML files
                for html_file in extracted_htmls:
                    html_files_to_process.append({
                        'filename': html_file['filename'],
                        'content': html_file['content'],
                        'source': f"{file.filename}/{html_file['path_in_zip']}"
                    })
                
                logger.info(f"✅ Extracted {len(extracted_htmls)} HTML files from {file.filename}")
                
            elif file.filename.lower().endswith(('.html', '.htm')):
                # Direct HTML file
                html_files_to_process.append({
                    'filename': file.filename,
                    'content': file_content,
                    'source': file.filename
                })
            else:
                logger.warning(f"⚠️  Skipping unsupported file: {file.filename}")
                investigations.append({
                    'filename': file.filename,
                    'success': False,
                    'error': 'Unsupported file type (only HTML and ZIP allowed)'
                })
        
        logger.info(f"📊 Total HTML files to process: {len(html_files_to_process)}")
        
        # Now process all HTML files
        for html_file in html_files_to_process:
            try:
                # Decode HTML content
                if isinstance(html_file['content'], bytes):
                    html_str = html_file['content'].decode('utf-8', errors='ignore')
                else:
                    html_str = html_file['content']
                
                # Extract base filename
                base_filename = extract_filename_base(html_file['filename'])
                
                # Check for duplicates and get unique name
                unique_filename = await check_duplicate_filename(db, fir_number, base_filename)
                
                logger.info(f"📄 Processing: {html_file['source']} → {unique_filename}")
                
                # Extract IPs and email from HTML
                ip_data, extracted_email = extract_ips_from_html(html_str)
                
                if not ip_data:
                    logger.warning(f"⚠️  No IPs found in {html_file['filename']}")
                    investigations.append({
                        'filename': html_file['filename'],
                        'base_name': unique_filename,
                        'success': False,
                        'error': 'No IP data found in HTML',
                        'email': extracted_email
                    })
                    continue
                
                logger.info(f"✅ Found {len(ip_data)} IPs in {html_file['filename']}")
                if extracted_email:
                    logger.info(f"📧 Email: {extracted_email}")
                
                # Create investigation with email in description
                run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{unique_filename}"
                description = f"Processed from {html_file['source']}"
                if extracted_email:
                    description += f" | Email: {extracted_email}"
                
                investigation = await CloudStorageService.create_investigation(
                    db,
                    fir_number=fir_number,
                    run_id=run_id,
                    user_id="1",  # Default user ID (no auth required)
                    total_ips=len(ip_data),
                    investigation_name=unique_filename,
                    description=description
                )
                
                inv_id = str(investigation["_id"])
                
                # Save original HTML file
                await CloudStorageService.save_file(
                    db,
                    inv_id,
                    html_file['filename'],
                    html_file['content'].encode('utf-8') if isinstance(html_file['content'], str) else html_file['content'],
                    'html',
                    'text/html',
                    f"Original HTML file from {html_file['source']}"
                )
                
                # Step 1: Create original_log.csv
                original_log_df = pd.DataFrame(ip_data)
                original_log_csv = original_log_df.to_csv(index=False).encode('utf-8')
                
                await CloudStorageService.save_file(
                    db,
                    inv_id,
                    f"{unique_filename}_original_log.csv",
                    original_log_csv,
                    'csv',
                    'text/csv',
                    'Step 1: Original log with timestamps and IPs'
                )
                
                # Save IP data to database
                for ip_record in ip_data:
                    # Skip if IP is None or empty
                    if not ip_record.get('ip'):
                        continue
                        
                    await CloudStorageService.save_ip_result(
                        db,
                        inv_id,
                        {
                            'ip': ip_record['ip'],  # Use 'ip' key, not 'ip_address'
                            'timestamp': ip_record['timestamp'],
                            'status': 'pending'
                        }
                    )
                
                # Update investigation status
                from bson import ObjectId
                await db[INVESTIGATIONS_COLLECTION].update_one(
                    {"_id": investigation["_id"]},
                    {"$set": {"status": "step_1_complete", "current_step": 1}}
                )
                
                logger.info(f"✅ Investigation created: ID={inv_id}, Name={unique_filename}")
                
                # Start auto-processing Steps 2-4 in background
                asyncio.create_task(start_auto_processing(inv_id))
                logger.info(f"🚀 Started background processing for investigation {inv_id}")
                
                investigations.append({
                    'filename': html_file['filename'],
                    'source': html_file['source'],
                    'base_name': unique_filename,
                    'investigation_id': inv_id,
                    'run_id': run_id,
                    'total_ips': len(ip_data),
                    'email': extracted_email,
                    'success': True
                })
                
            except Exception as e:
                logger.error(f"❌ Error processing {html_file['filename']}: {e}")
                investigations.append({
                    'filename': html_file['filename'],
                    'source': html_file.get('source', html_file['filename']),
                    'success': False,
                    'error': str(e)
                })
        
        # Count successes
        successful = sum(1 for inv in investigations if inv.get('success'))
        
        return {
            'success': True,
            'fir_number': fir_number,
            'total_files': len(files),
            'successful': successful,
            'failed': len(files) - successful,
            'investigations': investigations,
            'message': f"Uploaded {successful}/{len(files)} files successfully. Processing started."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fir/{fir_number:path}/investigations")
async def get_fir_investigations(
    fir_number: str,
    db=Depends(get_session)
):
    """
    Get all investigations for a FIR with progress tracking
    """
    try:
        logger.info(f"🔍 Looking for investigations with FIR number: {fir_number}")
        
        cursor = db[INVESTIGATIONS_COLLECTION].find(
            {"fir_number": fir_number}
        ).sort("created_at", -1)
        investigations = await cursor.to_list(length=None)
        
        return {
            'fir_number': fir_number,
            'total_investigations': len(investigations),
            'investigations': [
                {
                    'id': str(inv["_id"]),
                    'name': inv.get("investigation_name"),
                    'run_id': inv.get("run_id"),
                    'status': inv.get("status"),
                    'current_step': inv.get("current_step") or 1,
                    'total_steps': 7,
                    'total_ips': inv.get("total_ips", 0),
                    'completed_ips': inv.get("completed_ips", 0),
                    'remaining_ips': inv.get("total_ips", 0) - inv.get("completed_ips", 0),
                    'progress_percentage': round((inv.get("completed_ips", 0) / inv.get("total_ips", 1) * 100) if inv.get("total_ips", 0) > 0 else 0, 1),
                    'description': inv.get("description"),
                    'created_at': inv["created_at"].isoformat() if inv.get("created_at") else None,
                    'updated_at': inv["updated_at"].isoformat() if inv.get("updated_at") else None,
                }
                for inv in investigations
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting investigations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investigation/{investigation_id}/download-fully-fixed")
async def download_fully_fixed(
    investigation_id: str,
    db=Depends(get_session)
):
    """
    Download fully_fixed.csv file for an investigation
    """
    try:
        investigation = await CloudStorageService.get_investigation(db, investigation_id)
        
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        # Get fully_fixed file
        file = await CloudStorageService.get_file(
            db, 
            investigation_id, 
            f"{investigation['investigation_name']}_fully_fixed.csv"
        )
        
        if not file:
            raise HTTPException(status_code=404, detail="fully_fixed.csv not found. Processing may not be complete.")
        
        return StreamingResponse(
            io.BytesIO(file["file_data"]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={investigation['investigation_name']}_fully_fixed.csv"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/investigation/{investigation_id}")
async def delete_investigation(
    investigation_id: str,
    db=Depends(get_session)
):
    """
    Delete investigation and all associated data
    """
    try:
        from bson import ObjectId
        from models.investigation import (
            IP_LOOKUP_RESULTS_COLLECTION, FILE_STORAGE_COLLECTION,
            GENERATED_DOCUMENTS_COLLECTION, PROGRESS_TRACKING_COLLECTION,
        )
        
        investigation = await CloudStorageService.get_investigation(db, investigation_id)
        
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        fir_number = investigation["fir_number"]
        inv_name = investigation.get("investigation_name")
        inv_id_str = str(investigation["_id"])
        
        # Delete related documents
        await db[IP_LOOKUP_RESULTS_COLLECTION].delete_many({"investigation_id": inv_id_str})
        await db[FILE_STORAGE_COLLECTION].delete_many({"investigation_id": inv_id_str})
        await db[GENERATED_DOCUMENTS_COLLECTION].delete_many({"investigation_id": inv_id_str})
        await db[PROGRESS_TRACKING_COLLECTION].delete_many({"investigation_id": inv_id_str})
        await db[INVESTIGATIONS_COLLECTION].delete_one({"_id": investigation["_id"]})
        
        logger.info(f"✅ Deleted investigation {investigation_id} ({inv_name}) from FIR {fir_number}")
        
        return {
            'success': True,
            'message': f'Investigation "{inv_name}" deleted successfully',
            'investigation_id': investigation_id,
            'fir_number': fir_number
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting investigation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
