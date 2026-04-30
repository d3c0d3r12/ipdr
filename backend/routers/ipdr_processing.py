from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import csv
import json
import os
import io
import zipfile

from fastapi import APIRouter, Depends, HTTPException, Query, Form
from fastapi.responses import FileResponse, StreamingResponse

from core.config import PROCESSED_DIR

from routers.auth_secure import get_current_user
from utils.background_task_manager import task_manager
from utils.extract_html import is_public_ip, is_valid_ip
from utils.multi_source_ip_lookup import MultiSourceIPLookup
from utils.path_security import safe_get_run_dir
from utils.progress_manager import ProgressManager
from utils.isp_letter_generator import ISPLetterGenerator

router = APIRouter()


def _resolve_run_dir(run_dir_input: str) -> Path:
	try:
		p = Path(run_dir_input)
		run_name = p.name if p.is_absolute() else run_dir_input
	except Exception:
		run_name = run_dir_input
	return safe_get_run_dir(run_name, PROCESSED_DIR)


def _load_ip_stats(run_dir: Path) -> Dict[str, Dict[str, Any]]:
	original_csv = run_dir / "original_log.csv"
	if not original_csv.exists():
		raise HTTPException(status_code=404, detail="original_log.csv not found; upload and extract first")

	stats: Dict[str, Dict[str, Any]] = {}
	with original_csv.open("r", encoding="utf-8", errors="replace", newline="") as f:
		reader = csv.DictReader(f)
		for row in reader:
			ip = (row.get("ip") or row.get("ip_original") or "").strip()
			ts = (row.get("timestamp") or row.get("timestamp_original") or "").strip()
			if not ip or not ts:
				continue
			if not is_valid_ip(ip) or not is_public_ip(ip):
				continue
			s = stats.get(ip)
			if not s:
				stats[ip] = {"count": 1, "first_seen": ts, "last_seen": ts}
			else:
				s["count"] += 1
				if ts < s["first_seen"]:
					s["first_seen"] = ts
				if ts > s["last_seen"]:
					s["last_seen"] = ts
	return stats


def _normalize_isp(isp: str | None) -> str:
	if not isp:
		return "Unknown"
	v = " ".join(isp.strip().split())
	return v if v else "Unknown"


_MOBILE_KEYWORDS = {
	"mobile", "wireless", "cellular", "gsm", "lte", "4g", "5g",
	"airtel", "jio", "vodafone", "idea", "bsnl", "mtnl", "tata docomo",
	"vi limited", "reliance jio", "indus towers",
}

_RESIDENTIAL_KEYWORDS = {
	"broadband", "dsl", "ftth", "fiber", "cable",
	"act fibernet", "hathway", "you broadband", "den networks", "sify",
	"connect broadband", "excitel", "atria convergence", "spectranet",
	"internet service provider",
}

_VPS_KEYWORDS = {
	"datacenter", "data center", "hosting", "cloud", "colo", "colocation",
	"amazon", "aws", "google cloud", "microsoft azure", "digitalocean",
	"linode", "akamai", "cloudflare", "vultr", "hetzner", "ovh", "contabo",
	"leaseweb", "choopa", "serverius", "fastly", "zscaler", "kamatera",
	"rackspace", "ibm cloud", "oracle cloud", "tencent cloud", "alibaba cloud",
	"quadranet", "psychz", "servercentral", "secured servers",
}

_VPN_KEYWORDS = {
	"vpn", "mullvad", "nordvpn", "expressvpn", "surfshark", "purevpn",
	"private internet access", "ipvanish", "protonvpn", "hidemyass",
	"cyberghost", "tunnelbear", "windscribe",
}


def _load_tor_exits(geoip_dir: Path) -> "set[str]":
	tor_file = geoip_dir / "tor_exits.txt"
	if not tor_file.exists():
		return set()
	exits: "set[str]" = set()
	for line in tor_file.read_text(encoding="utf-8", errors="replace").splitlines():
		line = line.strip()
		if line and not line.startswith("#"):
			exits.add(line)
	return exits


