"""
Cloud Storage API Router - Multi-File Per FIR System
Handles unlimited investigations per FIR with zero local storage
All data stored in MongoDB
Supports parallel processing of multiple HTML files
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query, Header
from fastapi.responses import Response, StreamingResponse
from database import get_session
from services.cloud_storage_service import CloudStorageService
from services.parallel_processor import ParallelProcessor
from utils.enhanced_cloudflare_bypass import EnhancedCloudflareBypass
from models.investigation import (
    INVESTIGATIONS_COLLECTION, IP_LOOKUP_RESULTS_COLLECTION,
    FILE_STORAGE_COLLECTION, GENERATED_DOCUMENTS_COLLECTION,
    PROGRESS_TRACKING_COLLECTION,
)
from bson import ObjectId
import io
import json
import asyncio
from datetime import datetime
import random
from typing import Optional, List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# Simple auth dependency for async routes (optional for now)
async def get_current_user_optional(
    authorization: Optional[str] = Header(None)
) -> Optional[dict]:
    """
    Optional authentication for cloud storage endpoints
    Returns None if no auth provided (for testing)
    """
    # For now, return a mock user dict for testing
    # In production, you should enforce authentication
    return {
        "_id": ObjectId("000000000000000000000001"),
        "username": "test_user",
        "email": "test@example.com",
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_ips_from_content(content: bytes) -> list:
    """Extract IPs from CSV content"""
    try:
        import pandas as pd
        df = pd.read_csv(io.BytesIO(content))
        
        # Try different column names
        ip_column = None
        for col in ['ip', 'IP', 'ip_address', 'IP Address', 'IP_Address']:
            if col in df.columns:
                ip_column = col
                break
        
        if not ip_column:
            raise ValueError("No IP column found in CSV")
        
        ips = df[ip_column].dropna().unique().tolist()
        return [str(ip).strip() for ip in ips if str(ip).strip()]
        
    except Exception as e:
        logger.error(f"Error extracting IPs: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")


async def process_ips_cloud(
    investigation_id: str,
    ips: list,
    db
):
    """
    Process IPs and save directly to cloud database
    No local files created
    """
    bypass = EnhancedCloudflareBypass(headless=True, verbose=False)
    
    try:
        for idx, ip in enumerate(ips, 1):
            try:
                # Lookup IP
                result = bypass.lookup_ip(ip)
                
                # Save to database immediately
                await CloudStorageService.save_ip_result(db, investigation_id, result)
                
                # Update progress
                await CloudStorageService.update_progress(db, investigation_id, idx, len(ips))
                await CloudStorageService.save_progress_tracking(db, investigation_id, idx, len(ips), ip)
                
                logger.info(f"✅ Processed IP {idx}/{len(ips)}: {ip}")
                
            except Exception as e:
                logger.error(f"❌ Error processing IP {ip}: {e}")
                # Save error result
                await CloudStorageService.save_ip_result(db, investigation_id, {
                    'ip': ip,
                    'country': 'Error',
                    'error': str(e)
                })
        
        # Mark investigation as completed
        await CloudStorageService.update_progress(db, investigation_id, len(ips), len(ips))
        
        # Generate and save CSV
        csv_bytes = await CloudStorageService.get_ip_results_as_csv(db, investigation_id)
        await CloudStorageService.save_file(
            db, investigation_id, 'ip_lookup_results.csv',
            csv_bytes, 'csv', 'text/csv',
            'IP lookup results'
        )
        
        logger.info(f"✅ Investigation {investigation_id} completed!")
        
    finally:
        bypass.close()


# ============================================================================
# CLOUD INVESTIGATION ENDPOINTS
# ============================================================================

@router.post("/start-cloud")
async def start_cloud_investigation(
    file: UploadFile = File(...),
    fir_number: str = Form(...),
    investigation_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db=Depends(get_session),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Start IP lookup with cloud storage (no local files)
    """
    try:
        run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(100, 999)}"
        content = await file.read()
        ips = extract_ips_from_content(content)
        
        if not ips:
            raise HTTPException(status_code=400, detail="No IPs found in file")
        
        logger.info(f"📊 Starting cloud investigation for FIR {fir_number}: {len(ips)} IPs")
        
        investigation = await CloudStorageService.create_investigation(
            db, 
            fir_number=fir_number,
            run_id=run_id, 
            user_id=str(current_user["_id"]), 
            total_ips=len(ips),
            investigation_name=investigation_name,
            description=description
        )
        
        inv_id = str(investigation["_id"])
        
        await CloudStorageService.save_file(
            db, inv_id, file.filename or 'original_log.csv', 
            content, 'csv', 'text/csv',
            'Original uploaded file'
        )
        
        logger.info(f"✅ Investigation created: ID={inv_id}, FIR={fir_number}")
        
        asyncio.create_task(process_ips_cloud(inv_id, ips, db))
        
        return {
            "success": True,
            "investigation_id": inv_id,
            "run_id": run_id,
            "fir_number": fir_number,
            "total_ips": len(ips),
            "investigation_name": investigation.get("investigation_name"),
            "message": "Investigation started in cloud - no local files created!",
            "note": "Processing in background. Use /investigation/{id}/status to check progress."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error starting cloud investigation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investigation/{investigation_id}/status")
async def get_investigation_status(
    investigation_id: str,
    db=Depends(get_session),
    current_user: dict = Depends(get_current_user_optional)
):
    """Get investigation status and progress"""
    try:
        investigation = await CloudStorageService.get_investigation(db, investigation_id)
        
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        inv_id = str(investigation["_id"])
        progress = await db[PROGRESS_TRACKING_COLLECTION].find_one(
            {"investigation_id": inv_id}
        )
        
        return {
            "investigation_id": inv_id,
            "run_id": investigation.get("run_id"),
            "fir_number": investigation.get("fir_number"),
            "investigation_name": investigation.get("investigation_name"),
            "status": investigation.get("status"),
            "total_ips": investigation.get("total_ips", 0),
            "completed_ips": investigation.get("completed_ips", 0),
            "success_count": investigation.get("success_count", 0),
            "progress_percentage": float(investigation.get("progress_percentage", 0)),
            "current_ip": progress.get("current_ip") if progress else None,
            "started_at": investigation["started_at"].isoformat() if investigation.get("started_at") else None,
            "completed_at": investigation["completed_at"].isoformat() if investigation.get("completed_at") else None,
            "can_resume": progress.get("can_resume", False) if progress else False,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting investigation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FIR MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/fir/{fir_number}/statistics")
async def get_fir_statistics(
    fir_number: str,
    db=Depends(get_session),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Get aggregated statistics for all investigations in a FIR
    Shows all uploads for the same FIR number
    """
    try:
        stats = await CloudStorageService.get_fir_statistics(db, fir_number)
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error getting FIR statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fir/{fir_number}/investigations")
async def get_fir_investigations(
    fir_number: str,
    db=Depends(get_session),
    current_user: dict = Depends(get_current_user_optional)
):
    """Get all investigations for a FIR"""
    try:
        investigations = await CloudStorageService.get_fir_investigations(db, fir_number)
        
        return {
            "fir_number": fir_number,
            "total_investigations": len(investigations),
            "investigations": [
                {
                    "id": str(inv["_id"]),
                    "run_id": inv.get("run_id"),
                    "investigation_name": inv.get("investigation_name"),
                    "description": inv.get("description"),
                    "status": inv.get("status"),
                    "total_ips": inv.get("total_ips", 0),
                    "completed_ips": inv.get("completed_ips", 0),
                    "progress_percentage": float(inv.get("progress_percentage", 0)),
                    "created_at": inv["created_at"].isoformat() if inv.get("created_at") else None,
                    "completed_at": inv["completed_at"].isoformat() if inv.get("completed_at") else None,
                }
                for inv in investigations
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting FIR investigations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FILE DOWNLOAD ENDPOINTS
# ============================================================================

@router.get("/investigation/{investigation_id}/results/csv")
async def download_investigation_results(
    investigation_id: str,
    db=Depends(get_session),
    current_user: dict = Depends(get_current_user_optional)
):
    """Download IP results as CSV for single investigation"""
    try:
        investigation = await CloudStorageService.get_investigation(db, investigation_id)
        
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        csv_bytes = await CloudStorageService.get_ip_results_as_csv(db, investigation_id)
        
        filename = f"ip_results_{investigation.get('run_id')}.csv"
        
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error downloading results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fir/{fir_number}/all-results/csv")
async def download_all_fir_results(
    fir_number: str,
    db=Depends(get_session),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Download ALL IP results from ALL investigations for a FIR
    Combines data from multiple uploads
    """
    try:
        csv_bytes = await CloudStorageService.get_all_fir_ip_results_as_csv(db, fir_number)
        
        filename = f"fir_{fir_number.replace('/', '-')}_all_results.csv"
        
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"❌ Error downloading FIR results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investigation/{investigation_id}/file/{file_name}")
async def download_file(
    investigation_id: str,
    file_name: str,
    db=Depends(get_session),
    current_user: dict = Depends(get_current_user_optional)
):
    """Download specific file from investigation"""
    try:
        file = await CloudStorageService.get_file(db, investigation_id, file_name)
        
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        return Response(
            content=file["file_data"],
            media_type=file.get("mime_type", "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename={file['file_name']}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investigation/{investigation_id}/files")
async def list_investigation_files(
    investigation_id: str,
    db=Depends(get_session),
    current_user: dict = Depends(get_current_user_optional)
):
    """List all files for an investigation"""
    try:
        files = await CloudStorageService.get_investigation_files(db, investigation_id)
        
        return {
            "investigation_id": investigation_id,
            "total_files": len(files),
            "files": [
                {
                    "id": str(f["_id"]),
                    "file_name": f.get("file_name"),
                    "file_type": f.get("file_type"),
                    "file_size": f.get("file_size"),
                    "mime_type": f.get("mime_type"),
                    "description": f.get("description"),
                    "created_at": f["created_at"].isoformat() if f.get("created_at") else None,
                }
                for f in files
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get("/my-investigations")
async def get_my_investigations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db=Depends(get_session),
    current_user: dict = Depends(get_current_user_optional)
):
    """Get all investigations for current user"""
    try:
        user_id = str(current_user["_id"])
        cursor = (
            db[INVESTIGATIONS_COLLECTION]
            .find({"user_id": user_id})
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )
        investigations = await cursor.to_list(length=limit)
        
        return {
            "total": len(investigations),
            "limit": limit,
            "offset": offset,
            "investigations": [
                {
                    "id": str(inv["_id"]),
                    "run_id": inv.get("run_id"),
                    "fir_number": inv.get("fir_number"),
                    "investigation_name": inv.get("investigation_name"),
                    "status": inv.get("status"),
                    "total_ips": inv.get("total_ips", 0),
                    "completed_ips": inv.get("completed_ips", 0),
                    "progress_percentage": float(inv.get("progress_percentage", 0)),
                    "created_at": inv["created_at"].isoformat() if inv.get("created_at") else None,
                }
                for inv in investigations
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting investigations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/investigation/{investigation_id}")
async def delete_investigation(
    investigation_id: str,
    db=Depends(get_session),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Delete investigation and all associated data
    """
    try:
        investigation = await CloudStorageService.get_investigation(db, investigation_id)
        
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        if investigation.get("user_id") != str(current_user["_id"]):
            raise HTTPException(status_code=403, detail="Not authorized")
        
        inv_id_str = str(investigation["_id"])
        
        # Delete related documents
        await db[IP_LOOKUP_RESULTS_COLLECTION].delete_many({"investigation_id": inv_id_str})
        await db[FILE_STORAGE_COLLECTION].delete_many({"investigation_id": inv_id_str})
        await db[GENERATED_DOCUMENTS_COLLECTION].delete_many({"investigation_id": inv_id_str})
        await db[PROGRESS_TRACKING_COLLECTION].delete_many({"investigation_id": inv_id_str})
        await db[INVESTIGATIONS_COLLECTION].delete_one({"_id": investigation["_id"]})
        
        logger.info(f"✅ Deleted investigation {investigation_id}")
        
        return {
            "success": True,
            "message": "Investigation and all associated data deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting investigation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PARALLEL PROCESSING ENDPOINTS
# ============================================================================

@router.post("/process-multiple-html")
async def process_multiple_html_files(
    files: List[UploadFile] = File(...),
    fir_number: str = Form(...),
    perform_ip_lookup: bool = Form(False),
    db=Depends(get_session),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Process multiple HTML files in parallel (up to 5 at once)
    
    Features:
    - Extracts unique ID from each HTML file (email, subscriber ID, or filename)
    - Processes up to 5 files simultaneously
    - Creates separate investigation for each file
    - Names results using unique IDs
    - Stores everything in cloud database
    - All files linked to same FIR number
    
    Args:
        files: List of HTML files to process
        fir_number: FIR number for grouping
        perform_ip_lookup: Whether to perform actual IP lookups (default: False)
    
    Returns:
        Processing results with investigation IDs and unique identifiers
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 files allowed per request")
        
        logger.info(f"🚀 Starting parallel processing of {len(files)} HTML files for FIR {fir_number}")
        
        # Read all files
        html_contents = []
        filenames = []
        
        for file in files:
            content = await file.read()
            html_contents.append(content)
            filenames.append(file.filename or f"file_{len(filenames)}.html")
        
        # Initialize parallel processor
        processor = ParallelProcessor(max_workers=5)
        
        # Process files
        if perform_ip_lookup:
            results = await processor.process_with_ip_lookup(
                html_contents, filenames, fir_number, str(current_user["_id"]), db, perform_lookup=True
            )
        else:
            results = await processor.process_multiple_files(
                html_contents, filenames, fir_number, str(current_user["_id"]), db
            )
        
        logger.info(f"✅ Parallel processing complete: {results['processed']}/{results['total_files']} successful")
        
        return {
            "success": True,
            "fir_number": fir_number,
            "total_files": results['total_files'],
            "processed": results['processed'],
            "failed": results['failed'],
            "investigations": results['investigations'],
            "errors": results['errors'],
            "message": f"Processed {results['processed']} files successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in parallel processing: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
