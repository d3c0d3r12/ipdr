"""
FIR Case Management Router
Handles FIR creation, IP lookup storage, and case management
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import shutil
import csv
import json

from core.db import get_db
from database import get_session
from core.config import PROCESSED_DIR
from services.fir_service import FIRService
from services.auth_service import AuthService
from models.fir_case import FIR_CASES_COLLECTION, new_fir_case
from models.investigation import INVESTIGATIONS_COLLECTION, IP_LOOKUP_RESULTS_COLLECTION
from routers.auth_secure import get_current_user


router = APIRouter()


def _find_latest_run_for_fir(fir_number: str) -> Optional[Path]:
    """Locate the most recent processed run directory belonging to a FIR.

    The enrichment pipeline writes results to processed/<timestamp>_<fir> and
    records the original FIR in processing_options.txt ("FIR: <value>"). We match
    on that line first (robust against name sanitization), then fall back to the
    directory-name suffix. Returns the latest matching run dir, or None.
    """
    base = Path(PROCESSED_DIR)
    if not base.exists():
        return None

    fir_clean = (fir_number or "").strip()
    if not fir_clean:
        return None
    safe_fir = ''.join(c if c.isalnum() or c in ('-', '_') else '-' for c in fir_clean)[:64]

    candidates = []
    for run in base.iterdir():
        if not run.is_dir():
            continue
        matched = False
        opts = run / 'processing_options.txt'
        if opts.exists():
            try:
                for line in opts.read_text(encoding='utf-8', errors='replace').splitlines():
                    if line.startswith('FIR:'):
                        matched = line.split(':', 1)[1].strip() == fir_clean
                        break
            except Exception:
                pass
        if not matched and safe_fir and run.name.endswith(f"_{safe_fir}"):
            matched = True
        if matched:
            candidates.append(run)

    if not candidates:
        return None
    # Directory names are timestamp-prefixed, so lexicographic max == most recent.
    return sorted(candidates, key=lambda p: p.name)[-1]


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
    """Get IP lookup results for a FIR from its latest processed run on disk."""
    fir_case = await db[FIR_CASES_COLLECTION].find_one({"fir_number": fir_number})
    if not fir_case:
        raise HTTPException(status_code=404, detail="FIR case not found")

    run = _find_latest_run_for_fir(fir_number)
    if run is None:
        return {"fir_number": fir_number, "total": 0, "ip_lookups": [], "run_dir": None}

    csv_file = run / 'ip_lookup_results.csv'
    if not csv_file.exists():
        return {"fir_number": fir_number, "total": 0, "ip_lookups": [], "run_dir": run.name}

    rows = []
    total = 0
    with csv_file.open('r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            total += 1
            if i < offset or len(rows) >= limit:
                continue
            country = (row.get('country') or '').strip()
            city = (row.get('city') or '').strip()
            isp = (row.get('isp') or '').strip()
            ip = row.get('ip') or ''
            # Derive the IP version from the address itself — the CSV 'ip_type' column
            # is a connection classification (Residential/Mobile/Datacenter), not the version.
            ip_type = 'IPv6' if ':' in ip else ('IPv4' if '.' in ip else '')
            rows.append({
                "ip_address": ip,
                "ip_type": ip_type or None,
                "country": country or None,
                "city": city or None,
                "region": (row.get('region') or '').strip() or None,
                "isp": isp or None,
                "latitude": row.get('latitude'),
                "longitude": row.get('longitude'),
                "lookup_status": "success" if country and country.lower() != 'unknown' else "no_data",
            })

    return {
        "fir_number": fir_number,
        "total": total,
        "ip_lookups": rows,
        "run_dir": run.name,
    }


@router.get("/{fir_number:path}/statistics")
async def get_fir_statistics(
    fir_number: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_session)
):
    """Get statistics for a FIR from its latest processed run on disk."""
    empty = {
        "fir_number": fir_number,
        "total_ip_lookups": 0,
        "unique_ips": 0,
        "unique_countries": 0,
        "unique_cities": 0,
        "total_cities": 0,
        "total_isps": 0,
        "top_isps": [],
        "run_dir": None,
    }

    run = _find_latest_run_for_fir(fir_number)
    if run is None:
        return empty

    total_records = 0
    total_unique = 0
    top_isps = []
    summary_file = run / 'ipdr_summary.json'
    if summary_file.exists():
        try:
            data = json.loads(summary_file.read_text(encoding='utf-8'))
            total_records = data.get('total_records', 0)
            total_unique = data.get('total_unique_ips', 0)
            top_isps = (data.get('by_isp') or [])[:10]
        except Exception:
            pass

    countries: set = set()
    cities: set = set()
    isps: set = set()
    row_count = 0
    csv_file = run / 'ip_lookup_results.csv'
    if csv_file.exists():
        try:
            with csv_file.open('r', encoding='utf-8', errors='replace') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row_count += 1
                    c = (row.get('country') or '').strip()
                    if c and c.lower() != 'unknown':
                        countries.add(c)
                    ci = (row.get('city') or '').strip()
                    if ci and ci.lower() != 'unknown':
                        cities.add(ci)
                    isp = (row.get('isp') or '').strip()
                    if isp:
                        isps.add(isp)
        except Exception:
            pass

    return {
        "fir_number": fir_number,
        "total_ip_lookups": total_records or row_count,
        "unique_ips": total_unique or row_count,
        "unique_countries": len(countries),
        "unique_cities": len(cities),
        "total_cities": len(cities),
        "total_isps": len(isps),
        "top_isps": top_isps,
        "run_dir": run.name,
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
