import os
import tarfile
import urllib.request
from pathlib import Path
import getpass


def _download(url: str, dest: Path) -> None:
	dest.parent.mkdir(parents=True, exist_ok=True)
	with urllib.request.urlopen(url) as r, dest.open("wb") as f:
		f.write(r.read())


def _extract_mmdb(tar_path: Path, out_dir: Path) -> None:
	with tarfile.open(tar_path, "r:gz") as tf:
		mmdb_members = [m for m in tf.getmembers() if m.name.endswith(".mmdb")]
		for m in mmdb_members:
			name = Path(m.name).name
			out_path = out_dir / name
			out_dir.mkdir(parents=True, exist_ok=True)
			with tf.extractfile(m) as src, out_path.open("wb") as dst:
				dst.write(src.read())


def main() -> int:
	license_key = os.getenv("MAXMIND_LICENSE_KEY", "").strip()
	if not license_key:
		license_key = getpass.getpass("MAXMIND_LICENSE_KEY: ").strip()
		if not license_key:
			print("MAXMIND_LICENSE_KEY not set.")
			return 1

	base_dir = Path(__file__).resolve().parent
	geoip_dir = base_dir / "geoip"

	city_url = f"https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key={license_key}&suffix=tar.gz"
	asn_url = f"https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key={license_key}&suffix=tar.gz"

	tmp_dir = base_dir / ".geoip_tmp"
	tmp_dir.mkdir(parents=True, exist_ok=True)

	city_tar = tmp_dir / "GeoLite2-City.tar.gz"
	asn_tar = tmp_dir / "GeoLite2-ASN.tar.gz"

	_download(city_url, city_tar)
	_download(asn_url, asn_tar)

	_extract_mmdb(city_tar, geoip_dir)
	_extract_mmdb(asn_tar, geoip_dir)

	print(f"Installed GeoLite2 databases into: {geoip_dir}")
	print(f"GEOIP_CITY_DB={geoip_dir / 'GeoLite2-City.mmdb'}")
	print(f"GEOIP_ASN_DB={geoip_dir / 'GeoLite2-ASN.mmdb'}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
