"""
FIR Case Management Router
Handles FIR creation, IP lookup storage, and case management
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import shutil

from core.db import get_db
from services.fir_service import FIRService
from services.auth_service import AuthService
from models.user_auth import User
from routers.auth_secure import get_current_user


router = APIRouter()


# Pydantic models
class CreateFIRRequest(BaseModel):
    fir_number: str
    case_title: str
    case_description: Optional[str] = None
    priority: str = "medium"


class FIRResponse(BaseModel):
    success: bool
    message: str
    fir_number: str
    data: Optional[dict] = None


@router.post("/create", response_model=FIRResponse)
async def create_fir(
    request: CreateFIRRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new FIR case
    
    Requires: investigator role or higher
    """
    
    # Check permission
    if not AuthService.check_permission(current_user, "create_fir"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Create FIR case
    fir_case, message = FIRService.create_fir_case(
        db=db,
        fir_number=request.fir_number,
        case_title=request.case_title,
        case_description=request.case_description,
        investigating_officer=current_user.full_name,
        department=current_user.department,
        priority=request.priority,
        created_by=current_user.username
    )
    
    if not fir_case:
        raise HTTPException(status_code=400, detail=message)
    
    return FIRResponse(
        success=True,
        message=message,
        fir_number=fir_case.fir_number,
        data={
            "id": fir_case.id,
            "fir_number": fir_case.fir_number,
            "case_title": fir_case.case_title,
            "status": fir_case.status,
            "priority": fir_case.priority,
            "created_at": str(fir_case.created_at)
        }
    )


@router.post("/store-ip-results/{fir_number}/{year}")
async def store_ip_results(
    fir_number: str,
    year: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Store IP lookup results (CSV or JSON) into FIR database
    
    This automatically stores all IP lookup data in the database
    associated with the FIR number.
    """
    
    # Combine FIR number and year
    full_fir_number = f"{fir_number}/{year}"
    
    # Check if FIR exists
    fir_case = FIRService.get_fir_case(db, full_fir_number)
    if not fir_case:
        raise HTTPException(status_code=404, detail="FIR case not found")
    
    # Save uploaded file temporarily
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    
    file_path = temp_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Determine file type and store results
    try:
        if file.filename.endswith('.csv'):
            count, message = FIRService.store_ip_lookup_results_from_csv(
                db=db,
                fir_number=full_fir_number,
                csv_file_path=str(file_path),
                performed_by=current_user.username
            )
        elif file.filename.endswith('.json'):
            count, message = FIRService.store_ip_lookup_results_from_json(
                db=db,
                fir_number=full_fir_number,
                json_file_path=str(file_path),
                performed_by=current_user.username
            )
        else:
            raise HTTPException(status_code=400, detail="File must be CSV or JSON")
        
        # Clean up temp file
        file_path.unlink()
        
        return {
            "success": True,
            "message": message,
            "fir_number": full_fir_number,
            "ips_stored": count
        }
        
    except Exception as e:
        # Clean up temp file
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{fir_number}/ip-lookups")
async def get_fir_ip_lookups(
    fir_number: str,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get IP lookup results for a FIR"""
    
    # Check if FIR exists
    fir_case = FIRService.get_fir_case(db, fir_number)
    if not fir_case:
        raise HTTPException(status_code=404, detail="FIR case not found")
    
    # Get IP lookups
    ip_lookups = FIRService.get_ip_lookups(db, fir_number, limit, offset)
    
    return {
        "fir_number": fir_number,
        "total": len(ip_lookups),
        "results": [
            {
                "ip_address": ip.ip_address,
                "country": ip.country,
                "city": ip.city,
                "region": ip.region,
                "isp": ip.isp,
                "latitude": ip.latitude,
                "longitude": ip.longitude,
                "lookup_date": str(ip.lookup_date)
            }
            for ip in ip_lookups
        ]
    }


@router.get("/{fir_number}/statistics")
async def get_fir_statistics(
    fir_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive statistics for FIR"""
    
    stats = FIRService.get_fir_statistics(db, fir_number)
    
    if not stats:
        raise HTTPException(status_code=404, detail="FIR case not found")
    
    return stats


@router.get("/{fir_number}/timeline")
async def get_fir_timeline(
    fir_number: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get timeline of events for FIR"""
    
    timeline = FIRService.get_timeline(db, fir_number, limit)
    
    return {
        "fir_number": fir_number,
        "events": [
            {
                "event_type": event.event_type,
                "event_title": event.event_title,
                "event_description": event.event_description,
                "performed_by": event.performed_by,
                "timestamp": str(event.event_timestamp),
                "importance": event.importance
            }
            for event in timeline
        ]
    }


@router.get("/{fir_number}")
async def get_fir_details(
    fir_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete FIR case details"""
    
    fir_case = FIRService.get_fir_case(db, fir_number)
    
    if not fir_case:
        raise HTTPException(status_code=404, detail="FIR case not found")
    
    return {
        "fir_number": fir_case.fir_number,
        "case_title": fir_case.case_title,
        "case_description": fir_case.case_description,
        "investigating_officer": fir_case.investigating_officer,
        "department": fir_case.department,
        "status": fir_case.status,
        "priority": fir_case.priority,
        "total_ips": fir_case.total_ips,
        "total_suspects": fir_case.total_suspects,
        "total_evidence": fir_case.total_evidence,
        "created_at": str(fir_case.created_at),
        "updated_at": str(fir_case.updated_at)
    }


@router.get("/")
async def list_fir_cases(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all FIR cases (with optional status filter)"""
    
    from models.fir_case import FIRCase
    
    query = db.query(FIRCase)
    
    if status:
        query = query.filter(FIRCase.status == status)
    
    cases = query.offset(offset).limit(limit).all()
    
    return {
        "total": len(cases),
        "cases": [
            {
                "fir_number": case.fir_number,
                "case_title": case.case_title,
                "status": case.status,
                "priority": case.priority,
                "investigating_officer": case.investigating_officer,
                "total_ips": case.total_ips,
                "created_at": str(case.created_at)
            }
            for case in cases
        ]
    }
