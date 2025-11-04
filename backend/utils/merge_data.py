import argparse
import csv
from pathlib import Path

import pandas as pd


def _read_original(original_csv: Path) -> pd.DataFrame:
	df = pd.read_csv(original_csv, dtype=str).fillna('')
	# New simplified format: only timestamp and ip
	expected = ['timestamp', 'ip']
	missing = [c for c in expected if c not in df.columns]
	if missing:
		raise RuntimeError(f"original_log.csv missing columns: {missing}")
	return df


def _read_lookup(lookup_csv: Path) -> pd.DataFrame:
	df = pd.read_csv(lookup_csv, dtype=str).fillna('')
	expected = ['ip', 'country', 'region', 'city', 'isp', 'source_file']
	missing = [c for c in expected if c not in df.columns]
	if missing:
		raise RuntimeError(f"ip_lookup_table.csv missing columns: {missing}")
	return df


def merge_all(run_dir: Path) -> Path:
	original_csv = run_dir / 'original_log.csv'
	lookup_csv = run_dir / 'ip_lookup_table.csv'
	conflicts_csv = run_dir / 'lookup_conflicts.csv'
	missing_csv = run_dir / 'missing_lookups.csv'
	output_xlsx = run_dir / 'master_ip_data.xlsx'

	df_orig = _read_original(original_csv)
	df_lookup = _read_lookup(lookup_csv)

	# track conflict-kept IPs
	conflict_ips = set()
	if conflicts_csv.exists():
		df_conf = pd.read_csv(conflicts_csv, dtype=str)
		conflict_ips = set(df_conf['ip'].astype(str).tolist())

	merged = df_orig.merge(
		df_lookup,
		left_on='ip',
		right_on='ip',
		how='left',
		indicator=False
	)
	# prepare fields
	merged['lookup_source_file'] = merged['source_file'].fillna('')
	# derive status
	def _status(row: pd.Series) -> str:
		ip_val = row.get('ip', '')
		if ip_val == '' or pd.isna(ip_val):
			return 'missing_lookup'
		return 'conflict_kept' if ip_val in conflict_ips else 'matched'
	merged['merge_status'] = merged.apply(_status, axis=1)

	# select columns - simplified output
	out_cols = [
		'timestamp', 'ip',
		'country', 'region', 'city', 'isp', 'lookup_source_file', 'merge_status'
	]
	for c in ['country', 'region', 'city', 'isp']:
		if c not in merged.columns:
			merged[c] = ''
	merged[out_cols].to_excel(output_xlsx, index=False)

	# compute missing lookups
	unmatched = merged[merged['merge_status'] == 'missing_lookup']
	if not unmatched.empty:
		with missing_csv.open('w', encoding='utf-8', newline='') as f:
			w = csv.writer(f)
			w.writerow(['ip', 'first_seen_timestamp'])
			unique_missing = {}
			for _, r in df_orig.iterrows():
				ip = str(r['ip'])
				if ip and ip not in unique_missing:
					unique_missing[ip] = r['timestamp']
			for ip in sorted(set(unmatched['ip'].astype(str).tolist())):
				w.writerow([ip, unique_missing.get(ip, '')])

	return output_xlsx


def main() -> None:
	parser = argparse.ArgumentParser(description='Merge lookup enrichment into original events and export Excel.')
	parser.add_argument('--run', required=True, help='Path to run directory')
	args = parser.parse_args()
	out = merge_all(Path(args.run))
	print(str(out))


if __name__ == '__main__':
	main()






