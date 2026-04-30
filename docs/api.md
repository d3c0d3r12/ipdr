# IPDR Tracking Hub — API Documentation

## Authentication
### POST `/api/auth/signup`
Creates a new user.

Request JSON:
- `username` (string)
- `email` (string)
- `password` (string)
- `full_name` (string)
- `role` (string)

### POST `/api/auth/login`
Authenticates a user and returns a bearer token.

Request JSON:
- `username` (string)
- `password` (string)

Response JSON:
- `success` (boolean)
- `access_token` (string)

All endpoints below require:
- `Authorization: Bearer <token>`

## Upload
### POST `/api/upload/`
Uploads an IPDR file and extracts valid public IP rows.

Form fields:
- `file` (multipart file): `.html/.htm/.csv`
- `fir` (string, optional)
- `preserve_duplicates` (boolean string, optional)
- `bypass_cloudflare` (boolean string, optional; enables legacy InfoByIP scraping)

Response:
- `run_dir` (string)
- `original_csv` (string)
- `problems_csv` (string|null)
- `count_rows` (number)
- `unique_ips` (number)
- `problem_rows` (number)

## IPDR Processing (Enrichment)
### POST `/api/process/ipdr/enrich/start?run_dir=<run>`
Starts enrichment and categorization for a given run.

Response:
- `task_id` (string)
- `total_ips` (number)
- `run_dir` (string)

### GET `/api/process/ipdr/enrich/status?task_id=<id>`
Returns background task progress.

### GET `/api/process/ipdr/enrich/summary?run_dir=<run>`
Returns summary JSON:
- `total_unique_ips`
- `total_records`
- `by_isp[]`
- `shared_ips[]`

### GET `/api/process/ipdr/enrich/results?run_dir=<run>&limit=<n>&offset=<n>`
Returns enriched IP rows:
- `ip`
- `isp`
- `country/region/city`
- `latitude/longitude/timezone/postal_code`
- `occurrences`, `first_seen`, `last_seen`
- `ip_type`
- `source` (`geolite` / `offline` / `ip-api` / etc.)
- `whois` (optional dict)

## Exports
### GET `/api/process/ipdr/enrich/export/csv?run_dir=<run>`
Downloads `ipdr_results.csv`.

### GET `/api/process/ipdr/enrich/export/json?run_dir=<run>`
Downloads `ipdr_results.json` containing `{ summary, results }`.

### GET `/api/process/ipdr/enrich/export/pdf?run_dir=<run>`
Downloads `ipdr_report.pdf`.

## Configuration
GeoLite recommended for large-scale processing:
- `GEOIP_CITY_DB=/path/to/GeoLite2-City.mmdb`
- `GEOIP_ASN_DB=/path/to/GeoLite2-ASN.mmdb`

Optional WHOIS RDAP:
- `IPDR_WHOIS_RDAP=1`
