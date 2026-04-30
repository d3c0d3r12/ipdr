from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from utils.csv_cleaner import _clean_one, build_lookup
from utils.merge_data import merge_all
from utils.extract_html import _find_table, _extract_rows
from utils.path_security import safe_get_run_dir
from core.config import PROCESSED_DIR
from routers.auth_secure import get_current_user


router = APIRouter()


def _resolve_run_dir(run_dir_input: str) -> Path:
	# Accept full path or basename; always constrain under PROCESSED_DIR
	try:
		p = Path(run_dir_input)
		run_name = p.name if p.is_absolute() else run_dir_input
	except Exception:
		run_name = run_dir_input
	return safe_get_run_dir(run_name, PROCESSED_DIR)


@router.get("/extract")
def extract(run_dir: str = Query(...), _user: dict = Depends(get_current_user)):
	"""Extracts IPs/timestamps from uploaded HTML files"""
	run = _resolve_run_dir(run_dir)
	if not run.exists():
		raise HTTPException(status_code=404, detail="run_dir not found")
	
	# Find HTML files in run directory
	html_files = list(run.glob('*.html')) + list(run.glob('*.htm'))
	if not html_files:
		raise HTTPException(status_code=400, detail="No HTML files found in run_dir")
	
	html_file = html_files[0]
	html_text = html_file.read_text(encoding='utf-8', errors='replace')
	table_rows = _find_table(html_text)
	rows, problems = _extract_rows(table_rows)
	
	return {
		"status": "extracted",
		"html_file": html_file.name,
		"rows_extracted": len(rows),
		"sample": rows[:5] if len(rows) > 5 else rows
	}


@router.post("/merge")
def merge(run_dir: str = Query(...), _user: dict = Depends(get_current_user)):
	"""Merges InfoByIP CSVs and creates master Excel"""
	run = _resolve_run_dir(run_dir)
	if not run.exists():
		raise HTTPException(status_code=404, detail="run_dir not found")
	
	# Clean raw InfoByIP CSVs and build lookup
	raw_csvs: List[Path] = sorted(run.glob('infobyip_batch_*.csv'))
	if not raw_csvs:
		raise HTTPException(status_code=400, detail="No infobyip_batch_*.csv found in run_dir")
	
	log_path = run / 'process_log.txt'
	cleaned: List[Path] = []
	for raw in raw_csvs:
		cleaned.append(_clean_one(raw, run, log_path))
	
	lookup_path, conflicts_path = build_lookup(cleaned, run, log_path)
	
	# Merge to master excel
	xlsx_path = merge_all(run)
	lookup_size = sum(1 for _ in lookup_path.read_text(encoding='utf-8', errors='ignore').splitlines()) - 1
	
	return {
		"message": "processed",
		"lookup": str(lookup_path),
		"conflicts": str(conflicts_path),
		"excel": str(xlsx_path),
		"lookup_size": max(0, lookup_size),
	}


@router.get("/export")
def export_excel(run_dir: str = Query(...), _user: dict = Depends(get_current_user)):
	"""Export final Excel file"""
	run = _resolve_run_dir(run_dir)
	if not run.exists():
		raise HTTPException(status_code=404, detail="run_dir not found")
	
	xlsx = run / 'master_ip_data.xlsx'
	if not xlsx.exists():
		# Attempt merge if lookup present
		lookup = run / 'ip_lookup_table.csv'
		orig = run / 'original_log.csv'
		if lookup.exists() and orig.exists():
			merge_all(run)
		else:
			raise HTTPException(status_code=400, detail="master_ip_data.xlsx not found; run processing first")
	
	return FileResponse(
		path=str(xlsx),
		media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		filename='master_ip_data.xlsx'
	)




