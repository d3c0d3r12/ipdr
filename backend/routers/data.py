from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from core.db import SessionLocal
from models.ip_record import IPRecord
import csv

router = APIRouter()

@router.get("/")
def get_records(run_dir: str = Query(None), limit: int = Query(100)):
	"""Provides data to frontend (for table, charts, etc.)"""
	if run_dir:
		# Get records from specific run directory
		run = Path(run_dir)
		if not run.exists():
			raise HTTPException(status_code=404, detail="run_dir not found")
		master = run / 'master_ip_data.csv'
		if not master.exists():
			raise HTTPException(status_code=404, detail="master_ip_data.csv not found; run processing first")
		rows = []
		with master.open('r', encoding='utf-8') as f:
			reader = csv.DictReader(f)
			for i, row in enumerate(reader):
				if i >= limit:
					break
				rows.append(row)
		return {"count": len(rows), "records": rows}
	else:
		# Get records from database
		session = SessionLocal()
		try:
			results = session.query(IPRecord).limit(limit).all()
			records = [{
				"id": r.id,
				"timestamp": r.timestamp,
				"ip": r.ip,
				"country": r.country,
				"region": r.region,
				"city": r.city,
				"isp": r.isp,
				"source_file": r.source_file,
				"created_at": str(r.created_at)
			} for r in results]
			return {"count": len(records), "records": records}
		finally:
			session.close()

@router.get("/summary")
def get_summary(run_dir: str = Query(None)):
	"""Get summary statistics"""
	if run_dir:
		run = Path(run_dir)
		if not run.exists():
			raise HTTPException(status_code=404, detail="run_dir not found")
		master = run / 'master_ip_data.csv'
		if not master.exists():
			return {"total": 0, "countries": 0, "cities": 0, "suspicious": 0}
		
		countries = set()
		cities = set()
		total = 0
		with master.open('r', encoding='utf-8') as f:
			reader = csv.DictReader(f)
			for row in reader:
				total += 1
				if row.get('Country'):
					countries.add(row['Country'])
				if row.get('City'):
					cities.add(row['City'])
		return {"total": total, "countries": len(countries), "cities": len(cities), "suspicious": 0}
	else:
		# Get summary from database
		session = SessionLocal()
		try:
			total = session.query(IPRecord).count()
			countries = session.query(IPRecord.country).distinct().count()
			cities = session.query(IPRecord.city).distinct().count()
			return {"total": total, "countries": countries, "cities": cities, "suspicious": 0}
		finally:
			session.close()
