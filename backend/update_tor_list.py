"""Download the Tor exit node list and save it locally for offline VPS/TOR detection."""
import sys
import urllib.request
from pathlib import Path

TOR_LIST_URL = "https://www.dan.me.uk/torlist/"
FALLBACK_URL = "https://check.torproject.org/torbulkexitlist"
OUT_FILE = Path(__file__).resolve().parent / "geoip" / "tor_exits.txt"


def fetch(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def main() -> int:
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    for url in (TOR_LIST_URL, FALLBACK_URL):
        try:
            print(f"Fetching TOR exit list from {url} …")
            content = fetch(url)
            ips = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
            if not ips:
                print("  Got empty list, trying fallback…")
                continue
            OUT_FILE.write_text("\n".join(ips), encoding="utf-8")
            print(f"  Saved {len(ips)} TOR exit nodes → {OUT_FILE}")
            return 0
        except Exception as e:
            print(f"  Failed: {e}")

    print("ERROR: Could not fetch TOR exit list from any source.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
