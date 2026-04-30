"""
FIR Case Management Router
Handles FIR creation, IP lookup storage, and case management
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import shutil

from core.db import get_db
from database import get_session
from services.fir_service import FIRService
from services.auth_service import AuthService
from models.fir_case import FIR_CASES_COLLECTION, new_fir_case
from models.investigation import INVESTIGATIONS_COLLECTION, IP_LOOKUP_RESULTS_COLLECTION
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
    current_user: dict = Depends(get_current_user),
    db=Depends(get_session)
):
    """Create new FIR case"""
    if not AuthService.check_permission(current_user, "create_fir"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    existing = await db[FIR_CASES_COLLECTION].find_one({"fir_number": request.fir_number})
    if existing:
        raise HTTPException(status_code=400, detail=f"FIR {request.fir_number} already exists")
    
    doc = new_fir_case(
        fir_number=request.fir_number,
        case_title=request.case_title,
        case_description=request.case_description,
        investigating_officer=current_user.get("full_name"),
        department=current_user.get("department"),
        priority=request.priority,
        status="active",
    )
    result = await db[FIR_CASES_COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    
    return FIRResponse(
        success=True,
        message=f"FIR {request.fir_number} created successfully",
        fir_number=request.fir_number,
        data={
            "id": str(doc["_id"]),
            "fir_number": doc["fir_number"],
            "case_title": doc["case_title"],
            "status": doc["status"],
            "priority": doc["priority"],
            "created_at": str(doc["created_at"]),
        },
    )


@router.post("/store-ip-results/{fir_number}/{year}")
async def store_ip_results(
    fir_number: str,
    year: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """Store IP lookup results (CSV or JSON) into FIR database"""
    full_fir_number = f"{fir_number}/{year}"
    
    fir_case = FIRService.get_fir_case(db, full_fir_number)
    if not fir_case:
        raise HTTPException(status_code=404, detail="FIR case not found")
    
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    file_path = temp_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        if file.filename.endswith('.csv'):
            count, message = FIRService.store_ip_lookup_results_from_csv(
                db=db,
                fir_number=full_fir_number,
                csv_file_path=str(file_path),
                performed_by=current_user.get("username"),
            )
        elif file.filename.endswith('.json'):
            count, message = FIRService.store_ip_lookup_results_from_json(
                db=db,
                fir_number=full_fir_number,
                json_file_path=str(file_path),
                performed_by=current_user.get("username"),
            )
        else:
            raise HTTPException(status_code=400, detail="File must be CSV or JSON")
        
        file_path.unlink()
        return {
            "success": True,
            "message": message,
            "fir_number": full_fir_number,
            "ips_stored": count,
        }
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LIST ENDPOINT
# ============================================================================

@router.get("/")
async def list_fir_cases(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_session)
):
    """List all FIR cases with aggregated statistics from investigations"""
    query_filter = {}
    if status:
        query_filter["status"] = status
    
    # Get FIR cases
    cursor = db[FIR_CASES_COLLECTION].find(query_filter).sort("created_at", -1).skip(offset).limit(limit)
    fir_cases = await cursor.to_list(length=limit)
    
    cases_with_stats = []
    for fc in fir_cases:
        # Aggregate investigation stats for this FIR
        pipeline = [
            {"$match": {"fir_number": fc["fir_number"]}},
            {"$group": {
                "_id": None,
                "total_investigations": {"$sum": 1},
                "total_ips": {"$sum": {"$ifNull": ["$total_ips", 0]}},
                "completed_ips": {"$sum": {"$ifNull": ["$completed_ips", 0]}},
            }},
        ]
        agg = await db[INVESTIGATIONS_COLLECTION].aggregate(pipeline).to_list(length=1)
        stats = agg[0] if agg else {}
        
        cases_with_stats.append({
            "fir_number": fc["fir_number"],
            "case_title": fc.get("case_title"),
            "case_description": fc.get("case_description"),
            "status": fc.get("status"),
            "priority": fc.get("priority"),
            "total_ips": stats.get("total_ips", 0),
            "total_investigations": stats.get("total_investigations", 0),
            "completed_ips": stats.get("completed_ips", 0),
            "created_at": str(fc.get("created_at")),
            "updated_at": str(fc.get("updated_at")) if fc.get("updated_at") else str(fc.get("created_at")),
        })
    
    return {"total": len(cases_with_stats), "cases": cases_with_stats}


# ============================================================================
# PATH-BASED ENDPOINTS
# ============================================================================

@router.get("/{fir_number:path}/ip-lookups")
async def get_fir_ip_lookups(
    fir_number: str,
    limit: int = 1000,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_session)
):
    """Get IP lookup results for a FIR from all investigations"""
    fir_case = await db[FIR_CASES_COLLECTION].find_one({"fir_number": fir_number})
    if not fir_case:
        raise HTTPException(status_code=404, detail="FIR case not found")
    
    inv_cursor = db[INVESTIGATIONS_COLLECTION].find(
        {"fir_number": fir_number}, {"_id": 1}
    )
    investigations = await inv_cursor.to_list(length=None)
    investigation_ids = [str(inv["_id"]) for inv in investigations]
    
    if not investigation_ids:
        return {"fir_number": fir_number, "total": 0, "ip_lookups": []}
    
    ip_cursor = (
        db[IP_LOOKUP_RESULTS_COLLECTION]
        .find({"investigation_id": {"$in": investigation_ids}})
        .skip(offset)
        .limit(limit)
    )
    ip_lookups = await ip_cursor.to_list(length=limit)
    
    total_count = await db[IP_LOOKUP_RESULTS_COLLECTION].count_documents(
        {"investigation_id": {"$in": investigation_ids}}
    )
    
    return {
        "fir_number": fir_number,
        "total": total_count,
        "ip_lookups": [
            {
                "ip_address": ip.get("ip_address"),
                "country": ip.get("country"),
                "city": ip.get("city"),
                "region": ip.get("region"),
                "isp": ip.get("isp"),
                "latitude": ip.get("latitude"),
                "longitude": ip.get("longitude"),
                "timestamp": str(ip.get("timestamp")) if ip.get("timestamp") else None,
                "lookup_date": str(ip.get("created_at")) if ip.get("created_at") else None,
            }
            for ip in ip_lookups
        ],
    }


@router.get("/{fir_number:path}/statistics")
async def get_fir_statistics(
    fir_number: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_session)
):
    """Get comprehensive statistics for FIR"""
    investigations = await db[INVESTIGATIONS_COLLECTION].find(
        {"fir_number": fir_number}
    ).to_list(length=None)

    if not investigations:
        return {
            "fir_number": fir_number,
            "total_ip_lookups": 0,
            "unique_ips": 0,
            "total_investigations": 0,
            "unique_countries": 0,
            "total_isps": 0,
            "total_cities": 0,
            "progress_percentage": 0,
            "investigations": [],
        }

    total_ips = sum(inv.get("total_ips", 0) for inv in investigations)
    completed_ips = sum(inv.get("completed_ips", 0) for inv in investigations)
    investigation_ids = [str(inv["_id"]) for inv in investigations]

    # Count distinct values
    countries = await db[IP_LOOKUP_RESULTS_COLLECTION].distinct(
        "country", {"investigation_id": {"$in": investigation_ids}, "country": {"$ne": None}}
    )
    isps = await db[IP_LOOKUP_RESULTS_COLLECTION].distinct(
        "isp", {"investigation_id": {"$in": investigation_ids}, "isp": {"$ne": None}}
    )
    cities = await db[IP_LOOKUP_RESULTS_COLLECTION].distinct(
        "city", {"investigation_id": {"$in": investigation_ids}, "city": {"$ne": None}}
    )

    return {
        "fir_number": fir_number,
        "total_ip_lookups": completed_ips,
        "unique_ips": total_ips,
        "total_investigations": len(investigations),
        "unique_countries": len(countries),
        "total_isps": len(isps),
        "total_cities": len(cities),
        "progress_percentage": round((completed_ips / total_ips * 100) if total_ips > 0 else 0, 1),
        "investigations": [
            {
                "id": str(inv["_id"]),
                "name": inv.get("investigation_name"),
                "status": inv.get("status"),
                "total_ips": inv.get("total_ips", 0),
                "completed_ips": inv.get("completed_ips", 0),
                "progress": float(inv.get("progress_percentage", 0)),
            }
            for inv in investigations
        ],
    }


@router.get("/{fir_number:path}/timeline")
async def get_fir_timeline(
    fir_number: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_session)
):
    """Get timeline of events for FIR"""
    fir_case = await db[FIR_CASES_COLLECTION].find_one({"fir_number": fir_number})
    if not fir_case:
        raise HTTPException(status_code=404, detail="FIR case not found")
    
    investigations = await db[INVESTIGATIONS_COLLECTION].find(
        {"fir_number": fir_number}
    ).sort("created_at", -1).to_list(length=limit)
    
    timeline_events = []
    
    timeline_events.append({
        "event_type": "fir_created",
        "event_title": "FIR Case Created",
        "event_description": f"FIR {fir_number} - {fir_case.get('case_title')}",
        "performed_by": fir_case.get("investigating_officer") or "System",
        "timestamp": str(fir_case.get("created_at")),
        "importance": "high",
    })
    
    for inv in investigations:
        timeline_events.append({
            "event_type": "investigation_created",
            "event_title": f"Investigation Started: {inv.get('investigation_name')}",
            "event_description": inv.get("description") or f"Processing {inv.get('total_ips', 0)} IPs",
            "performed_by": "System",
            "timestamp": str(inv.get("created_at")),
            "importance": "normal",
        })
        
        if inv.get("status") in ("completed", "step_4_complete"):
            timeline_events.append({
                "event_type": "investigation_completed",
                "event_title": f"Investigation Completed: {inv.get('investigation_name')}",
                "event_description": f"Processed {inv.get('completed_ips', 0)}/{inv.get('total_ips', 0)} IPs successfully",
                "performed_by": "System",
                "timestamp": str(inv.get("updated_at")),
                "importance": "high",
            })
    
    timeline_events.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    
    return {"fir_number": fir_number, "events": timeline_events[:limit]}


@router.get("/{fir_number:path}")
async def get_fir_details(
    fir_number: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_session)
):
    """Get complete FIR case details with aggregated statistics"""
    fir_case = await db[FIR_CASES_COLLECTION].find_one({"fir_number": fir_number})
    if not fir_case:
        raise HTTPException(status_code=404, detail="FIR case not found")
    
    investigations = await db[INVESTIGATIONS_COLLECTION].find(
        {"fir_number": fir_number}
    ).to_list(length=None)
    
    total_ips = sum(inv.get("total_ips", 0) for inv in investigations)
    
    return {
        "fir_number": fir_case["fir_number"],
        "case_title": fir_case.get("case_title"),
        "case_description": fir_case.get("case_description"),
        "investigating_officer": fir_case.get("investigating_officer") or "Not assigned",
        "department": fir_case.get("department") or "Not specified",
        "status": fir_case.get("status"),
        "priority": fir_case.get("priority"),
        "total_ips": total_ips,
        "total_investigations": len(investigations),
        "total_suspects": 0,
        "total_evidence": 0,
        "created_at": str(fir_case.get("created_at")),
        "updated_at": str(fir_case.get("updated_at")) if fir_case.get("updated_at") else str(fir_case.get("created_at")),
    }