def _infer_ip_type(ip: str, isp: str | None, org: str | None, asn_desc: str | None, tor_exits: "set[str] | None" = None) -> str:
	"""Return a meaningful IP type — never returns 'unknown'."""
	if tor_exits and ip in tor_exits:
		return "TOR"

	text = " ".join([isp or "", org or "", asn_desc or ""]).lower()

	if any(k in text for k in _VPN_KEYWORDS):
		return "VPN"
	if any(k in text for k in _VPS_KEYWORDS):
		return "VPS"
	if any(k in text for k in _MOBILE_KEYWORDS):
		return "Mobile"
	if any(k in text for k in _RESIDENTIAL_KEYWORDS):
		return "Residential"
	return "IPv6" if ip and ":" in ip else "IPv4"


def _whois_rdap(ip: str) -> Dict[str, Any]:
	try:
		from ipwhois import IPWhois
		obj = IPWhois(ip)
		res = obj.lookup_rdap(depth=1)
		network = res.get("network") or {}
		return {
			"asn": res.get("asn"),
			"asn_description": res.get("asn_description"),
			"asn_country_code": res.get("asn_country_code"),
			"network_name": network.get("name"),
			"network_cidr": network.get("cidr"),
		}
	except Exception:
		return {}


def _write_ipdr_summary(run_dir: Path, summary: Dict[str, Any]) -> None:
	out = run_dir / "ipdr_summary.json"
	out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def _enrich_ipdr_task(task_id: str, run_dir: Path, ip_stats: Dict[str, Dict[str, Any]]) -> None:
	pm = ProgressManager(run_dir)
	lookup = None

	offline = os.getenv("IPDR_OFFLINE", "").strip() == "1"
	whois_enabled = os.getenv("IPDR_WHOIS_RDAP", "").strip() == "1"
	workers_raw = os.getenv("IPDR_ENRICH_WORKERS", "8").strip() or "8"
	try:
		max_workers = max(1, min(int(workers_raw), 32))
	except Exception:
		max_workers = 8

	base_dir = Path(__file__).resolve().parents[1]
	default_geoip_dir = base_dir / "geoip"
	city_db = os.getenv("GEOIP_CITY_DB", "").strip() or str(default_geoip_dir / "GeoLite2-City.mmdb")
	asn_db = os.getenv("GEOIP_ASN_DB", "").strip() or str(default_geoip_dir / "GeoLite2-ASN.mmdb")
	tor_exits = _load_tor_exits(default_geoip_dir)
	city_reader = None
	asn_reader = None
	try:
		if city_db and Path(city_db).exists():
			import geoip2.database
			city_reader = geoip2.database.Reader(city_db)
		if asn_db and Path(asn_db).exists():
			import geoip2.database
			asn_reader = geoip2.database.Reader(asn_db)
	except Exception as e:
		import logging
		logging.getLogger(__name__).warning(f"GeoLite2 init failed: {type(e).__name__}: {e}")
		city_reader = None
		asn_reader = None

	def _unknown_geo(ip: str, source: str) -> Dict[str, Any]:
		return {
			"ip": ip,
			"country": "Unknown",
			"city": "Unknown",
			"region": "Unknown",
			"isp": "Unknown",
			"organization": "Unknown",
			"latitude": "Unknown",
			"longitude": "Unknown",
			"timezone": "Unknown",
			"postal_code": "Unknown",
			"source": source,
		}

	def _geo_from_geolite(ip: str) -> Dict[str, Any]:
		geo = _unknown_geo(ip, "geolite")
		try:
			if city_reader:
				resp = city_reader.city(ip)
				geo["country"] = resp.country.name or "Unknown"
				geo["region"] = resp.subdivisions.most_specific.name or "Unknown"
				geo["city"] = resp.city.name or "Unknown"
				geo["latitude"] = resp.location.latitude if resp.location else "Unknown"
				geo["longitude"] = resp.location.longitude if resp.location else "Unknown"
				geo["timezone"] = resp.location.time_zone if resp.location else "Unknown"
				geo["postal_code"] = resp.postal.code or "Unknown"
		except Exception:
			pass

		try:
			if asn_reader:
				ar = asn_reader.asn(ip)
				org = getattr(ar, "autonomous_system_organization", None) or "Unknown"
				geo["isp"] = org
				geo["organization"] = org
				geo["asn"] = getattr(ar, "autonomous_system_number", None)
		except Exception:
			pass

		return geo

	def _build_result(ip: str, geo: Dict[str, Any], rdap: Dict[str, Any]) -> Dict[str, Any]:
		isp = _normalize_isp(geo.get("isp"))
		org = geo.get("organization")
		asn_desc = rdap.get("asn_description")
		ip_type = _infer_ip_type(ip, isp, org, asn_desc, tor_exits)

		return {
			"ip": ip,
			"occurrences": ip_stats[ip]["count"],
			"first_seen": ip_stats[ip]["first_seen"],
			"last_seen": ip_stats[ip]["last_seen"],
			"ip_type": ip_type,
			"is_tor": ip_type == "TOR",
			"isp": isp,
			"organization": org,
			"country": geo.get("country"),
			"region": geo.get("region"),
			"city": geo.get("city"),
			"latitude": geo.get("latitude"),
			"longitude": geo.get("longitude"),
			"timezone": geo.get("timezone"),
			"postal_code": geo.get("postal_code"),
			"source": geo.get("source"),
			"whois": rdap,
		}

	try:
		ips = list(ip_stats.keys())
		total = len(ips)
		pm.save_progress(0, total)
		task_manager.mark_started(task_id)

		isp_groups: Dict[str, int] = {}
		type_groups: Dict[str, int] = {}
		shared_ips: List[str] = []
		tor_count: int = 0
		buffer: List[Dict[str, Any]] = []

		def _consume_result(result: Dict[str, Any], completed_count: int) -> None:
			nonlocal tor_count
			ip = str(result.get("ip") or "")
			occ = int(result.get("occurrences") or 0)
			if occ > 1:
				shared_ips.append(ip)

			isp = _normalize_isp(str(result.get("isp") or "Unknown"))
			isp_groups[isp] = isp_groups.get(isp, 0) + 1

			ip_type = str(result.get("ip_type") or "IPv4")
			type_groups[ip_type] = type_groups.get(ip_type, 0) + 1
			if result.get("is_tor"):
				tor_count += 1

			buffer.append(result)
			if len(buffer) >= 500:
				pm.save_results_batch(buffer)
				buffer.clear()

			if completed_count % 50 == 0 or completed_count == total:
				pm.save_progress(completed_count, total, current_ip=ip)
			task_manager.update_progress(task_id, completed_count)

		def _error_result(ip: str) -> Dict[str, Any]:
			return _build_result(ip, _unknown_geo(ip, "error"), {})

		def _run_parallel(submit_fn, ips_list):
			"""Run submit_fn over ips_list with ThreadPoolExecutor, consuming results."""
			worker_count = min(max_workers, len(ips_list))
			if worker_count <= 1:
				for i, ip in enumerate(ips_list, start=1):
					try:
						_consume_result(submit_fn(ip), i)
					except Exception:
						_consume_result(_error_result(ip), i)
			else:
				with ThreadPoolExecutor(max_workers=worker_count) as pool:
					futures = {pool.submit(submit_fn, ip): ip for ip in ips_list}
					completed = 0
					for future in as_completed(futures):
						ip = futures[future]
						completed += 1
						try:
							result = future.result()
						except Exception:
							result = _error_result(ip)
						_consume_result(result, completed)

		if city_reader or asn_reader:
			# geoip2 Reader is thread-safe — run fully parallel for 10k+ IPs
			def _geolite_one(ip: str) -> Dict[str, Any]:
				geo = _geo_from_geolite(ip)
				rdap = _whois_rdap(ip) if whois_enabled else {}
				return _build_result(ip, geo, rdap)

			_run_parallel(_geolite_one, ips)

		elif offline:
			for i, ip in enumerate(ips, start=1):
				rdap = _whois_rdap(ip) if whois_enabled else {}
				_consume_result(_build_result(ip, _unknown_geo(ip, "offline"), rdap), i)
		else:
			# Pre-batch via ip-api.com (100 IPs per request) — reduces 10k calls to 100
			pre_cached: Dict[str, Any] = {}
			_batch_lu = MultiSourceIPLookup()
			try:
				for chunk_start in range(0, total, 100):
					chunk_results = _batch_lu.lookup_ip_api_batch(ips[chunk_start:chunk_start + 100])
					pre_cached.update(chunk_results)
			except Exception as _be:
				import logging as _log
				_log.getLogger(__name__).warning("Batch pre-fetch error: %s", _be)
			finally:
				_batch_lu.close()

			def _lookup_one(ip: str) -> Dict[str, Any]:
				if ip in pre_cached:
					geo = pre_cached[ip]
				else:
					local_lookup = MultiSourceIPLookup()
					try:
						geo = local_lookup.lookup_with_fallback(ip)
					finally:
						local_lookup.close()
				rdap = _whois_rdap(ip) if whois_enabled else {}
				return _build_result(ip, geo, rdap)

			_run_parallel(_lookup_one, ips)

		if buffer:
			pm.save_results_batch(buffer)

		pm.mark_complete()
		task_manager.mark_completed(task_id)

		summary = {
			"run_dir": str(run_dir),
			"generated_at": datetime.utcnow().isoformat() + "Z",
			"total_unique_ips": len(ips),
			"total_records": sum(s["count"] for s in ip_stats.values()),
			"by_isp": [{"isp": k, "count": v} for k, v in sorted(isp_groups.items(), key=lambda kv: kv[1], reverse=True)],
			"by_type": [{"type": k, "count": v} for k, v in sorted(type_groups.items(), key=lambda kv: kv[1], reverse=True)],
			"shared_ips": shared_ips,
			"tor_count": tor_count,
			"tor_list_loaded": len(tor_exits) > 0,
		}
		_write_ipdr_summary(run_dir, summary)
	except Exception as e:
		task_manager.mark_failed(task_id, f"{type(e).__name__}: {e}")
	finally:
		try:
			if city_reader:
				city_reader.close()
		except Exception:
			pass
		try:
			if asn_reader:
				asn_reader.close()
		except Exception:
			pass
		try:
			if lookup:
				lookup.close()
		except Exception:
			pass


