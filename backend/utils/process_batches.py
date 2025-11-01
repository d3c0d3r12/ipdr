import argparse
import csv
from pathlib import Path
from typing import List


def create_batches_from_original(original_csv: Path, batch_size: int = 100) -> List[Path]:
	assert original_csv.exists(), f"original csv not found: {original_csv}"
	ips: List[str] = []
	with original_csv.open('r', encoding='utf-8', newline='') as f:
		reader = csv.DictReader(f)
		for row in reader:
			ips.append(row.get('ip_original', ''))
	# unique-first-seen
	seen = set()
	unique_ips: List[str] = []
	for ip in ips:
		if ip and ip not in seen:
			seen.add(ip)
			unique_ips.append(ip)
	batch_paths: List[Path] = []
	for i in range(0, len(unique_ips), batch_size):
		chunk = unique_ips[i:i + batch_size]
		batch_no = i // batch_size + 1
		p = original_csv.parent / f"batch_{batch_no:03d}.txt"
		p.write_text('\n'.join(chunk), encoding='utf-8')
		batch_paths.append(p)
	# summary
	summary = original_csv.parent / 'batches_summary.csv'
	with summary.open('w', encoding='utf-8', newline='') as f:
		w = csv.writer(f)
		w.writerow(['batch_no', 'file', 'ip_count'])
		for i, p in enumerate(batch_paths, start=1):
			cnt = sum(1 for _ in p.read_text(encoding='utf-8').splitlines() if _.strip())
			w.writerow([i, p.name, cnt])
	return batch_paths


def main() -> None:
	parser = argparse.ArgumentParser(description='Create 100-IP lookup batches from original_log.csv')
	parser.add_argument('--original', required=True, help='Path to original_log.csv')
	parser.add_argument('--batch-size', type=int, default=100)
	args = parser.parse_args()

	paths = create_batches_from_original(Path(args.original), batch_size=args.batch_size)
	for p in paths:
		print(p)


if __name__ == '__main__':
	main()



