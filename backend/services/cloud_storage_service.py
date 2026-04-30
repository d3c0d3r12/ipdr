"""
Cloud Storage Service - MongoDB Storage for Multiple Files per FIR
Handles unlimited investigations per FIR case with proper relationships
"""
from bson import ObjectId, Binary
from models.investigation import (
    INVESTIGATIONS_COLLECTION, IP_LOOKUP_RESULTS_COLLECTION,
    FILE_STORAGE_COLLECTION, GENERATED_DOCUMENTS_COLLECTION,
    PROGRESS_TRACKING_COLLECTION,
    new_investigation, new_ip_lookup_result, new_file_storage,
    new_generated_document, new_progress_tracking,
)
from models.fir_case import FIR_CASES_COLLECTION, new_fir_case
import io
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timezone


class CloudStorageService:
    """Service for storing data in MongoDB instead of local files"""
    
    # ============================================================================
    # FIR CASE MANAGEMENT
    # ============================================================================
    
    @staticmethod
    async def get_or_create_fir(db, fir_number: str, user_id) -> dict:
        """Get existing FIR or create new one"""
        fir_case = await db[FIR_CASES_COLLECTION].find_one({"fir_number": fir_number})
        
        if not fir_case:
            doc = new_fir_case(
                fir_number=fir_number,
                case_title=f"FIR {fir_number}",
                status="active",
            )
            result = await db[FIR_CASES_COLLECTION].insert_one(doc)
            doc["_id"] = result.inserted_id
            fir_case = doc
        
        return fir_case
    
    @staticmethod
    async def get_fir_investigations(db, fir_number: str) -> List[dict]:
        """Get all investigations for a FIR"""
        cursor = db[INVESTIGATIONS_COLLECTION].find(
            {"fir_number": fir_number}
        ).sort("created_at", -1)
        return await cursor.to_list(length=None)
    
    @staticmethod
    async def get_fir_statistics(db, fir_number: str) -> Dict:
        """Get aggregated statistics for all investigations in a FIR"""
        investigations = await CloudStorageService.get_fir_investigations(db, fir_number)
        
        total_ips = sum(inv.get("total_ips", 0) for inv in investigations)
        completed_ips = sum(inv.get("completed_ips", 0) for inv in investigations)
        success_count = sum(inv.get("success_count", 0) for inv in investigations)
        
        return {
            "fir_number": fir_number,
            "total_investigations": len(investigations),
            "total_ips": total_ips,
            "completed_ips": completed_ips,
            "success_count": success_count,
            "investigations": [
                {
                    "id": str(inv["_id"]),
                    "run_id": inv.get("run_id"),
                    "investigation_name": inv.get("investigation_name"),
                    "status": inv.get("status"),
                    "total_ips": inv.get("total_ips", 0),
                    "completed_ips": inv.get("completed_ips", 0),
                    "progress_percentage": float(inv.get("progress_percentage", 0)),
                    "created_at": inv["created_at"].isoformat() if inv.get("created_at") else None,
                }
                for inv in investigations
            ],
        }
    
    # ============================================================================
    # INVESTIGATION MANAGEMENT
    # ============================================================================
    
    @staticmethod
    async def create_investigation(db, fir_number: str, run_id: str,
                                    user_id, total_ips: int,
                                    investigation_name: str = None,
                                    description: str = None) -> dict:
        """Create new investigation for a FIR"""
        fir_case = await CloudStorageService.get_or_create_fir(db, fir_number, user_id)
        
        doc = new_investigation(
            run_id=run_id,
            fir_id=str(fir_case["_id"]),
            fir_number=fir_number,
            user_id=str(user_id) if not isinstance(user_id, str) else user_id,
            total_ips=total_ips,
            investigation_name=investigation_name or f"Investigation {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
            description=description,
        )
        
        result = await db[INVESTIGATIONS_COLLECTION].insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc
    
    @staticmethod
    async def get_investigation(db, investigation_id) -> Optional[dict]:
        """Get investigation by ID"""
        if isinstance(investigation_id, str):
            investigation_id = ObjectId(investigation_id)
        return await db[INVESTIGATIONS_COLLECTION].find_one({"_id": investigation_id})
    
    @staticmethod
    async def get_investigation_by_run_id(db, run_id: str) -> Optional[dict]:
        """Get investigation by run_id"""
        return await db[INVESTIGATIONS_COLLECTION].find_one({"run_id": run_id})
    
    # ============================================================================
    # IP RESULTS STORAGE
    # ============================================================================
    
    @staticmethod
    async def save_ip_result(db, investigation_id, ip_data: dict):
        """Save single IP lookup result to database"""
        inv_id = str(investigation_id) if isinstance(investigation_id, ObjectId) else str(investigation_id)
        doc = new_ip_lookup_result(
            investigation_id=inv_id,
            ip_address=ip_data.get("ip"),
            timestamp=ip_data.get("timestamp"),
            country=ip_data.get("country"),
            region=ip_data.get("region"),
            city=ip_data.get("city"),
            isp=ip_data.get("isp"),
            postal_code=ip_data.get("postal_code"),
            latitude=ip_data.get("latitude"),
            longitude=ip_data.get("longitude"),
            timezone=ip_data.get("timezone"),
            lookup_source=ip_data.get("source", "infobyip"),
        )
        result = await db[IP_LOOKUP_RESULTS_COLLECTION].insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc
    
    @staticmethod
    async def save_ip_results_batch(db, investigation_id, ip_data_list: List[dict]):
        """Save multiple IP results at once (faster)"""
        inv_id = str(investigation_id) if isinstance(investigation_id, ObjectId) else str(investigation_id)
        docs = [
            new_ip_lookup_result(
                investigation_id=inv_id,
                ip_address=ip_data.get("ip"),
                timestamp=ip_data.get("timestamp"),
                country=ip_data.get("country"),
                region=ip_data.get("region"),
                city=ip_data.get("city"),
                isp=ip_data.get("isp"),
                postal_code=ip_data.get("postal_code"),
                latitude=ip_data.get("latitude"),
                longitude=ip_data.get("longitude"),
                timezone=ip_data.get("timezone"),
                lookup_source=ip_data.get("source", "infobyip"),
            )
            for ip_data in ip_data_list
        ]
        if docs:
            await db[IP_LOOKUP_RESULTS_COLLECTION].insert_many(docs)
    
    @staticmethod
    async def get_ip_results(db, investigation_id) -> List[dict]:
        """Get all IP results for an investigation"""
        inv_id = str(investigation_id) if isinstance(investigation_id, ObjectId) else str(investigation_id)
        cursor = db[IP_LOOKUP_RESULTS_COLLECTION].find(
            {"investigation_id": inv_id}
        ).sort("created_at", 1)
        return await cursor.to_list(length=None)
    
    @staticmethod
    async def get_ip_results_as_csv(db, investigation_id) -> bytes:
        """Get IP results as CSV bytes"""
        results = await CloudStorageService.get_ip_results(db, investigation_id)
        
        data = [
            {
                "ip": r.get("ip_address"),
                "timestamp": r.get("timestamp"),
                "country": r.get("country"),
                "region": r.get("region"),
                "city": r.get("city"),
                "isp": r.get("isp"),
                "postal_code": r.get("postal_code"),
                "latitude": r.get("latitude"),
                "longitude": r.get("longitude"),
                "timezone": r.get("timezone"),
            }
            for r in results
        ]
        
        df = pd.DataFrame(data)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue().encode("utf-8")
    
    @staticmethod
    async def get_all_fir_ip_results_as_csv(db, fir_number: str) -> bytes:
        """Get ALL IP results from ALL investigations for a FIR as CSV"""
        investigations = await CloudStorageService.get_fir_investigations(db, fir_number)
        
        all_results = []
        for inv in investigations:
            results = await CloudStorageService.get_ip_results(db, inv["_id"])
            for r in results:
                all_results.append({
                    "investigation_name": inv.get("investigation_name"),
                    "run_id": inv.get("run_id"),
                    "ip": r.get("ip_address"),
                    "timestamp": r.get("timestamp"),
                    "country": r.get("country"),
                    "region": r.get("region"),
                    "city": r.get("city"),
                    "isp": r.get("isp"),
                    "postal_code": r.get("postal_code"),
                    "latitude": r.get("latitude"),
                    "longitude": r.get("longitude"),
                    "timezone": r.get("timezone"),
                })
        
        df = pd.DataFrame(all_results)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue().encode("utf-8")
    
    # ============================================================================
    # FILE STORAGE
    # ============================================================================
    
    @staticmethod
    async def save_file(db, investigation_id, file_name: str,
                        file_data: bytes, file_type: str, mime_type: str,
                        description: str = None):
        """Save file (CSV, DOCX, PDF, ZIP) to database"""
        inv_id = str(investigation_id) if isinstance(investigation_id, ObjectId) else str(investigation_id)
        doc = new_file_storage(
            investigation_id=inv_id,
            file_name=file_name,
            file_type=file_type,
            file_size=len(file_data),
            mime_type=mime_type,
            file_data=file_data,
            description=description,
        )
        result = await db[FILE_STORAGE_COLLECTION].insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc
    
    @staticmethod
    async def get_file(db, investigation_id, file_name: str):
        """Retrieve file from database"""
        inv_id = str(investigation_id) if isinstance(investigation_id, ObjectId) else str(investigation_id)
        return await db[FILE_STORAGE_COLLECTION].find_one({
            "investigation_id": inv_id,
            "file_name": file_name,
        })
    
    @staticmethod
    async def get_investigation_files(db, investigation_id) -> List[dict]:
        """Get all files for an investigation"""
        inv_id = str(investigation_id) if isinstance(investigation_id, ObjectId) else str(investigation_id)
        cursor = db[FILE_STORAGE_COLLECTION].find(
            {"investigation_id": inv_id}
        ).sort("created_at", 1)
        return await cursor.to_list(length=None)
    
    # ============================================================================
    # PROGRESS TRACKING
    # ============================================================================
    
    @staticmethod
    async def update_progress(db, investigation_id, completed_ips: int,
                               total_ips: int, current_ip: str = None):
        """Update investigation progress"""
        if isinstance(investigation_id, str):
            investigation_id = ObjectId(investigation_id)
        
        progress = (completed_ips / total_ips * 100) if total_ips > 0 else 0
        
        update_fields = {
            "completed_ips": completed_ips,
            "progress_percentage": progress,
            "status": "in_progress" if completed_ips < total_ips else "completed",
            "updated_at": datetime.now(timezone.utc),
        }
        if completed_ips >= total_ips:
            update_fields["completed_at"] = datetime.now(timezone.utc)
        
        await db[INVESTIGATIONS_COLLECTION].update_one(
            {"_id": investigation_id},
            {"$set": update_fields},
        )
    
    @staticmethod
    async def save_progress_tracking(db, investigation_id, completed_ips: int,
                                      total_ips: int, current_ip: str = None):
        """Save progress for resume capability"""
        inv_id = str(investigation_id) if isinstance(investigation_id, ObjectId) else str(investigation_id)
        
        existing = await db[PROGRESS_TRACKING_COLLECTION].find_one(
            {"investigation_id": inv_id}
        )
        
        if existing:
            await db[PROGRESS_TRACKING_COLLECTION].update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "completed_ips": completed_ips,
                    "current_ip": current_ip,
                    "last_updated": datetime.now(timezone.utc),
                }},
            )
        else:
            doc = new_progress_tracking(
                investigation_id=inv_id,
                total_ips=total_ips,
                completed_ips=completed_ips,
                current_ip=current_ip,
            )
            await db[PROGRESS_TRACKING_COLLECTION].insert_one(doc)
    
    # ============================================================================
    # GENERATED DOCUMENTS
    # ============================================================================
    
    @staticmethod
    async def save_document(db, investigation_id, document_type: str,
                            file_name: str, file_data: bytes,
                            isp_name: str = None):
        """Save generated document (ISP letter, report, etc.)"""
        inv_id = str(investigation_id) if isinstance(investigation_id, ObjectId) else str(investigation_id)
        doc = new_generated_document(
            investigation_id=inv_id,
            document_type=document_type,
            file_name=file_name,
            file_data=file_data,
            file_size=len(file_data),
            isp_name=isp_name,
        )
        result = await db[GENERATED_DOCUMENTS_COLLECTION].insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc
    
    @staticmethod
    async def get_investigation_documents(db, investigation_id) -> List[dict]:
        """Get all generated documents for an investigation"""
        inv_id = str(investigation_id) if isinstance(investigation_id, ObjectId) else str(investigation_id)
        cursor = db[GENERATED_DOCUMENTS_COLLECTION].find(
            {"investigation_id": inv_id}
        ).sort("created_at", 1)
        return await cursor.to_list(length=None)
