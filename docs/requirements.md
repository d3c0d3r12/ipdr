# Delhi Police Cyber Cell: Real-Time IP Tracing System

## 1. Objectives
- Provide investigators with real-time IP intelligence (RDAP/WHOIS, GeoIP, ASN, reputation, passive DNS).
- Correlate IPs with events (complaints, cases, logs) and visualize on map/timeline.
- Support case management, collaboration, audit logging, and chain-of-custody exports.
- Ensure strict legal compliance, data minimization, and security best practices.

## 2. Legal, Ethical, and Compliance
- Use only legally authorized data sources; any sensitive or subscriber data must be obtained via due process.
- Comply with Indian laws (IT Act 2000/2008, CrPC, data protection guidelines), vendor ToS, and internal SOPs.
- Maintain audit logs for all access; immutable exports for court submission.
- Data minimization: store only what is necessary for a case; configurable retention with secure deletion.
- Access control: role-based, least privilege, and regular access reviews.

## 3. Core Features
- IP Lookup: RDAP/WHOIS, GeoIP, ASN, allocation, abuse contacts, reputation feeds.
- Enrichment: Reverse DNS, passive DNS (if licensed), open ports (Shodan/Censys if licensed), hosting/ISP info.
- Mapping: World map with IP geolocation, ASN boundaries, confidence radius.
- Timeline: Events (complaint, lookup, action) plotted; filter by time range.
- Case Workspace: Create cases, attach evidence, notes, tags, link related indicators.
- Collaboration: Assign tasks, comment threads, activity feed.
- Real-time Updates: Background enrichment and notifications via WebSocket/SSE.
- Reporting: Case summary, chain-of-custody, PDF/CSV exports.
- Audit Logging: Every read/write with who/when/what; tamper-evident.

## 4. Data Sources (pluggable)
- Public/Free: RDAP, WHOIS (rate-limited), Team Cymru ASN, IP2Location Lite/Free GeoIP, MaxMind GeoLite2.
- Licensed (optional): MaxMind GeoIP2/ASN, Shodan/Censys, Passive DNS providers, VirusTotal, AbuseIPDB.
- Internal: FIR/case databases, internal logs (if authorized), SIEM.

## 5. Non-Functional Requirements
- Security: OWASP ASVS L2/L3, TLS-only, secrets in vault, signed artifacts.
- Availability: 99.9% target; graceful degradation when vendors rate-limit.
- Performance: P95 page load < 2.5s; typical IP enrichment < 3s.
- Scalability: Horizontal for API and websockets; work queue for enrichment.
- Observability: Metrics, structured logs, tracing, health checks.
- Data Residency: Configurable; prefer in-country storage where required.

## 6. High-Level Architecture
- Web App (React/Next.js) + API (Node.js/Express or NestJS) + Worker (queue-based) + DB (PostgreSQL) + Cache (Redis) + Object Storage (evidence) + Message Broker (Redis streams/NATS/RabbitMQ).
- Integrations via provider adapters with retry/backoff and circuit breakers.
- Realtime via WebSocket/SSE; auth via JWT sessions with short TTL and refresh.

## 7. Roles and Permissions
- Admin: Manage users, roles, providers, retention.
- Investigator: View/create cases, run lookups, export reports.
- Auditor: Read-only access to logs and reports.
- Custom roles via granular permissions.

## 8. Data Model (initial sketch)
- User(id, name, role, org)
- Case(id, title, status, createdBy, createdAt, tags)
- Indicator(id, type, value, caseId, firstSeen, lastSeen)
- LookupJob(id, indicatorId, provider, status, result, startedAt, finishedAt)
- Event(id, caseId, type, details, createdBy, createdAt)
- AuditLog(id, userId, action, subject, metadata, createdAt)
- Attachment(id, caseId, path, hash, size, createdAt)

## 9. Security Controls
- MFA; strong password policy; session management; IP allowlists for admin.
- RBAC enforcement server-side; attribute checks on case membership.
- Input validation, output encoding, SSRF/XXE disabled in HTTP clients.
- Rate limiting, quotas per user and per provider.
- At-rest encryption for DB and storage; field-level encryption for sensitive data.

## 10. Deployment & Environments
- Local dev (Docker Compose), Staging, Production.
- CI/CD with tests, lint, SCA, SAST; signed containers.
- Config via env vars; secrets via vault/KeyVault/SSM.

## 11. Open Questions (need your input)
1) Target stack preference (Node/NestJS + React, or Python/FastAPI + React)?
2) Must-have providers at launch (MaxMind, AbuseIPDB, Shodan, others)?
3) Offline capability requirements? Air-gapped?
4) Data retention periods per case type?
5) Deployment target (on-prem Windows Server, Linux VM, cloud)?
6) UI language/localization needs?
7) Any integration with existing Delhi Police systems/FIR database?

## 12. Milestones
- M1: Skeleton repo, auth, basic IP lookup (RDAP/GeoIP), case creation.
- M2: Worker queue, realtime updates, map and timeline, audit logging.
- M3: Reports/exports, additional providers, RBAC hardening, observability.
- M4: Compliance review, performance tuning, packaging and deployment.