@router.post("/ipdr/enrich/start")
async def start_ipdr_enrich(
	run_dir: str = Query(...),
	_user: dict = Depends(get_current_user)
):
	run = _resolve_run_dir(run_dir)
	if not run.exists():
		raise HTTPException(status_code=404, detail="run_dir not found")

	for p in (
		run / "progress.json",
		run / "ip_lookup_results.csv",
		run / "ip_lookup_results_temp.csv",
		run / "ipdr_summary.json",
		run / "ipdr_results.json",
		run / "ipdr_report.pdf"
	):
		try:
			if p.exists():
				p.unlink()
		except Exception:
			pass

	ip_stats = _load_ip_stats(run)
	if not ip_stats:
		raise HTTPException(status_code=400, detail="No valid public IPs found to enrich")

	task_id = task_manager.create_task(run, list(ip_stats.keys()), resume=False)
	asyncio.create_task(asyncio.to_thread(_enrich_ipdr_task, task_id, run, ip_stats))
	return {"task_id": task_id, "total_ips": len(ip_stats), "run_dir": str(run)}


@router.get("/ipdr/enrich/status")
def ipdr_enrich_status(
	task_id: str = Query(...),
	_user: dict = Depends(get_current_user)
):
	task = task_manager.get_task(task_id)
	if not task:
		raise HTTPException(status_code=404, detail="task not found")
	return task


