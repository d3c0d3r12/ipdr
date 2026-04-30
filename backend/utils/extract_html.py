import argparse
import csv
import hashlib
import ipaddress
import re
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from bs4 import BeautifulSoup


def extract_ips_from_text(text: str) -> List[str]:
	"""
	Extract all IP addresses from text using regex (fallback method)
	Useful when table structure is not standard
	"""
	# IPv4 pattern
	ipv4_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
	
	# IPv6 pattern
	ipv6_pattern = r'\b(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\b'
	
	ips = []
	
	# Find IPv4
	ipv4_matches = re.findall(ipv4_pattern, text)
	for ip in ipv4_matches:
		if is_valid_ip(ip):
			ips.append(ip)
	
	# Find IPv6
	ipv6_matches = re.findall(ipv6_pattern, text)
	for ip in ipv6_matches:
		if is_valid_ip(ip):
			ips.append(ip)
	
	return list(set(ips))  # Remove duplicates


def _log(log_path: Path, message: str) -> None:
	ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
	log_path.parent.mkdir(parents=True, exist_ok=True)
	with log_path.open('a', encoding='utf-8', newline='') as f:
		f.write(f"[{ts}] {message}\n")


def is_valid_ip(ip_str: str) -> bool:
	"""
	Validate if string is a valid IPv4 or IPv6 address
	
	Args:
		ip_str: String to validate
		
	Returns:
		True if valid IP, False otherwise
	"""
	if not ip_str or not isinstance(ip_str, str):
		return False
	
	ip_clean = ip_str.strip()
	
	# IPv4 pattern: 192.168.1.1
	ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
	
	# IPv6 pattern: 2001:0db8:85a3:0000:0000:8a2e:0370:7334 or compressed forms
	ipv6_pattern = r'^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$'
	
	# Check IPv4
	if re.match(ipv4_pattern, ip_clean):
		try:
			# Validate octets are 0-255
			octets = ip_clean.split('.')
			return all(0 <= int(octet) <= 255 for octet in octets)
		except (ValueError, AttributeError):
			return False
	
	# Check IPv6
	if re.match(ipv6_pattern, ip_clean):
		return True
	
	return False


def is_public_ip(ip_str: str) -> bool:
	"""
	Check if an IP is globally routable (filters private, loopback, reserved, etc.)
	"""
	try:
		ip_obj = ipaddress.ip_address(ip_str.strip())
		return bool(getattr(ip_obj, "is_global", False))
	except Exception:
		return False


def _detect_best_ip_column(headers: List[str], sample_rows: List[List[str]]) -> int:
	# Prefer header names that look like an IP column
	for i, h in enumerate(headers):
		h_norm = (h or "").strip().lower()
		if h_norm in {"ip", "ip_address", "ipaddress"} or "ip" == h_norm.replace(" ", "_"):
			return i

	# Otherwise score by valid IP occurrences
	scores: dict[int, int] = {}
	for row in sample_rows:
		for col_idx, cell in enumerate(row):
			if cell and is_valid_ip(cell.strip()):
				scores[col_idx] = scores.get(col_idx, 0) + 1
	if scores:
		return max(scores, key=scores.get)
	return -1


def _detect_timestamp_column(headers: List[str]) -> int:
	for i, h in enumerate(headers):
		h_norm = (h or "").strip().lower()
		if any(k in h_norm for k in ("timestamp", "time", "date", "datetime")):
			return i
	return 0


def extract_rows_from_csv(csv_text: str) -> Tuple[List[Tuple[int, str, str, str]], List[Tuple[int, str, str, str, str]]]:
	"""
	Extract (idx, timestamp, ip, activity) rows from an IPDR CSV.
	"""
	data_rows: List[Tuple[int, str, str, str]] = []
	problems: List[Tuple[int, str, str, str, str]] = []

	if not csv_text.strip():
		return data_rows, [(0, "empty_file", "", "", "")]

	try:
		sniffer = csv.Sniffer()
		dialect = sniffer.sniff(csv_text[:4096])
	except Exception:
		dialect = csv.excel

	reader = csv.reader(csv_text.splitlines(), dialect)
	rows = [r for r in reader if any((c or "").strip() for c in r)]
	if not rows:
		return data_rows, [(0, "empty_file", "", "", "")]

	headers = [c.strip() for c in rows[0]]
	sample = rows[1: min(len(rows), 11)]

	ip_col = _detect_best_ip_column(headers, sample)
	if ip_col == -1:
		return data_rows, [(0, "ip_column_not_found", "", "", "")]

	ts_col = _detect_timestamp_column(headers)

	activity_col = -1
	for i, h in enumerate(headers):
		h_norm = (h or "").strip().lower()
		if any(k in h_norm for k in ("activity", "event", "type", "service", "remark", "notes")):
			activity_col = i
			break

	for idx, row in enumerate(rows[1:], start=1):
		ip_original = (row[ip_col].strip() if len(row) > ip_col else "")
		timestamp_original = (row[ts_col].strip() if len(row) > ts_col else "")
		activity = (row[activity_col].strip() if activity_col != -1 and len(row) > activity_col else "")

		if not ip_original or not timestamp_original:
			reasons = []
			if not timestamp_original:
				reasons.append("missing_timestamp")
			if not ip_original:
				reasons.append("missing_ip")
			problems.append((idx, ",".join(reasons), timestamp_original, ip_original, activity))
			continue

		if not is_valid_ip(ip_original):
			problems.append((idx, "invalid_ip_format", timestamp_original, ip_original, activity))
			continue

		if not is_public_ip(ip_original):
			problems.append((idx, "non_public_ip", timestamp_original, ip_original, activity))
			continue

		data_rows.append((idx, timestamp_original, ip_original, activity))

	return data_rows, problems


