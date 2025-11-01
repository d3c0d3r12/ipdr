from fastapi import APIRouter, UploadFile, File, HTTPException, Form, BackgroundTasks
from datetime import datetime
from pathlib import Path
from core.config import UPLOAD_DIR, PROCESSED_DIR
from utils.extract_html import _find_table, _extract_rows, write_original_csv, create_batches
from utils.csv_cleaner import _clean_one, build_lookup
from utils.merge_data import merge_all
from utils.advanced_infobyip import auto_fetch_batches_advanced  # Advanced anti-detection for InfoByIP
import shutil
import os
import time

# Ensure directories exist
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(PROCESSED_DIR).mkdir(parents=True, exist_ok=True)

router = APIRouter()

def _auto_process(run_dir: Path, timeout_seconds: int = 900) -> None:
	"""
	Auto-process uploaded file with advanced InfoByIP scraping
	
	Steps:
	1. Check if CSVs already exist
	2. If not, use advanced anti-detection to scrape InfoByIP
	3. Clean and merge data
	4. Create master Excel file
	"""
	log_path = run_dir / 'process_log.txt'
	deadline = time.time() + timeout_seconds
	
	# If CSVs already present, process immediately; else fetch
	while True:
		raw_csvs = sorted(run_dir.glob('infobyip_batch_*.csv'))
		if raw_csvs:
			# CSVs exist, process them
			cleaned = []
			for raw in raw_csvs:
				cleaned.append(_clean_one(raw, run_dir, log_path))
			build_lookup(cleaned, run_dir, log_path)
			merge_all(run_dir)
			return
		else:
			# No CSVs, use advanced anti-detection to scrape InfoByIP
			fetched = auto_fetch_batches_advanced(run_dir)
			if fetched:
				# loop again to process the newly created CSVs
				continue
		
		if time.time() > deadline:
			# timeout reached
			return
		time.sleep(5)


@router.post("/")
async def upload_file(
	background: BackgroundTasks,
	file: UploadFile = File(...),
	fir: str = Form("UNKNOWN"),
	preserve_duplicates: bool = Form(False),
	bypass_cloudflare: bool = Form(False)
):
	"""
	Upload HTML file and extract IP activity
	
	Args:
		file: HTML file to upload
		fir: FIR number/case identifier
		preserve_duplicates: If True, keep duplicate IPs in batches; if False, remove duplicates (default)
		bypass_cloudflare: If True, use Cloudflare bypass for unlimited InfoByIP access
		background: Background tasks handler
	"""
	if not file.filename.endswith(('.html', '.htm')):
		raise HTTPException(status_code=400, detail="Only HTML files allowed")
	
	# Read file
	html_bytes = await file.read()
	html_text = html_bytes.decode('utf-8', errors='replace')
	
	# Create run directory
	ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
	safe_fir = ''.join(c if c.isalnum() or c in ('-', '_') else '-' for c in fir)[:64] or 'FIR'
	run_dir = Path(PROCESSED_DIR) / f"{ts}_{safe_fir}"
	run_dir.mkdir(parents=True, exist_ok=True)
	
	# Save HTML snapshot to run directory
	(run_dir / file.filename).write_bytes(html_bytes)
	
	# Extract IP activity
	table_rows = _find_table(html_text)
	rows, problems = _extract_rows(table_rows)
	if not rows:
		raise HTTPException(status_code=400, detail="No IP ACTIVITY rows found")
	
	original_csv = write_original_csv(run_dir, rows)
	ips = [row[2] for row in rows]  # row format: (idx, timestamp, ip, activity)
	
	# Create batches with duplicate handling option
	batches = create_batches(run_dir, ips, preserve_duplicates=preserve_duplicates)
	
	# Save processing options
	options_file = run_dir / 'processing_options.txt'
	options_file.write_text(
		f"FIR: {fir}\n"
		f"Filename: {file.filename}\n"
		f"Preserve Duplicates: {'Yes' if preserve_duplicates else 'No'}\n"
		f"Bypass Cloudflare: {'Yes' if bypass_cloudflare else 'No'}\n"
		f"Total Records: {len(rows)}\n"
		f"Unique IPs: {len(set(ips))}\n"
		f"Timestamp: {ts}\n",
		encoding='utf-8'
	)
	
	# Kick off background processing
	background.add_task(_auto_process, run_dir)
	
	return {
		"status": "uploaded",
		"filename": file.filename,
		"run_dir": str(run_dir),
		"original_csv": str(original_csv),
		"batches": [str(p) for p in batches],
		"count_rows": len(rows),
		"unique_ips": len(set(ips)),
		"preserve_duplicates": preserve_duplicates,
		"bypass_cloudflare": bypass_cloudflare
	}
