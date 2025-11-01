# 🏗️ System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER (Officer)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Nuxt 3 / Vue 3)                    │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────────┐  │
│  │Dashboard │  Upload  │ IP List  │Analytics │     Map      │  │
│  │(index)   │          │          │          │              │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────────┘  │
│                    Port: 3000 (Dev) / 3001 (Docker)             │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST API
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI / Python)                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Routers                           │  │
│  │  ┌────────┬─────────┬──────────┬────────────────────┐   │  │
│  │  │ Upload │ Process │   Data   │  Authentication    │   │  │
│  │  │        │         │          │                    │   │  │
│  │  └────────┴─────────┴──────────┴────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Core Modules                          │  │
│  │  ┌────────┬─────────┬──────────────────────────────┐    │  │
│  │  │ Config │   DB    │       Security (JWT)         │    │  │
│  │  └────────┴─────────┴──────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Utils / Workers                       │  │
│  │  ┌────────────┬────────────┬────────────┬──────────┐    │  │
│  │  │Extract HTML│Process Batch│Merge Data │CSV Clean │    │  │
│  │  └────────────┴────────────┴────────────┴──────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                         Port: 8000                              │
└────────────┬────────────────────────────┬───────────────────────┘
             │                            │
             ▼                            ▼
┌─────────────────────────┐  ┌─────────────────────────────────┐
│  PostgreSQL Database    │  │   External: InfoByIP Service    │
│  ┌──────────────────┐   │  │  (IP Geolocation Enrichment)    │
│  │   ip_records     │   │  │                                 │
│  │   - id           │   │  │  Batch lookup: 100 IPs/request  │
│  │   - timestamp    │   │  │  Returns: Country, City, ISP    │
│  │   - ip           │   │  └─────────────────────────────────┘
│  │   - country      │   │
│  │   - city         │   │
│  │   - isp          │   │
│  └──────────────────┘   │
│      Port: 5432         │
└─────────────────────────┘

```

---

## Data Flow Diagram

```
┌──────────────┐
│   Officer    │
│  Uploads     │
│  HTML File   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ STEP 1: Upload & Parse                                   │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Frontend sends file + FIR number to /api/upload/   │   │
│ │ Backend saves to uploads/ and processed/ folders   │   │
│ │ HTML parser extracts "IP ACTIVITY" table           │   │
│ │ Creates: original_log.csv with all IP entries      │   │
│ └────────────────────────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│ STEP 2: Batch Creation                                   │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Split IPs into batches of 100                      │   │
│ │ Creates: batch_001.txt, batch_002.txt, ...        │   │
│ │ Preserves duplicates and order                     │   │
│ └────────────────────────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│ STEP 3: IP Enrichment (Background Task)                  │
│ ┌────────────────────────────────────────────────────┐   │
│ │ For each batch:                                    │   │
│ │   - Submit to InfoByIP bulk lookup                 │   │
│ │   - Wait for CSV response                          │   │
│ │   - Save as infobyip_batch_001.csv                 │   │
│ │   - Delay 1 second between requests                │   │
│ └────────────────────────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│ STEP 4: Data Cleaning & Merging                          │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Clean each InfoByIP CSV:                           │   │
│ │   - Remove duplicates                              │   │
│ │   - Standardize columns                            │   │
│ │   - Handle conflicts                               │   │
│ │ Build lookup table: ip_lookup_table.csv            │   │
│ └────────────────────────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│ STEP 5: Master Excel Generation                          │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Merge original_log.csv + ip_lookup_table.csv       │   │
│ │ Add enriched columns:                              │   │
│ │   - Country, Region, City                          │   │
│ │   - ISP, Organization                              │   │
│ │   - Latitude, Longitude                            │   │
│ │ Export: master_ip_data.xlsx                        │   │
│ └────────────────────────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│ STEP 6: Database Storage (Optional)                      │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Insert records into PostgreSQL                     │   │
│ │ Table: ip_records                                  │   │
│ │ Enables: Querying, filtering, analytics           │   │
│ └────────────────────────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│ STEP 7: Visualization & Export                           │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Frontend displays:                                 │   │
│ │   - Dashboard statistics                           │   │
│ │   - IP records table                               │   │
│ │   - Geographic map                                 │   │
│ │   - Analytics charts                               │   │
│ │ Officer downloads Excel file                       │   │
│ └────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

