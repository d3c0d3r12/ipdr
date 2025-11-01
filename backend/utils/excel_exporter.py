import argparse
from pathlib import Path
import pandas as pd


def export_to_excel(csv_path: Path, out_xlsx: Path) -> Path:
	df = pd.read_csv(csv_path, dtype=str).fillna('')
	df.to_excel(out_xlsx, index=False)
	return out_xlsx


def main() -> None:
	parser = argparse.ArgumentParser(description='Export a CSV file to Excel (.xlsx).')
	parser.add_argument('--csv', required=True, help='Input CSV path')
	parser.add_argument('--out', required=False, help='Output XLSX path')
	args = parser.parse_args()

	csv_path = Path(args.csv)
	assert csv_path.exists(), f"CSV not found: {csv_path}"
	out_xlsx = Path(args.out) if args.out else csv_path.with_suffix('.xlsx')
	out = export_to_excel(csv_path, out_xlsx)
	print(str(out))


if __name__ == '__main__':
	main()





