from fastapi import APIRouter, Query
from pathlib import Path

router = APIRouter(tags=["status"])

@router.get("/status")
async def get_status(run_dir: str | None = Query(None)):
	# Compute status by inspecting run folder files
	if not run_dir:
		return {"ok": False, "detail": "run_dir required"}
	run = Path(run_dir)
	if not run.exists():
		return {"ok": False, "detail": "run_dir not found"}
	batch_files = sorted(run.glob('batch_*.txt'))
	csv_files = sorted(run.glob('infobyip_batch_*.csv'))
	master = run / 'master_ip_data.xlsx'
	lookup = run / 'ip_lookup_table.csv'
	state = 'pending'
	if master.exists():
		state = 'ready'
	elif csv_files:
		state = 'merging'
	elif batch_files:
		state = 'fetching'
	return {
		"ok": True,
		"state": state,
		"batches_total": len(batch_files),
		"batches_fetched": len(csv_files),
		"has_lookup": lookup.exists(),
		"has_master": master.exists(),
	}