@router.get("/ipdr/enrich/summary")
def ipdr_enrich_summary(
	run_dir: str = Query(...),
	_user: dict = Depends(get_current_user)
):
	run = _resolve_run_dir(run_dir)
	out = run / "ipdr_summary.json"
	if not out.exists():
		raise HTTPException(status_code=404, detail="Summary not found; run enrichment first")
	return json.loads(out.read_text(encoding="utf-8"))


@router.get("/ipdr/enrich/results")
def ipdr_enrich_results(
	run_dir: str = Query(...),
	limit: int = Query(100, ge=1, le=1000),
	offset: int = Query(0, ge=0),
	_user: dict = Depends(get_current_user)
):
	run = _resolve_run_dir(run_dir)
	pm = ProgressManager(run)
	total = pm.get_results_count()
	results = pm.get_results_paginated(offset, limit)
	for r in results:
		w = r.get("whois")
		if isinstance(w, str) and w.strip().startswith("{"):
			try:
				r["whois"] = json.loads(w)
			except Exception:
				pass
	return {"total": total, "count": len(results), "offset": offset, "limit": limit, "results": results}


@router.get("/ipdr/enrich/export/csv")
def ipdr_export_csv(
	run_dir: str = Query(...),
	_user: dict = Depends(get_current_user)
):
	run = _resolve_run_dir(run_dir)
	p = run / "ip_lookup_results.csv"
	if not p.exists():
		raise HTTPException(status_code=404, detail="Results CSV not found; run enrichment first")
	return FileResponse(path=str(p), media_type="text/csv", filename="ipdr_results.csv")


