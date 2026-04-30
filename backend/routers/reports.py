from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from utils.merge import build_lookup_from_csvs, build_master_excel

router = APIRouter(tags=["reports"])

@router.post("/process")
async def process_run(run_dir: str = Query(...)):
	run = Path(run_dir)
	if not run.exists():
		raise HTTPException(status_code=404, detail="run_dir not found")
	original_csv = run / 'original_log.csv'
	if not original_csv.exists():
		raise HTTPException(status_code=400, detail="original_log.csv missing in run_dir")
	csvs = sorted(run.glob('infobyip_batch_*.csv'))
	if not csvs:
		raise HTTPException(status_code=400, detail="No InfoByIP batch CSVs found (expected infobyip_batch_*.csv)")
	lookup = build_lookup_from_csvs(csvs)
	master = run / 'master_ip_data.xlsx'
	build_master_excel(original_csv, lookup, master)
	return JSONResponse({"ok": True, "master_excel": str(master), "lookup_size": len(lookup)})

@router.get("/export")
async def export_master(run_dir: str = Query(...)):
	master = Path(run_dir) / 'master_ip_data.xlsx'
	if not master.exists():
		raise HTTPException(status_code=404, detail="master_ip_data.xlsx not found; run /api/process first")
	return FileResponse(str(master), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename='master_ip_data.xlsx')
