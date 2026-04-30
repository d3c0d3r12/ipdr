"""
FIR Case Management Service
Handles all FIR-related operations including storing IP lookup results
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json
import csv
from pathlib import Path

from models.fir_case import (
    FIR_CASES_COLLECTION, FIR_IP_LOOKUPS_COLLECTION,
    FIR_EVIDENCE_COLLECTION, FIR_TIMELINE_COLLECTION,
    new_fir_case, new_fir_ip_lookup, new_fir_evidence, new_fir_timeline,
)


class FIRService:
    """Service for managing FIR cases"""
    
    @staticmethod
    def create_fir_case(db, fir_number, case_title, investigating_officer,
                        department="Delhi Police Cyber Cell",
                        case_description=None, priority="medium",
                        created_by=None):
        """Create new FIR case"""
        existing = db[FIR_CASES_COLLECTION].find_one({"fir_number": fir_number})
        if existing:
            return existing, "FIR case already exists"
        
        doc = new_fir_case(
            fir_number=fir_number,
            case_title=case_title,
            case_description=case_description,
            investigating_officer=investigating_officer,
            department=department,
            priority=priority,
            status="active",
        )
        
        result = db[FIR_CASES_COLLECTION].insert_one(doc)
        doc["_id"] = result.inserted_id
        
        FIRService.add_timeline_event(
            db=db,
            fir_number=fir_number,
            event_type="case_created",
            event_title="FIR Case Created",
            event_description=f"New FIR case {fir_number} created",
            performed_by=created_by or investigating_officer,
            importance="high",
        )
        
        return doc, "FIR case created successfully"
    
    @staticmethod
    def get_fir_case(db, fir_number):
        """Get FIR case by number"""
        return db[FIR_CASES_COLLECTION].find_one({"fir_number": fir_number})
    
    @staticmethod
    def store_ip_lookup_results_from_csv(db, fir_number, csv_file_path,
                                         performed_by=None):
        """Store IP lookup results from CSV file into database"""
        fir_case = FIRService.get_fir_case(db, fir_number)
        if not fir_case:
            return 0, "FIR case not found"
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception as e:
            return 0, f"Failed to read CSV: {str(e)}"
        
        docs = []
        for row in rows:
            try:
                ip_version = "IPv6" if ':' in row.get('ip', '') else "IPv4"
                country = row.get('country', '')
                country_code = None
                if '(' in country and ')' in country:
                    country_code = country.split('(')[1].split(')')[0]
                    country = country.split('(')[0].strip()
                
                lat = None
                lon = None
                try:
                    if row.get('latitude') and row.get('latitude') != 'Unknown':
                        lat = float(row['latitude'])
                    if row.get('longitude') and row.get('longitude') != 'Unknown':
                        lon = float(row['longitude'])
                except Exception:
                    pass
                
                doc = new_fir_ip_lookup(
                    fir_number=fir_number,
                    ip_address=row.get('ip'),
                    ip_version=ip_version,
                    country=country,
                    country_code=country_code,
                    city=row.get('city'),
                    region=row.get('region'),
                    timezone=row.get('timezone'),
                    postal_code=row.get('postal_code'),
                    isp=row.get('isp'),
                    organization=row.get('organization'),
                    data_source="infobyip",
                    raw_data=row,
                    latitude=lat,
                    longitude=lon,
                )
                docs.append(doc)
            except Exception as e:
                print(f"Error storing IP {row.get('ip')}: {str(e)}")
                continue
        
        if docs:
            db[FIR_IP_LOOKUPS_COLLECTION].insert_many(docs)
        
        count = len(docs)
        db[FIR_CASES_COLLECTION].update_one(
            {"_id": fir_case["_id"]},
            {"$set": {"total_ips": count, "updated_at": datetime.now(timezone.utc)}},
        )
        
        FIRService.add_timeline_event(
            db=db,
            fir_number=fir_number,
            event_type="ip_lookup_completed",
            event_title="IP Lookup Results Stored",
            event_description=f"Stored {count} IP lookup results in database",
            performed_by=performed_by,
            event_data={"total_ips": count, "source_file": csv_file_path},
            importance="high",
        )
        
        return count, f"Successfully stored {count} IP lookup results"
    
    @staticmethod
    def store_ip_lookup_results_from_json(db, fir_number, json_file_path,
                                          performed_by=None):
        """Store IP lookup results from JSON file into database"""
        fir_case = FIRService.get_fir_case(db, fir_number)
        if not fir_case:
            return 0, "FIR case not found"
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            return 0, f"Failed to read JSON: {str(e)}"
        
        if not isinstance(data, list):
            data = [data]
        
        docs = []
        for item in data:
            try:
                ip_version = "IPv6" if ':' in item.get('ip', '') else "IPv4"
                country = item.get('country', '')
                country_code = None
                if '(' in country and ')' in country:
                    country_code = country.split('(')[1].split(')')[0]
                    country = country.split('(')[0].strip()
                
                lat = None
                lon = None
                try:
                    if item.get('latitude') and item.get('latitude') != 'Unknown':
                        lat = float(item['latitude'])
                    if item.get('longitude') and item.get('longitude') != 'Unknown':
                        lon = float(item['longitude'])
                except Exception:
                    pass
                
                doc = new_fir_ip_lookup(
                    fir_number=fir_number,
                    ip_address=item.get('ip'),
                    ip_version=ip_version,
                    country=country,
                    country_code=country_code,
                    city=item.get('city'),
                    region=item.get('region'),
                    timezone=item.get('timezone'),
                    postal_code=item.get('postal_code'),
                    isp=item.get('isp'),
                    organization=item.get('organization'),
                    data_source="infobyip",
                    raw_data=item,
                    latitude=lat,
                    longitude=lon,
                )
                docs.append(doc)
            except Exception as e:
                print(f"Error storing IP {item.get('ip')}: {str(e)}")
                continue
        
        if docs:
            db[FIR_IP_LOOKUPS_COLLECTION].insert_many(docs)
        
        count = len(docs)
        db[FIR_CASES_COLLECTION].update_one(
            {"_id": fir_case["_id"]},
            {"$set": {"total_ips": count, "updated_at": datetime.now(timezone.utc)}},
        )
        
        FIRService.add_timeline_event(
            db=db,
            fir_number=fir_number,
            event_type="ip_lookup_completed",
            event_title="IP Lookup Results Stored",
            event_description=f"Stored {count} IP lookup results in database",
            performed_by=performed_by,
            event_data={"total_ips": count, "source_file": json_file_path},
            importance="high",
        )
        
        return count, f"Successfully stored {count} IP lookup results"
    
    @staticmethod
    def get_ip_lookups(db, fir_number, limit=100, offset=0):
        """Get IP lookup results for a FIR"""
        return list(
            db[FIR_IP_LOOKUPS_COLLECTION]
            .find({"fir_number": fir_number})
            .skip(offset)
            .limit(limit)
        )
    
    @staticmethod
    def add_evidence(db, fir_number, file_name, file_path, file_type,
                     file_size, uploaded_by, description=None, tags=None):
        """Add evidence file to FIR"""
        doc = new_fir_evidence(
            fir_number=fir_number,
            file_name=file_name,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            uploaded_by=uploaded_by,
            description=description,
            tags=tags,
            processing_status="pending",
        )
        result = db[FIR_EVIDENCE_COLLECTION].insert_one(doc)
        doc["_id"] = result.inserted_id
        
        db[FIR_CASES_COLLECTION].update_one(
            {"fir_number": fir_number},
            {"$inc": {"total_evidence": 1}, "$set": {"updated_at": datetime.now(timezone.utc)}},
        )
        
        FIRService.add_timeline_event(
            db=db,
            fir_number=fir_number,
            event_type="evidence_added",
            event_title="Evidence Added",
            event_description=f"Added evidence file: {file_name}",
            performed_by=uploaded_by,
            event_data={"file_name": file_name, "file_type": file_type},
        )
        
        return doc, "Evidence added successfully"
    
    @staticmethod
    def add_timeline_event(db, fir_number, event_type, event_title,
                           event_description, performed_by,
                           event_data=None, importance="normal"):
        """Add event to FIR timeline"""
        doc = new_fir_timeline(
            fir_number=fir_number,
            event_type=event_type,
            event_title=event_title,
            event_description=event_description,
            performed_by=performed_by,
            event_data=event_data,
            importance=importance,
        )
        db[FIR_TIMELINE_COLLECTION].insert_one(doc)
    
    @staticmethod
    def get_timeline(db, fir_number, limit=50):
        """Get timeline events for FIR"""
        return list(
            db[FIR_TIMELINE_COLLECTION]
            .find({"fir_number": fir_number})
            .sort("event_timestamp", -1)
            .limit(limit)
        )
    
    @staticmethod
    def get_fir_statistics(db, fir_number):
        """Get comprehensive statistics for FIR"""
        fir_case = FIRService.get_fir_case(db, fir_number)
        if not fir_case:
            return {}
        
        ip_count = db[FIR_IP_LOOKUPS_COLLECTION].count_documents({"fir_number": fir_number})
        countries = db[FIR_IP_LOOKUPS_COLLECTION].distinct("country", {"fir_number": fir_number})
        isps = db[FIR_IP_LOOKUPS_COLLECTION].distinct("isp", {"fir_number": fir_number})
        
        return {
            "fir_number": fir_number,
            "status": fir_case.get("status"),
            "priority": fir_case.get("priority"),
            "total_ips": ip_count,
            "total_countries": len(countries),
            "total_isps": len(isps),
            "total_evidence": fir_case.get("total_evidence", 0),
            "total_suspects": fir_case.get("total_suspects", 0),
            "created_at": fir_case.get("created_at"),
            "updated_at": fir_case.get("updated_at"),
        }
