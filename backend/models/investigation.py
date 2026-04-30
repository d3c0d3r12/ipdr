"""
Investigation Models - MongoDB Collections
Handles unlimited investigations per FIR case
"""
from datetime import datetime, timezone
from bson import Binary

# ---------------------------------------------------------------------------
# Collection names
# ---------------------------------------------------------------------------
INVESTIGATIONS_COLLECTION = "investigations"
IP_LOOKUP_RESULTS_COLLECTION = "ip_lookup_results"
FILE_STORAGE_COLLECTION = "file_storage"
GENERATED_DOCUMENTS_COLLECTION = "generated_documents"
BACKGROUND_TASKS_COLLECTION = "background_tasks"
PROGRESS_TRACKING_COLLECTION = "progress_tracking"

INDEXES = {
    INVESTIGATIONS_COLLECTION: [
        {"keys": "run_id", "unique": True},
        {"keys": "fir_number"},
        {"keys": "fir_id"},
        {"keys": "user_id"},
    ],
    IP_LOOKUP_RESULTS_COLLECTION: [
        {"keys": "investigation_id"},
        {"keys": "ip_address"},
        {"keys": "isp"},
    ],
    FILE_STORAGE_COLLECTION: [
        {"keys": "investigation_id"},
    ],
    GENERATED_DOCUMENTS_COLLECTION: [
        {"keys": "investigation_id"},
        {"keys": "document_type"},
    ],
    BACKGROUND_TASKS_COLLECTION: [
        {"keys": "task_id", "unique": True},
        {"keys": "investigation_id"},
    ],
    PROGRESS_TRACKING_COLLECTION: [
        {"keys": "investigation_id", "unique": True},
    ],
}


# ---------------------------------------------------------------------------
# Document factories
# ---------------------------------------------------------------------------
def new_investigation(*, run_id, fir_id, fir_number, user_id, total_ips=0,
                      investigation_name=None, description=None, **extra):
    return {
        "run_id": run_id,
        "fir_id": fir_id,
        "fir_number": fir_number,
        "user_id": user_id,
        "investigation_name": investigation_name,
        "description": description,
        "status": "pending",
        "current_step": 1,
        "total_ips": total_ips,
        "completed_ips": 0,
        "success_count": 0,
        "failed_count": 0,
        "progress_percentage": 0.0,
        "started_at": datetime.now(timezone.utc),
        "completed_at": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


def new_ip_lookup_result(*, investigation_id, ip_address, **extra):
    return {
        "investigation_id": investigation_id,
        "ip_address": ip_address,
        "timestamp": extra.get("timestamp"),
        "country": extra.get("country"),
        "region": extra.get("region"),
        "city": extra.get("city"),
        "postal_code": extra.get("postal_code"),
        "latitude": extra.get("latitude"),
        "longitude": extra.get("longitude"),
        "timezone": extra.get("timezone"),
        "isp": extra.get("isp"),
        "lookup_source": extra.get("lookup_source", "infobyip"),
        "created_at": datetime.now(timezone.utc),
    }


def new_file_storage(*, investigation_id, file_name, file_type, file_size,
                     mime_type, file_data: bytes, description=None):
    return {
        "investigation_id": investigation_id,
        "file_name": file_name,
        "file_type": file_type,
        "file_size": file_size,
        "mime_type": mime_type,
        "file_data": Binary(file_data),
        "description": description,
        "created_at": datetime.now(timezone.utc),
    }


def new_generated_document(*, investigation_id, document_type, file_name,
                           file_data: bytes, file_size, isp_name=None):
    return {
        "investigation_id": investigation_id,
        "document_type": document_type,
        "isp_name": isp_name,
        "file_name": file_name,
        "file_data": Binary(file_data),
        "file_size": file_size,
        "created_at": datetime.now(timezone.utc),
    }


def new_background_task(*, task_id, investigation_id, user_id, total_ips, **extra):
    return {
        "task_id": task_id,
        "investigation_id": investigation_id,
        "user_id": user_id,
        "status": "pending",
        "total_ips": total_ips,
        "completed_ips": 0,
        "progress_percentage": 0.0,
        "error_message": None,
        "retry_count": 0,
        "max_retries": 3,
        "started_at": None,
        "completed_at": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


def new_progress_tracking(*, investigation_id, total_ips, completed_ips=0,
                          current_ip=None):
    return {
        "investigation_id": investigation_id,
        "current_ip": current_ip,
        "completed_ips": completed_ips,
        "total_ips": total_ips,
        "can_resume": True,
        "last_updated": datetime.now(timezone.utc),
    }
