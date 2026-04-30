from fastapi import APIRouter, HTTPException, Query, Depends
from pathlib import Path
from core.db import get_db
from models.ip_record import IP_RECORDS_COLLECTION
from routers.auth_secure import get_current_user
from utils.path_security import safe_get_run_dir
from core.config import PROCESSED_DIR
import csv
import json

router = APIRouter()

def _resolve_run_dir(run_dir_input: str) -> Path:
	try:
		p = Path(run_dir_input)
		name = p.name if p.is_absolute() else run_dir_input
	except Exception:
		name = run_dir_input
	return safe_get_run_dir(name, PROCESSED_DIR)


def _iter_processed_runs():
	"""Yield all run directories that have completed enrichment (have ip_lookup_results.csv)."""
	processed_dir = Path(PROCESSED_DIR)
	if not processed_dir.exists():
		return
	for run in sorted(processed_dir.iterdir(), reverse=True):
		if run.is_dir():
			yield run


@router.get("/")
def get_records(run_dir: str = Query(None), limit: int = Query(100), _user: dict = Depends(get_current_user)):
	"""Provides data to frontend (for table, charts, etc.)"""
	if run_dir:
		run = _resolve_run_dir(run_dir)
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
		records = []
		# Aggregate from all processed run directories
		for run in _iter_processed_runs():
			if len(records) >= limit:
				break
			csv_file = run / 'ip_lookup_results.csv'
			if not csv_file.exists():
				continue
			try:
				with csv_file.open('r', encoding='utf-8', errors='replace') as f:
					reader = csv.DictReader(f)
					for row in reader:
						if len(records) >= limit:
							break
						records.append({
							"id": f"{run.name}_{row.get('ip', '')}",
							"ip": row.get("ip"),
							"country": row.get("country"),
							"region": row.get("region"),
							"city": row.get("city"),
							"isp": row.get("isp"),
							"source_file": run.name,
						})
			except Exception:
				continue

		# Fall back to MongoDB if no file-based data found
		if not records:
			db = get_db()
			results = list(db[IP_RECORDS_COLLECTION].find().limit(limit))
			records = [{
				"id": str(r["_id"]),
				"timestamp": r.get("timestamp"),
				"ip": r.get("ip"),
				"country": r.get("country"),
				"region": r.get("region"),
				"city": r.get("city"),
				"isp": r.get("isp"),
				"source_file": r.get("source_file"),
				"created_at": str(r.get("created_at")) if r.get("created_at") else None,
			} for r in results]

		return {"count": len(records), "records": records}


@router.get("/summary")
def get_summary(run_dir: str = Query(None), _user: dict = Depends(get_current_user)):
	"""Get summary statistics"""
	if run_dir:
		run = _resolve_run_dir(run_dir)
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
		total = 0
		countries: set = set()
		cities: set = set()

		for run in _iter_processed_runs():
			# Sum totals from ipdr_summary.json (fast — no full CSV scan needed for counts)
			summary_file = run / 'ipdr_summary.json'
			if summary_file.exists():
				try:
					data = json.loads(summary_file.read_text(encoding='utf-8'))
					total += data.get('total_records', 0)
				except Exception:
					pass

			# Extract distinct countries and cities from the results CSV
			csv_file = run / 'ip_lookup_results.csv'
			if csv_file.exists():
				try:
					with csv_file.open('r', encoding='utf-8', errors='replace') as f:
						reader = csv.DictReader(f)
						for row in reader:
							if row.get('country'):
								countries.add(row['country'])
							if row.get('city'):
								cities.add(row['city'])
				except Exception:
					continue

		# Fall back to MongoDB if nothing found on disk
		if total == 0:
			db = get_db()
			total = db[IP_RECORDS_COLLECTION].count_documents({})
			if total > 0:
				countries = set(db[IP_RECORDS_COLLECTION].distinct("country"))
				cities = set(db[IP_RECORDS_COLLECTION].distinct("city"))

		return {"total": total, "countries": len(countries), "cities": len(cities), "suspicious": 0}