def find_ip_column(table_rows: List[List[str]]) -> int:
	"""
	Automatically detect which column contains IP addresses
	
	Args:
		table_rows: List of table rows (each row is a list of cells)
		
	Returns:
		Column index with most valid IPs, or -1 if not found
	"""
	if not table_rows or len(table_rows) < 2:
		return -1
	
	# Check first few data rows (skip header)
	sample_rows = table_rows[1:min(6, len(table_rows))]
	
	# Count valid IPs in each column
	column_scores = {}
	
	for row in sample_rows:
		for col_idx, cell in enumerate(row):
			if cell and is_valid_ip(cell):
				column_scores[col_idx] = column_scores.get(col_idx, 0) + 1
	
	# Return column with most valid IPs
	if column_scores:
		best_column = max(column_scores, key=column_scores.get)
		print(f"✅ Auto-detected IP column: {best_column} (found {column_scores[best_column]} valid IPs in sample)")
		return best_column
	
	print("⚠️  Could not auto-detect IP column, using default column 1")
	return -1


def _find_table(html_text: str) -> List[List[str]]:
	"""
	Find and extract table data from HTML
	
	Searches all tables in the HTML and returns the one with the most data rows.
	This handles cases where multiple tables exist (e.g., Google Subscriber Info)
	"""
	soup = BeautifulSoup(html_text, 'lxml')
	tables = soup.find_all('table')
	
	if not tables:
		print("❌ No tables found in HTML")
		return []
	
	print(f"📊 Found {len(tables)} table(s) in HTML")
	
	# Extract rows from all tables
	all_table_data = []
	
	for table_idx, table in enumerate(tables):
		rows: List[List[str]] = []
		for tr in table.find_all('tr'):
			cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
			if cells:
				rows.append(cells)
		
		if rows:
			all_table_data.append((table_idx, rows))
			print(f"  Table {table_idx}: {len(rows)} rows, {len(rows[0]) if rows else 0} columns")
	
	if not all_table_data:
		print("❌ No data found in any table")
		return []
	
	# Return the table with the most rows (likely the data table)
	best_table = max(all_table_data, key=lambda x: len(x[1]))
	print(f"✅ Using Table {best_table[0]} with {len(best_table[1])} rows")
	
	return best_table[1]


def _extract_rows(table_rows: List[List[str]]) -> Tuple[List[Tuple[int, str, str, str]], List[Tuple[int, str, str, str, str]]]:
	"""
	Extract rows with automatic IP column detection and validation
	
	Args:
		table_rows: List of table rows from HTML
		
	Returns:
		Tuple of (data_rows, problem_rows)
		- data_rows: List of (idx, timestamp, ip, activity)
		- problem_rows: List of (idx, reason, timestamp, ip, activity)
	"""
	data_rows: List[Tuple[int, str, str, str]] = []
	problems: List[Tuple[int, str, str, str, str]] = []
	
	if not table_rows:
		print("❌ No table rows provided")
		return data_rows, problems
	
	print(f"📋 Processing {len(table_rows)} rows from table")
	
	# Show first row (header) for debugging
	if table_rows:
		print(f"📌 Header row: {table_rows[0]}")
	
	# Auto-detect IP column
	ip_column = find_ip_column(table_rows)
	
	# Fallback to column 1 if auto-detection fails
	if ip_column == -1:
		print("⚠️  Using fallback: IP column = 1")
		ip_column = 1
	
	# Determine other columns based on IP column position
	# Common patterns:
	# Pattern 1: [Timestamp, IP, Activity] - IP at column 1
	# Pattern 2: [Index, Timestamp, IP, Activity] - IP at column 2
	# Pattern 3: [Timestamp, Activity, IP] - IP at column 2
	
	timestamp_column = 0  # Usually first column
	activity_column = ip_column + 1 if ip_column < 2 else ip_column - 1
	
	print(f"📊 Column mapping: Timestamp={timestamp_column}, IP={ip_column}, Activity={activity_column}")
	
	# Extract rows (skip header row)
	for idx, cells in enumerate(table_rows[1:], start=1):
		# Extract fields based on detected columns
		timestamp_original = cells[timestamp_column].strip() if len(cells) > timestamp_column else ''
		ip_original = cells[ip_column].strip() if len(cells) > ip_column else ''
		activity = cells[activity_column].strip() if len(cells) > activity_column else ''
		
		# Validate IP format
		if ip_original and not is_valid_ip(ip_original):
			problems.append((
				idx,
				'invalid_ip_format',
				timestamp_original,
				ip_original,
				activity
			))
			print(f"⚠️  Row {idx}: Invalid IP format: '{ip_original}'")
			continue
		
		# Check for missing required fields
		if not timestamp_original or not ip_original:
			reason_parts = []
			if not timestamp_original:
				reason_parts.append('missing_timestamp')
			if not ip_original:
				reason_parts.append('missing_ip')
			problems.append((
				idx,
				','.join(reason_parts),
				timestamp_original,
				ip_original,
				activity
			))
			print(f"⚠️  Row {idx}: {','.join(reason_parts)}")
			continue
		
		# Add valid row
		data_rows.append((idx, timestamp_original, ip_original, activity))
	
	print(f"✅ Extracted {len(data_rows)} valid rows, {len(problems)} problem rows")
	
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



