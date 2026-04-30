# IPDR Tracking Hub — User Manual

## Login
- Open the web app and sign up (or use your admin user).
- Log in to access file upload and results.

## Upload IPDR File (HTML/CSV)
- Go to **Upload & Extract**.
- Select an IPDR file:
  - HTML: `.html` / `.htm`
  - CSV: `.csv`
- Enter FIR number (optional) and upload.
- The system stores a run directory and extracts **public (globally routable)** IPs only.

## Enrich & Categorize (GeoLite Recommended)
- In **Processing**, paste/select the run directory (it also accepts full path, but only the run name is used).
- Click **Start ISP/WHOIS Enrichment**.
- Use **Refresh Status** until completed.

### Offline GeoLite Setup (For Thousands of IPs)
To process large volumes efficiently, configure GeoLite databases:
- Download MaxMind GeoLite2 databases:
  - GeoLite2-City.mmdb
  - GeoLite2-ASN.mmdb
- Set environment variables for the backend:
  - `GEOIP_CITY_DB=/absolute/path/to/GeoLite2-City.mmdb`
  - `GEOIP_ASN_DB=/absolute/path/to/GeoLite2-ASN.mmdb`

When GeoLite is configured, the system classifies ISP using ASN Organization and resolves geo fields offline.

## Results
The results view provides:
- **ISP categorization** (Top ISPs by count)
- **Common/Shared IPs** (IPs repeated in the same run)
- **IP metadata panel** (ISP/org, geo fields, usage stats)

## Export
From the results section:
- Download CSV
- Download JSON
- Download PDF

## Notes
- If you need live RDAP/WHOIS lookups for each IP, enable:
  - `IPDR_WHOIS_RDAP=1`
  - Recommended only for smaller IP sets due to network cost.
