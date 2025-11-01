import argparse
import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from bs4 import BeautifulSoup


def _log(log_path: Path, message: str) -> None:
	ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
	log_path.parent.mkdir(parents=True, exist_ok=True)
	with log_path.open('a', encoding='utf-8', newline='') as f:
		f.write(f"[{ts}] {message}\n")


def _find_table(html_text: str) -> List[List[str]]:
	soup = BeautifulSoup(html_text, 'lxml')
	table = soup.find('table')
	if not table:
		return []
	rows: List[List[str]] = []
	for tr in table.find_all('tr'):
		cells = [td.get_text(strip=False) for td in tr.find_all(['td', 'th'])]
		if cells:
			rows.append(cells)
	return rows


def _extract_rows(table_rows: List[List[str]]) -> Tuple[List[Tuple[int, str, str, str]], List[Tuple[int, str, str, str, str]]]:
	data_rows: List[Tuple[int, str, str, str]] = []
	problems: List[Tuple[int, str, str, str, str]] = []
	if not table_rows:
		return data_rows, problems
	# assume first row is header if it has th or looks like header; still skip index 0
	for idx, cells in enumerate(table_rows[1:], start=1):
		timestamp_original = cells[0] if len(cells) > 0 else ''
		ip_original = cells[1] if len(cells) > 1 else ''
		activity = cells[2] if len(cells) > 2 else ''
		data_rows.append((idx, timestamp_original, ip_original, activity))
		if not timestamp_original or not ip_original:
			reason_parts = []
			if not timestamp_original:
				reason_parts.append('missing_timestamp')
			if not ip_original:
				reason_parts.append('missing_ip')
			problems.append((idx, ','.join(reason_parts), timestamp_original, ip_original, activity))
	return data_rows, problems


def create_batches(run_dir: Path, ips: List[str], batch_size: int = 100, preserve_duplicates: bool = False) -> List[Path]:
	"""
	Create batch files for IP lookup
	
	Args:
		run_dir: Directory to save batch files
		ips: List of IP addresses
		batch_size: Number of IPs per batch (default 100)
		preserve_duplicates: If True, keep duplicate IPs; if False, remove duplicates (default False)
	
	Returns:
		List of paths to batch files
	"""
	if preserve_duplicates:
		# Keep all IPs including duplicates
		unique_ordered = ips
	else:
		# Remove duplicates while preserving order
		unique_ordered: List[str] = []
		seen = set()
		for ip in ips:
			if ip not in seen:
				seen.add(ip)
				unique_ordered.append(ip)
	
	batch_paths: List[Path] = []
	for i in range(0, len(unique_ordered), batch_size):
		chunk = unique_ordered[i:i + batch_size]
		batch_no = i // batch_size + 1
		p = run_dir / f"batch_{batch_no:03d}.txt"
		p.write_text('\n'.join(chunk), encoding='utf-8')
		batch_paths.append(p)
	
	# summary
	summary = run_dir / 'batches_summary.csv'
	with summary.open('w', encoding='utf-8', newline='') as f:
		w = csv.writer(f)
		w.writerow(['batch_no', 'file', 'ip_count', 'duplicates_preserved'])
		for i, p in enumerate(batch_paths, start=1):
			cnt = sum(1 for _ in p.read_text(encoding='utf-8').splitlines() if _.strip())
			w.writerow([i, p.name, cnt, 'Yes' if preserve_duplicates else 'No'])
	
	return batch_paths


def write_original_csv(run_dir: Path, rows: List[Tuple[int, str, str, str]]) -> Path:
	path = run_dir / 'original_log.csv'
	with path.open('w', encoding='utf-8', newline='') as f:
		w = csv.writer(f)
		# Only write timestamp and IP (exclude row_index and activity)
		w.writerow(['timestamp', 'ip'])
		for row in rows:
			# row format: (idx, timestamp, ip, activity)
			w.writerow([row[1], row[2]])  # Only timestamp and IP
	return path


def write_problems_csv(run_dir: Path, problems: List[Tuple[int, str, str, str, str]]) -> Path:
	path = run_dir / 'problems_rows.csv'
	if not problems:
		# still create an empty file with headers for auditability
		with path.open('w', encoding='utf-8', newline='') as f:
			csv.writer(f).writerow(['row_index', 'problem_reason', 'timestamp_original', 'ip_original', 'activity'])
		return path
	with path.open('w', encoding='utf-8', newline='') as f:
		w = csv.writer(f)
		w.writerow(['row_index', 'problem_reason', 'timestamp_original', 'ip_original', 'activity'])
		for row in problems:
			w.writerow(row)
	return path


def run_extraction(input_html: Path, outdir: Path, case: str | None = None) -> Path:
	assert input_html.exists(), f"Input HTML not found: {input_html}"
	html_bytes = input_html.read_bytes()
	hash_hex = hashlib.sha1(html_bytes).hexdigest()
	ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
	safe_case = ''.join(c if c.isalnum() or c in ('-', '_') else '-' for c in (case or 'CASE'))[:64]
	run_dir = outdir / f"{ts}_{safe_case}"
	run_dir.mkdir(parents=True, exist_ok=True)
	# save source html copy
	(input_html.parent / input_html.name)  # no-op; just clarity
	(run_dir / input_html.name).write_bytes(html_bytes)
	log_path = run_dir / 'process_log.txt'
	_log(log_path, f"input_file={input_html.name} sha1={hash_hex}")

	html_text = html_bytes.decode('utf-8', errors='replace')
	rows_raw = _find_table(html_text)
	rows, problems = _extract_rows(rows_raw)
	original_csv = write_original_csv(run_dir, rows)
	problems_csv = write_problems_csv(run_dir, problems)
	ips = [r[2] for r in rows]
	batches = create_batches(run_dir, ips=ips, batch_size=100)
	_log(log_path, f"rows={len(rows)} problems={len(problems)} batches={len(batches)}")
	return run_dir


def main() -> None:
	parser = argparse.ArgumentParser(description='Extract timestamp+IP rows and create lookup batches.')
	parser.add_argument('--input', required=True, help='Path to HTML file')
	parser.add_argument('--outdir', default='backend/processed', help='Output base directory')
	parser.add_argument('--case', default='CASE', help='Case identifier for run folder')
	args = parser.parse_args()

	run_dir = run_extraction(Path(args.input), Path(args.outdir), case=args.case)
	print(str(run_dir))


if __name__ == '__main__':
	main()