---

## Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Layer                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  index.vue ──────────┐                                      │
│                      │                                      │
│  upload.vue ─────────┼──► API Calls (fetch/axios)          │
│                      │                                      │
│  ip-list.vue ────────┤                                      │
│                      │                                      │
│  analytics.vue ──────┤                                      │
│                      │                                      │
│  map.vue ────────────┘                                      │
│                                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP REST
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend Layer                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  main.py (FastAPI) ──┬──► Routers                          │
│                      │     ├─ upload.py                    │
│                      │     ├─ process.py                   │
│                      │     ├─ data.py                      │
│                      │     └─ auth.py                      │
│                      │                                      │
│                      ├──► Core                             │
│                      │     ├─ config.py                    │
│                      │     ├─ db.py                        │
│                      │     └─ security.py                  │
│                      │                                      │
│                      ├──► Models                           │
│                      │     └─ ip_record.py                 │
│                      │                                      │
│                      └──► Utils                            │
│                            ├─ extract_html.py              │
│                            ├─ process_batches.py           │
│                            ├─ merge_data.py                │
│                            ├─ csv_cleaner.py               │
│                            └─ excel_exporter.py            │
│                                                             │
└──────────────────────┬──────────────────┬──────────────────┘
                       │                  │
                       ▼                  ▼
            ┌──────────────────┐  ┌──────────────────┐
            │   PostgreSQL     │  │   File System    │
            │   Database       │  │   - uploads/     │
            │                  │  │   - processed/   │
            └──────────────────┘  │   - logs/        │
                                  └──────────────────┘
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: Authentication                                    │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ JWT Token-based authentication                        │ │
│  │ Login: /api/auth/login                                │ │
│  │ Returns: JWT token with user info                     │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Layer 2: Authorization                                     │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Role-based access control (future)                    │ │
│  │ Inspector: Full access                                │ │
│  │ Analyst: Read-only access                             │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Layer 3: Data Protection                                   │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ HTTPS in production                                   │ │
│  │ Environment variables for secrets                     │ │
│  │ Database password encryption                          │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Layer 4: Input Validation                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Pydantic models for request validation                │ │
│  │ File type checking (.html only)                       │ │
│  │ SQL injection prevention (ORM)                        │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture (Docker)

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Frontend Container (Nuxt)                          │   │
│  │  Image: node:18                                     │   │
│  │  Port: 3001:3000                                    │   │
│  │  Env: NUXT_PUBLIC_API_BASE=http://localhost:8000   │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Backend Container (FastAPI)                        │   │
│  │  Image: python:3.10                                 │   │
│  │  Port: 8000:8000                                    │   │
│  │  Env: DATABASE_URL, REDIS_URL, SECRET_KEY          │   │
│  └─────────────────────────────────────────────────────┘   │
│                     │              │                        │
│                     ▼              ▼                        │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │  PostgreSQL          │  │  Redis               │        │
│  │  Container           │  │  Container           │        │
│  │  Port: 5432          │  │  Port: 6379          │        │
│  │  Volume: db_data     │  │  (Caching)           │        │
│  └──────────────────────┘  └──────────────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## File System Structure

```
processed/
└── 20250131_120000_FIR-2025-001/
    ├── SubscriberInfo.html          # Original uploaded file
    ├── original_log.csv             # Extracted IP activity
    ├── batch_001.txt                # IP batch 1 (100 IPs)
    ├── batch_002.txt                # IP batch 2 (100 IPs)
    ├── infobyip_batch_001.csv       # Enriched data batch 1
    ├── infobyip_batch_002.csv       # Enriched data batch 2
    ├── ip_lookup_table.csv          # Merged lookup table
    ├── lookup_conflicts.csv         # Duplicate IP conflicts
    ├── master_ip_data.xlsx          # Final Excel export
    └── process_log.txt              # Processing logs
```

---

**This architecture ensures:**
- ✅ Scalability
- ✅ Maintainability
- ✅ Security
- ✅ Performance
- ✅ Reliability
