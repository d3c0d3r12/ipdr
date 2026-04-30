import argparse
import csv
import hashlib
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def _map_headers(headers: Iterable[str]) -> Dict[str, str]:
	map_out: Dict[str, str] = {}
	for h in headers:
		low = h.lower().strip()
		if 'ip' in low and 'zip' not in low:
			map_out['ip'] = h
		elif 'country' in low:
			map_out['country'] = h
		elif 'region' in low or 'state' in low:
			map_out['region'] = h
		elif 'city' in low:
			map_out['city'] = h
		elif 'isp' in low or 'organization' in low or 'organisation' in low or 'provider' in low:
			map_out['isp'] = h
	return map_out


def _clean_one(raw_csv: Path, out_dir: Path, log_path: Path) -> Path:
	sha1 = hashlib.sha1(raw_csv.read_bytes()).hexdigest()
	with log_path.open('a', encoding='utf-8', newline='') as log:
		log.write(f"[file] {raw_csv.name} sha1={sha1}\n")
	with raw_csv.open('r', encoding='utf-8', errors='replace', newline='') as f:
		reader = csv.reader(f)
		rows = list(reader)
		if not rows:
			raise RuntimeError(f"Empty CSV: {raw_csv}")
		headers = rows[0]
		mapping = _map_headers(headers)
		missing = [k for k in ['ip', 'country', 'region', 'city', 'isp'] if k not in mapping]
		if missing:
			with log_path.open('a', encoding='utf-8', newline='') as log:
				log.write(f"[warn] {raw_csv.name} missing_columns={','.join(missing)}\n")
		# build cleaned
		index_by_header = {h: i for i, h in enumerate(headers)}
		out_rows: List[List[str]] = []
		for r in rows[1:]:
			def get_val(key: str) -> str:
				h = mapping.get(key)
				if not h:
					return ''
				idx = index_by_header.get(h, -1)
				return r[idx] if 0 <= idx < len(r) else ''
			out_rows.append([
				get_val('ip'),
				get_val('country'),
				get_val('region'),
				get_val('city'),
				get_val('isp'),
			])
		clean_name = raw_csv.name.replace('infobyip_batch_', 'infobyip_cleaned_batch_')
		clean_path = out_dir / clean_name
		with clean_path.open('w', encoding='utf-8', newline='') as outf:
			w = csv.writer(outf)
			w.writerow(['ip', 'country', 'region', 'city', 'isp'])
			for r in out_rows:
				w.writerow(r)
		return clean_path


def build_lookup(cleaned_csvs: List[Path], out_dir: Path, log_path: Path) -> Tuple[Path, Path]:
	lookup: Dict[str, Tuple[str, str, str, str, str]] = {}
	conflicts: List[Tuple[str, str, List[str], List[str], str, str]] = []
	for p in cleaned_csvs:
		with p.open('r', encoding='utf-8', newline='') as f:
			reader = csv.DictReader(f)
			for row in reader:
				ip = row.get('ip', '')
				vals = (row.get('country', ''), row.get('region', ''), row.get('city', ''), row.get('isp', ''), p.name)
				if ip in lookup:
					prev = lookup[ip]
					if prev[:4] != vals[:4]:
						# record conflict; keep first
						field_names = ['country', 'region', 'city', 'isp']
						for i, fname in enumerate(field_names):
							if prev[i] != vals[i]:
								conflicts.append((ip, fname, [prev[i], vals[i]], [prev[4], vals[4]], prev[i], prev[4]))
				else:
					lookup[ip] = vals
	# write lookup table
	lookup_path = out_dir / 'ip_lookup_table.csv'
	with lookup_path.open('w', encoding='utf-8', newline='') as f:
		w = csv.writer(f)
		w.writerow(['ip', 'country', 'region', 'city', 'isp', 'source_file'])
		for ip, vals in lookup.items():
			w.writerow([ip, *vals])
	# write conflicts
	conflicts_path = out_dir / 'lookup_conflicts.csv'
	with conflicts_path.open('w', encoding='utf-8', newline='') as f:
		w = csv.writer(f)
		w.writerow(['ip', 'field', 'values', 'source_files', 'kept_value', 'kept_source_file'])
		for ip, field, values, sources, kept_val, kept_src in conflicts:
			w.writerow([ip, field, '|'.join(values), '|'.join(sources), kept_val, kept_src])
	# log
	with log_path.open('a', encoding='utf-8', newline='') as log:
		log.write(f"[lookup] unique_ips={len(lookup)} conflicts={len(conflicts)}\n")
	return lookup_path, conflicts_path


def main() -> None:
	parser = argparse.ArgumentParser(description='Clean InfoByIP CSVs and build lookup table.')
	parser.add_argument('--run', required=True, help='Path to run directory containing infobyip_batch_*.csv')
	args = parser.parse_args()

	run_dir = Path(args.run)
	assert run_dir.exists(), f"run directory not found: {run_dir}"
	log_path = run_dir / 'process_log.txt'
	raw_csvs = sorted(run_dir.glob('infobyip_batch_*.csv'))
	cleaned: List[Path] = []
	for raw in raw_csvs:
		cleaned.append(_clean_one(raw, run_dir, log_path))
	lookup_path, conflicts_path = build_lookup(cleaned, run_dir, log_path)
	print(str(lookup_path))
	print(str(conflicts_path))


if __name__ == '__main__':
	main()



