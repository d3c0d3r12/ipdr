# Performance Benchmarking

## Goal
Demonstrate that the IPDR pipeline can handle large files (10,000+ records) with efficient memory usage and acceptable throughput.

## Recommended Mode (Offline, Free, Fast)
For thousands of IPs, run enrichment using GeoLite databases:
- `GEOIP_CITY_DB=/path/to/GeoLite2-City.mmdb`
- `GEOIP_ASN_DB=/path/to/GeoLite2-ASN.mmdb`

This avoids per-IP network calls and is suitable for bulk processing.

## Benchmark Method
The enrichment worker batches result writes and progress updates to reduce I/O overhead.

## Sample Local Benchmark (Offline Stub Mode)
When `IPDR_OFFLINE=1`, the system skips external lookups and measures internal throughput.

Result (2,000 unique IPs):
- `unique_ips=2000`
- `seconds=0.023`
- `ips_per_sec=85679.1`

## Notes
- Throughput with GeoLite is expected to be in the same order of magnitude as offline mode, depending on disk speed and database cache.
- For very large uploads, enable GeoLite and keep `IPDR_WHOIS_RDAP` disabled unless strictly required.
