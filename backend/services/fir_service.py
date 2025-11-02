"""
FIR Case Management Service
Handles all FIR-related operations including storing IP lookup results
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import json
import csv
from pathlib import Path

from models.fir_case import (
    FIRCase, FIRIPLookup, FIREvidence, FIRSuspect, FIRTimeline
)


class FIRService:
    """Service for managing FIR cases"""
    
    @staticmethod
    def create_fir_case(
        db: Session,
        fir_number: str,
        case_title: str,
        investigating_officer: str,
        department: str = "Delhi Police Cyber Cell",
        case_description: str = None,
        priority: str = "medium",
        created_by: str = None
    ) -> tuple[Optional[FIRCase], str]:
        """Create new FIR case"""
        
        # Check if FIR already exists
        existing = db.query(FIRCase).filter(FIRCase.fir_number == fir_number).first()
        if existing:
            return existing, "FIR case already exists"
        
        # Create FIR case
        fir_case = FIRCase(
            fir_number=fir_number,
            case_title=case_title,
            case_description=case_description,
            investigating_officer=investigating_officer,
            department=department,
            priority=priority,
            status="active"
        )
        
        db.add(fir_case)
        db.commit()
        db.refresh(fir_case)
        
        # Log timeline event
        FIRService.add_timeline_event(
            db=db,
            fir_number=fir_number,
            event_type="case_created",
            event_title="FIR Case Created",
            event_description=f"New FIR case {fir_number} created",
            performed_by=created_by or investigating_officer,
            importance="high"
        )
        
        return fir_case, "FIR case created successfully"
    
    @staticmethod
    def get_fir_case(db: Session, fir_number: str) -> Optional[FIRCase]:
        """Get FIR case by number"""
        return db.query(FIRCase).filter(FIRCase.fir_number == fir_number).first()
    
    @staticmethod
    def store_ip_lookup_results_from_csv(
        db: Session,
        fir_number: str,
        csv_file_path: str,
        performed_by: str = None
    ) -> tuple[int, str]:
        """Store IP lookup results from CSV file into database"""
        
        # Ensure FIR case exists
        fir_case = FIRService.get_fir_case(db, fir_number)
        if not fir_case:
            return 0, "FIR case not found"
        
        # Read CSV file
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception as e:
            return 0, f"Failed to read CSV: {str(e)}"
        
        # Store each IP lookup result
        count = 0
        for row in rows:
            try:
                # Determine IP version
                ip_version = "IPv6" if ':' in row.get('ip', '') else "IPv4"
                
                # Extract country code from country field (e.g., "India (IN)" -> "IN")
                country = row.get('country', '')
                country_code = None
                if '(' in country and ')' in country:
                    country_code = country.split('(')[1].split(')')[0]
                    country = country.split('(')[0].strip()
                
                # Create IP lookup record
                ip_lookup = FIRIPLookup(
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
                    raw_data=row  # Store complete row as JSON
                )
                
                # Try to parse latitude/longitude
                try:
                    if row.get('latitude') and row.get('latitude') != 'Unknown':
                        ip_lookup.latitude = float(row.get('latitude'))
                    if row.get('longitude') and row.get('longitude') != 'Unknown':
                        ip_lookup.longitude = float(row.get('longitude'))
                except:
                    pass
                
                db.add(ip_lookup)
                count += 1
                
            except Exception as e:
                print(f"Error storing IP {row.get('ip')}: {str(e)}")
                continue
        
        # Update FIR case statistics
        fir_case.total_ips = count
        fir_case.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Log timeline event
        FIRService.add_timeline_event(
            db=db,
            fir_number=fir_number,
            event_type="ip_lookup_completed",
            event_title="IP Lookup Results Stored",
            event_description=f"Stored {count} IP lookup results in database",
            performed_by=performed_by,
            event_data={"total_ips": count, "source_file": csv_file_path},
            importance="high"
        )
        
        return count, f"Successfully stored {count} IP lookup results"
    
    @staticmethod
    def store_ip_lookup_results_from_json(
        db: Session,
        fir_number: str,
        json_file_path: str,
        performed_by: str = None
    ) -> tuple[int, str]:
        """Store IP lookup results from JSON file into database"""
        
        # Ensure FIR case exists
        fir_case = FIRService.get_fir_case(db, fir_number)
        if not fir_case:
            return 0, "FIR case not found"
        
        # Read JSON file
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            return 0, f"Failed to read JSON: {str(e)}"
        
        # Ensure data is a list
        if not isinstance(data, list):
            data = [data]
        
        # Store each IP lookup result
        count = 0
        for item in data:
            try:
                # Determine IP version
                ip_version = "IPv6" if ':' in item.get('ip', '') else "IPv4"
                
                # Extract country code
                country = item.get('country', '')
                country_code = None
                if '(' in country and ')' in country:
                    country_code = country.split('(')[1].split(')')[0]
                    country = country.split('(')[0].strip()
                
                # Create IP lookup record
                ip_lookup = FIRIPLookup(
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
                    raw_data=item
                )
                
                # Parse coordinates
                try:
                    if item.get('latitude') and item.get('latitude') != 'Unknown':
                        ip_lookup.latitude = float(item.get('latitude'))
                    if item.get('longitude') and item.get('longitude') != 'Unknown':
                        ip_lookup.longitude = float(item.get('longitude'))
                except:
                    pass
                
                db.add(ip_lookup)
                count += 1
                
            except Exception as e:
                print(f"Error storing IP {item.get('ip')}: {str(e)}")
                continue
        
        # Update FIR case statistics
        fir_case.total_ips = count
        fir_case.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Log timeline event
        FIRService.add_timeline_event(
            db=db,
            fir_number=fir_number,
            event_type="ip_lookup_completed",
            event_title="IP Lookup Results Stored",
            event_description=f"Stored {count} IP lookup results in database",
            performed_by=performed_by,
            event_data={"total_ips": count, "source_file": json_file_path},
            importance="high"
        )
        
        return count, f"Successfully stored {count} IP lookup results"
    
    @staticmethod
    def get_ip_lookups(
        db: Session,
        fir_number: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[FIRIPLookup]:
        """Get IP lookup results for a FIR"""
        return db.query(FIRIPLookup).filter(
            FIRIPLookup.fir_number == fir_number
        ).offset(offset).limit(limit).all()
    
    @staticmethod
    def add_evidence(
        db: Session,
        fir_number: str,
        file_name: str,
        file_path: str,
        file_type: str,
        file_size: int,
        uploaded_by: str,
        description: str = None,
        tags: List[str] = None
    ) -> tuple[Optional[FIREvidence], str]:
        """Add evidence file to FIR"""
        
        evidence = FIREvidence(
            fir_number=fir_number,
            file_name=file_name,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            uploaded_by=uploaded_by,
            description=description,
            tags=tags,
            processing_status="pending"
        )
        
        db.add(evidence)
        
        # Update FIR statistics
        fir_case = FIRService.get_fir_case(db, fir_number)
        if fir_case:
            fir_case.total_evidence += 1
            fir_case.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(evidence)
        
        # Log timeline event
        FIRService.add_timeline_event(
            db=db,
            fir_number=fir_number,
            event_type="evidence_added",
            event_title="Evidence Added",
            event_description=f"Added evidence file: {file_name}",
            performed_by=uploaded_by,
            event_data={"file_name": file_name, "file_type": file_type}
        )
        
        return evidence, "Evidence added successfully"
    
    @staticmethod
    def add_timeline_event(
        db: Session,
        fir_number: str,
        event_type: str,
        event_title: str,
        event_description: str,
        performed_by: str,
        event_data: Dict = None,
        importance: str = "normal"
    ):
        """Add event to FIR timeline"""
        
        event = FIRTimeline(
            fir_number=fir_number,
            event_type=event_type,
            event_title=event_title,
            event_description=event_description,
            event_data=event_data,
            performed_by=performed_by,
            importance=importance
        )
        
        db.add(event)
        db.commit()
    
    @staticmethod
    def get_timeline(
        db: Session,
        fir_number: str,
        limit: int = 50
    ) -> List[FIRTimeline]:
        """Get timeline events for FIR"""
        return db.query(FIRTimeline).filter(
            FIRTimeline.fir_number == fir_number
        ).order_by(FIRTimeline.event_timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def get_fir_statistics(db: Session, fir_number: str) -> Dict[str, Any]:
        """Get comprehensive statistics for FIR"""
        
        fir_case = FIRService.get_fir_case(db, fir_number)
        if not fir_case:
            return {}
        
        # Get IP statistics
        ip_count = db.query(FIRIPLookup).filter(FIRIPLookup.fir_number == fir_number).count()
        
        # Get unique countries
        countries = db.query(FIRIPLookup.country).filter(
            FIRIPLookup.fir_number == fir_number
        ).distinct().all()
        
        # Get unique ISPs
        isps = db.query(FIRIPLookup.isp).filter(
            FIRIPLookup.fir_number == fir_number
        ).distinct().all()
        
        return {
            "fir_number": fir_number,
            "status": fir_case.status,
            "priority": fir_case.priority,
            "total_ips": ip_count,
            "total_countries": len(countries),
            "total_isps": len(isps),
            "total_evidence": fir_case.total_evidence,
            "total_suspects": fir_case.total_suspects,
            "created_at": fir_case.created_at,
            "updated_at": fir_case.updated_at
        }