@router.get("/ipdr/enrich/export/json")
def ipdr_export_json(
	run_dir: str = Query(...),
	_user: dict = Depends(get_current_user)
):
	run = _resolve_run_dir(run_dir)
	summary_path = run / "ipdr_summary.json"
	if not summary_path.exists():
		raise HTTPException(status_code=404, detail="Summary not found; run enrichment first")
	pm = ProgressManager(run)
	payload = {
		"summary": json.loads(summary_path.read_text(encoding="utf-8")),
		"results": pm.get_results()
	}
	out = run / "ipdr_results.json"
	out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
	return FileResponse(path=str(out), media_type="application/json", filename="ipdr_results.json")


@router.get("/ipdr/enrich/export/pdf")
def ipdr_export_pdf(
	run_dir: str = Query(...),
	_user: dict = Depends(get_current_user)
):
	run = _resolve_run_dir(run_dir)
	summary_path = run / "ipdr_summary.json"
	if not summary_path.exists():
		raise HTTPException(status_code=404, detail="Summary not found; run enrichment first")

	out = run / "ipdr_report.pdf"
	summary = json.loads(summary_path.read_text(encoding="utf-8"))
	pm = ProgressManager(run)
	results = pm.get_results()

	try:
		from reportlab.lib.pagesizes import A4
		from reportlab.pdfgen import canvas
		from reportlab.lib.units import cm
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"PDF export not available: {e}")

	c = canvas.Canvas(str(out), pagesize=A4)
	width, height = A4

	y = height - 2.0 * cm
	c.setFont("Helvetica-Bold", 14)
	c.drawString(2.0 * cm, y, "IPDR Processing Report")
	y -= 0.8 * cm

	c.setFont("Helvetica", 10)
	c.drawString(2.0 * cm, y, f"Generated: {summary.get('generated_at', '-')}")
	y -= 0.5 * cm
	c.drawString(2.0 * cm, y, f"Run: {Path(summary.get('run_dir', '')).name}")
	y -= 0.8 * cm

	c.setFont("Helvetica-Bold", 11)
	c.drawString(2.0 * cm, y, "Overview")
	y -= 0.5 * cm
	c.setFont("Helvetica", 10)
	c.drawString(2.0 * cm, y, f"Total records: {summary.get('total_records', 0)}")
	y -= 0.45 * cm
	c.drawString(2.0 * cm, y, f"Unique IPs: {summary.get('total_unique_ips', 0)}")
	y -= 0.45 * cm
	c.drawString(2.0 * cm, y, f"Shared IPs (duplicates): {len(summary.get('shared_ips', []) or [])}")
	y -= 0.8 * cm

	c.setFont("Helvetica-Bold", 11)
	c.drawString(2.0 * cm, y, "Top ISPs")
	y -= 0.5 * cm
	c.setFont("Helvetica", 9)
	for row in (summary.get("by_isp") or [])[:12]:
		c.drawString(2.0 * cm, y, f"- {row.get('isp', 'Unknown')}: {row.get('count', 0)}")
		y -= 0.4 * cm
		if y < 3.0 * cm:
			c.showPage()
			y = height - 2.0 * cm
			c.setFont("Helvetica", 9)

	if y < 5.0 * cm:
		c.showPage()
		y = height - 2.0 * cm

	c.setFont("Helvetica-Bold", 11)
	c.drawString(2.0 * cm, y, "Sample IP Metadata")
	y -= 0.6 * cm
	c.setFont("Helvetica", 8)
	for r in results[:25]:
		line = f"{r.get('ip','-')} | {r.get('isp','-')} | {r.get('country','-')} {r.get('city','-')} | uses={r.get('occurrences',0)}"
		c.drawString(2.0 * cm, y, line[:140])
		y -= 0.35 * cm
		if y < 2.5 * cm:
			c.showPage()
			y = height - 2.0 * cm
			c.setFont("Helvetica", 8)

	c.save()
	return FileResponse(path=str(out), media_type="application/pdf", filename="ipdr_report.pdf")

