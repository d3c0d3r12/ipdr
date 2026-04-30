# Security Audit Report (OWASP-Oriented)

## Summary
The application implements authentication, path traversal protections, file validation, and safe error handling to reduce common OWASP risks for an IPDR processing workflow.

## Findings and Controls
### Authentication & Authorization
- Protected endpoints require Bearer token authentication:
  - Upload (`/api/upload/`)
  - IPDR enrichment + exports (`/api/process/ipdr/...`)
  - Data endpoints (`/api/data/...`)
- Session expiry validation is handled safely for both timezone-aware and timezone-naive database values.

### File Upload Security
- Accepted file types restricted to `.html/.htm/.csv`.
- Upload size restricted using backend configuration.
- Filenames and FIR identifiers are sanitized to prevent unsafe filesystem behavior.
- Only public (globally routable) IPs are processed; private/reserved IPs are rejected and reported as problems.

### Path Traversal Prevention
- Run directory parameters are constrained under the configured processed directory using safe resolution.
- Absolute paths are normalized to run basenames to avoid arbitrary filesystem access.

### Injection Protection
- Database operations use SQLAlchemy ORM patterns for query composition.
- Run directory and file access use constrained paths rather than raw user-provided filesystem paths.

### Error Handling & Logging
- Global exception handling returns user-safe messages and includes a request ID for investigation.
- Internal exceptions are logged server-side without leaking sensitive stack traces to the UI.

### CORS & Browser Security
- Local development origins are allowed safely using regex-based origin rules for localhost and local network hosts.
- Credentialed requests are supported for authenticated API calls.

## Recommended Operational Practices
- Store `JWT_SECRET` securely in environment variables and rotate periodically.
- Run backend behind HTTPS in production.
- Use GeoLite databases for bulk enrichment to avoid leaking investigative IP lists to third-party APIs.
