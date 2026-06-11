"""
FIR Case Management - MongoDB Collections
"""
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Collection names
# ---------------------------------------------------------------------------
FIR_CASES_COLLECTION = "fir_cases"
FIR_IP_LOOKUPS_COLLECTION = "fir_ip_lookups"
FIR_EVIDENCE_COLLECTION = "fir_evidence"
FIR_SUSPECTS_COLLECTION = "fir_suspects"
FIR_TIMELINE_COLLECTION = "fir_timeline"

INDEXES = {
    FIR_CASES_COLLECTION: [
        {"keys": "fir_number", "unique": True},
        {"keys": "user_id"},
    ],
    FIR_IP_LOOKUPS_COLLECTION: [
        {"keys": "fir_number"},
        {"keys": "ip_address"},
    ],
    FIR_EVIDENCE_COLLECTION: [
        {"keys": "fir_number"},
    ],
    FIR_SUSPECTS_COLLECTION: [
        {"keys": "fir_number"},
    ],
    FIR_TIMELINE_COLLECTION: [
        {"keys": "fir_number"},
        {"keys": "event_timestamp"},
    ],
}


def new_fir_case(*, fir_number, case_title=None, case_description=None,
                 investigating_officer=None, department=None,
                 status="active", priority="medium", user_id=None, **extra):
    return {
        "fir_number": fir_number,
        "case_title": case_title,
        "case_description": case_description,
        "investigating_officer": investigating_officer,
        "department": department,
        "status": status,
        "priority": priority,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
        "closed_at": None,
        "tags": extra.get("tags"),
        "notes": extra.get("notes"),
    }


def new_fir_ip_lookup(*, fir_number, ip_address=None, **extra):
    return {
        "fir_number": fir_number,
        "ip_address": ip_address,
        "ip_version": extra.get("ip_version"),
        "country": extra.get("country"),
        "country_code": extra.get("country_code"),
        "city": extra.get("city"),
        "region": extra.get("region"),
        "latitude": extra.get("latitude"),
        "longitude": extra.get("longitude"),
        "timezone": extra.get("timezone"),
        "postal_code": extra.get("postal_code"),
        "isp": extra.get("isp"),
        "organization": extra.get("organization"),
        "asn": extra.get("asn"),
        "timestamp": extra.get("timestamp"),
        "activity_type": extra.get("activity_type"),
        "lookup_date": datetime.now(timezone.utc),
        "data_source": extra.get("data_source", "infobyip"),
        "raw_data": extra.get("raw_data"),
        "is_suspicious": False,
        "risk_score": 0,
        "notes": None,
    }


def new_fir_evidence(*, fir_number, file_name=None, file_path=None,
                     file_type=None, file_size=None, uploaded_by=None, **extra):
    return {
        "fir_number": fir_number,
        "file_name": file_name,
        "file_type": file_type,
        "file_size": file_size,
        "file_path": file_path,
        "file_hash": extra.get("file_hash"),
        "uploaded_by": uploaded_by,
        "uploaded_at": datetime.now(timezone.utc),
        "description": extra.get("description"),
        "tags": extra.get("tags"),
        "is_processed": False,
        "processing_status": extra.get("processing_status", "pending"),
        "processing_notes": None,
    }


def new_fir_timeline(*, fir_number, event_type, event_title,
                     event_description=None, performed_by=None,
                     event_data=None, importance="normal"):
    return {
        "fir_number": fir_number,
        "event_type": event_type,
        "event_title": event_title,
        "event_description": event_description,
        "event_data": event_data,
        "performed_by": performed_by,
        "event_timestamp": datetime.now(timezone.utc),
        "importance": importance,
        "tags": None,
    }
