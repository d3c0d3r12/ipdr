# 🏗️ POLICE INTELLIGENCE SYSTEM
## Complete Implementation Guide

## 📋 Project Overview

This is a **real-time IP tracing and enrichment system** designed for Delhi Police Cyber Cell investigators. It processes Google subscriber HTML files to extract IP activity data, enriches it with geolocation information, and generates comprehensive Excel reports.

---

## 🧱 PROJECT STRUCTURE

```
police-intel-system/
│
├── backend/                # Python FastAPI backend
│   ├── main.py            # FastAPI app entry point
│   ├── core/              # Core configuration
│   │   ├── config.py      # Environment & settings
│   │   ├── db.py          # Database connection
│   │   └── security.py    # JWT authentication
│   │
│   ├── routers/           # API endpoints
│   │   ├── upload.py      # File upload handler
│   │   ├── process.py     # Data processing
│   │   ├── data.py        # Data retrieval
│   │   └── auth.py        # Authentication
│   │
│   ├── models/            # Database models
│   │   └── ip_record.py   # IP record schema
│   │
│   ├── utils/             # Utility functions
│   │   ├── extract_html.py      # HTML parsing
│   │   ├── process_batches.py   # Batch processing
│   │   ├── merge_data.py        # Data merging
│   │   ├── csv_cleaner.py       # CSV cleaning
│   │   └── excel_exporter.py    # Excel generation
│   │
│   ├── uploads/           # Raw HTML uploads
│   ├── processed/         # Extracted CSVs
│   └── requirements.txt   # Python dependencies
│
├── frontend/              # Nuxt 3 (Vue) frontend
│   ├── pages/
│   │   ├── index.vue      # Dashboard
│   │   ├── upload.vue     # File upload
│   │   ├── ip-list.vue    # IP records table
│   │   ├── map.vue        # Geographic visualization
│   │   └── analytics.vue  # Charts & statistics
│   │
│   ├── components/        # Reusable components
│   ├── nuxt.config.ts     # Nuxt configuration
│   └── package.json       # Node dependencies
│
├── database/              # SQL and migrations
│   └── setup.sql          # Database schema
│
├── server/                # Node.js standalone server (alternative)
│   ├── index.js           # Express server
│   └── lib/               # Helper libraries
│
├── logs/                  # Processing & activity logs
├── .env                   # Configuration (DB creds, JWT key)
├── docker-compose.yml     # Docker setup
└── README.md              # Project documentation
```

---

## ⚙️ BACKEND (FastAPI)

### **API Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/upload/` | POST | Upload HTML file |
| `/api/process/extract` | GET | Extract IPs from HTML |
| `/api/process/merge` | POST | Merge InfoByIP CSVs |
| `/api/process/export` | GET | Download Excel file |
| `/api/data/` | GET | Get IP records |
| `/api/data/summary` | GET | Get statistics |
| `/api/auth/login` | POST | Officer login |

### **Core Configuration**

**`backend/core/config.py`**
```python
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET")
UPLOAD_DIR = "backend/uploads"
PROCESSED_DIR = "backend/processed"
MASTER_DIR = "backend/master"
```

### **Database Model**

**`backend/models/ip_record.py`**
```python
from sqlalchemy import Column, Integer, String, DateTime, func
from core.db import metadata
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base(metadata=metadata)

class IPRecord(Base):
    __tablename__ = "ip_records"
    id = Column(Integer, primary_key=True)
    timestamp = Column(String)
    ip = Column(String)
    country = Column(String)
    region = Column(String)
    city = Column(String)
    isp = Column(String)
    source_file = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

---

## 🧩 FRONTEND (Nuxt 3)

### **Pages**

1. **`index.vue`** - Dashboard with statistics cards
2. **`upload.vue`** - File upload interface
3. **`ip-list.vue`** - Paginated IP records table
4. **`map.vue`** - Geographic visualization
5. **`analytics.vue`** - Charts and analytics

### **Key Features**

- ✅ Modern dark theme UI
- ✅ Responsive design
- ✅ Real-time data fetching
- ✅ Error handling
- ✅ Loading states

---

## 🗄️ DATABASE (PostgreSQL)

**`database/setup.sql`**
```sql
CREATE TABLE IF NOT EXISTS ip_records (
  id SERIAL PRIMARY KEY,
  timestamp TEXT,
  ip TEXT,
  country TEXT,
  region TEXT,
  city TEXT,
  isp TEXT,
  source_file TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔐 ENVIRONMENT VARIABLES

**`.env`**
```env
DATABASE_URL=postgresql+psycopg2://police_user:StrongPass@localhost/police_data
JWT_SECRET=supersecurekey
INFOBYIP_URL=https://www.infobyip.com/ipbulklookup.php
```

---

## ⚡ RUNNING THE SYSTEM

### **1. Start Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### **2. Start Frontend**
```bash
cd frontend
npm install
npm run dev
```

### **3. Access the Application**
- 🌐 Frontend: http://localhost:3000
- 🌐 Backend API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs

---

## 🐳 DOCKER DEPLOYMENT

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- FastAPI backend (port 8000)
- Nuxt frontend (port 3001)

---

## 📊 WORKFLOW

1. **Upload** → Officer uploads Google SubscriberInfo HTML file with FIR number
2. **Extract** → System parses HTML to find "IP ACTIVITY" table
3. **Batch** → IPs are split into batches of 100 (preserves duplicates)
4. **Enrich** → Each batch is submitted to InfoByIP bulk lookup
5. **Merge** → All batch results are merged into single CSV
6. **Export** → Final master Excel file with enriched geolocation data

---

## 🔧 TECH STACK

**Backend:**
- FastAPI 0.115.2
- SQLAlchemy 2.0.36
- Pandas 2.2.3
- BeautifulSoup4 4.12.3
- Selenium 4.25.0

**Frontend:**
- Nuxt 3
- Vue 3
- TypeScript
- Tailwind CSS

**Infrastructure:**
- PostgreSQL 16
- Redis 7
- Docker & Docker Compose

---

## 📝 AUTHENTICATION

Default users (for demo):
- Username: `inspector` | Password: `secure@123`
- Username: `analyst` | Password: `an@123`

---

## ✅ FEATURES

✔ Upload HTML inspector logs  
✔ Extract timestamps & IPs (backend)  
✔ Process InfoByIP data  
✔ Merge and store in PostgreSQL  
✔ Display on frontend with filters, maps, and charts  
✔ Export results to Excel  
✔ JWT authentication  
✔ Background processing  
✔ Batch IP enrichment  
✔ Duplicate preservation  

---

## 📄 LICENSE

For authorized law enforcement use only. Data is processed locally; IP enrichment is fetched from InfoByIP.

---

## 🚀 NEXT STEPS

1. Configure `.env` with your database credentials
2. Run database migrations: `python -m alembic upgrade head`
3. Start backend and frontend servers
4. Access dashboard at http://localhost:3000
5. Upload HTML files and process IP data

---

**Built for Delhi Police Cyber Cell** 🚔