def _format_for_template(template_type: str, dt_from: datetime, dt_to: datetime) -> Dict[str, str]:
	if template_type == "jio":
		return {
			"From Date": dt_from.strftime("%Y%m%d"),
			"From Time": dt_from.strftime("%H:%M:%S"),
			"To Date": dt_to.strftime("%Y%m%d"),
			"To Time": dt_to.strftime("%H:%M:%S")
		}
	if template_type == "airtel":
		return {
			"From Date": dt_from.strftime("%Y-%m-%d"),
			"From Time": dt_from.strftime("%H:%M:%S"),
			"To Date": dt_to.strftime("%Y-%m-%d"),
			"To Time": dt_to.strftime("%H:%M:%S")
		}
	return {
		"From Date": dt_from.strftime("%d:%m:%Y"),
		"From Time": dt_from.strftime("%H:%M:%S"),
		"To Date": dt_to.strftime("%d:%m:%Y"),
		"To Time": dt_to.strftime("%H:%M:%S")
	}


def _build_letter_rows_df(run: Path, isp_filter: str | None, template_type: str):
	import pandas as pd

	original_csv = run / "original_log.csv"
	results_csv = run / "ip_lookup_results.csv"

	df_orig = pd.read_csv(original_csv, encoding="utf-8")
	if "timestamp" not in df_orig.columns or "ip" not in df_orig.columns:
		raise HTTPException(status_code=400, detail="original_log.csv missing required columns")

	df_res = pd.read_csv(results_csv, encoding="utf-8")
	if "ip" not in df_res.columns or "isp" not in df_res.columns:
		raise HTTPException(status_code=400, detail="ip_lookup_results.csv missing required columns")

	df_res = df_res[["ip", "isp"]].copy()
	df_res["ip"] = df_res["ip"].astype(str).str.strip()
	df_res["isp"] = df_res["isp"].astype(str).fillna("Unknown").str.strip()

	df_orig = df_orig[["timestamp", "ip"]].copy()
	df_orig["ip"] = df_orig["ip"].astype(str).str.strip()
	df_orig["timestamp"] = df_orig["timestamp"].astype(str)

	df = df_orig.merge(df_res, how="left", on="ip")
	df["isp"] = df["isp"].fillna("Unknown").astype(str).str.strip()
	df["isp_norm"] = df["isp"].apply(_normalize_isp)

	if isp_filter is not None:
		df = df[df["isp_norm"] == _normalize_isp(str(isp_filter))]

	df["dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
	df = df.dropna(subset=["dt"])
	if df.empty:
		raise HTTPException(status_code=400, detail="No timestamp rows found for the selected ISP")

	rows: List[Dict[str, Any]] = []
	for _, r in df.iterrows():
		ip = str(r["ip"])
		dt_from = r["dt"].to_pydatetime()
		dt_to = dt_from + timedelta(minutes=10)
		row = {
			"Type": "IPV6" if ":" in ip else "IPV4",
			"Search Value": ip
		}
		row.update(_format_for_template(template_type, dt_from, dt_to))
		rows.append(row)

	return pd.DataFrame(rows)


@router.post("/ipdr/letters")
async def generate_isp_letters_from_run(
	run_dir: str = Query(...),
	fir_number: str = Form("N/A"),
	fir_date: str = Form("N/A"),
	police_station: str = Form("Special Cell"),
	sections: str = Form("N/A"),
	subject: str = Form("Reg provide information in case"),
	email_reference: str = Form("N/A"),
	body_description: str = Form(""),
	complainant: str = Form("N/A"),
	officer_name: str = Form("Inspector"),
	officer_designation: str = Form("IFSO, Special Cell"),
	officer_location: str = Form("Sec. 16C, Dwarka, New Delhi"),
	officer_contact: str = Form("N/A"),
	letter_date: str = Form("N/A"),
	_user: dict = Depends(get_current_user)
):
	run = _resolve_run_dir(run_dir)
	if not run.exists():
		raise HTTPException(status_code=404, detail="run_dir not found")

	original_csv = run / "original_log.csv"
	results_csv = run / "ip_lookup_results.csv"
	if not original_csv.exists():
		raise HTTPException(status_code=404, detail="original_log.csv not found; upload first")
	if not results_csv.exists():
		raise HTTPException(status_code=404, detail="ip_lookup_results.csv not found; run enrichment first")

	import pandas as pd
	df_res = pd.read_csv(results_csv, encoding="utf-8")
	if "isp" not in df_res.columns:
		raise HTTPException(status_code=400, detail="ip_lookup_results.csv missing isp column")

	case_details = {
		"fir_number": fir_number,
		"fir_date": fir_date,
		"police_station": police_station,
		"sections": sections,
		"subject": subject,
		"email_reference": email_reference,
		"body_description": body_description,
		"complainant": complainant,
		"officer_name": officer_name,
		"officer_designation": officer_designation,
		"officer_location": officer_location,
		"officer_contact": officer_contact,
		"letter_date": letter_date
	}

	generator = ISPLetterGenerator()
	zip_buffer = io.BytesIO()

	with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
		for isp_clean in sorted({_normalize_isp(str(x)) for x in df_res["isp"].fillna("Unknown").tolist()}):
			template_type = generator.get_template_type(isp_clean)
			letter_df = _build_letter_rows_df(run, isp_clean, template_type)
			doc = generator.generate_letter(isp_clean, letter_df, case_details)

			doc_buffer = io.BytesIO()
			doc.save(doc_buffer)
			doc_buffer.seek(0)

			safe_name = isp_clean.replace(" ", "_").replace("/", "_").replace("\\", "_")
			filename = f"{safe_name}_Letter_{fir_number.replace('/', '-')}.docx"
			zf.writestr(filename, doc_buffer.getvalue())

			if template_type == "jio":
				try:
					txt_content = generator.create_jio_txt_file(isp_clean, letter_df, case_details)
					zf.writestr(f"{safe_name}_Data_{fir_number.replace('/', '-')}.txt", txt_content)
				except Exception:
					pass

	zip_buffer.seek(0)
	return StreamingResponse(
		iter([zip_buffer.getvalue()]),
		media_type="application/zip",
		headers={"Content-Disposition": f'attachment; filename="ISP_Letters_{fir_number.replace("/", "-")}.zip"'}
	)


@router.post("/ipdr/letter")
async def generate_single_isp_letter_from_run(
	run_dir: str = Query(...),
	isp: str = Query(...),
	fir_number: str = Form("N/A"),
	fir_date: str = Form("N/A"),
	police_station: str = Form("Special Cell"),
	sections: str = Form("N/A"),
	subject: str = Form("Reg provide information in case"),
	email_reference: str = Form("N/A"),
	body_description: str = Form(""),
	complainant: str = Form("N/A"),
	officer_name: str = Form("Inspector"),
	officer_designation: str = Form("IFSO, Special Cell"),
	officer_location: str = Form("Sec. 16C, Dwarka, New Delhi"),
	officer_contact: str = Form("N/A"),
	letter_date: str = Form("N/A"),
	_user: dict = Depends(get_current_user)
):
	run = _resolve_run_dir(run_dir)
	if not run.exists():
		raise HTTPException(status_code=404, detail="run_dir not found")

	original_csv = run / "original_log.csv"
	results_csv = run / "ip_lookup_results.csv"
	if not original_csv.exists():
		raise HTTPException(status_code=404, detail="original_log.csv not found; upload first")
	if not results_csv.exists():
		raise HTTPException(status_code=404, detail="ip_lookup_results.csv not found; run enrichment first")

	isp_name = str(isp)
	isp_clean = _normalize_isp(isp_name)

	generator = ISPLetterGenerator()
	template_type = generator.get_template_type(isp_clean)

	letter_df = _build_letter_rows_df(run, isp_name, template_type)

	case_details = {
		"fir_number": fir_number,
		"fir_date": fir_date,
		"police_station": police_station,
		"sections": sections,
		"subject": subject,
		"email_reference": email_reference,
		"body_description": body_description,
		"complainant": complainant,
		"officer_name": officer_name,
		"officer_designation": officer_designation,
		"officer_location": officer_location,
		"officer_contact": officer_contact,
		"letter_date": letter_date
	}

	doc = generator.generate_letter(isp_clean, letter_df, case_details)
	doc_buffer = io.BytesIO()
	doc.save(doc_buffer)
	doc_buffer.seek(0)

	safe_name = isp_clean.replace(" ", "_").replace("/", "_").replace("\\", "_")
	filename = f"{safe_name}_Letter_{fir_number.replace('/', '-')}.docx"

	return StreamingResponse(
		iter([doc_buffer.getvalue()]),
		media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
		headers={"Content-Disposition": f'attachment; filename="{filename}"'}
	)
