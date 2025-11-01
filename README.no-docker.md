# Police Intelligence System (No Docker / No C++)

## Prereqs
- Python 3.11+
- Node.js 18+
- (Optional) PostgreSQL (local). Default dev uses SQLite.

## Backend (FastAPI)
```
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
# source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
- Health: http://localhost:8000/health

## Frontend (Nuxt 3)
```
cd frontend
npm ci --no-audit --no-fund || npm install
set NUXT_PUBLIC_API_BASE=http://localhost:8000  # Windows
# export NUXT_PUBLIC_API_BASE=http://localhost:8000  # Linux/Mac
npm run dev -- -p 3001
```
- App: http://localhost:3001

## Workflow
1. Go to Upload page → select FIR No. + HTML file → Upload & Extract
   - Backend creates run folder under `backend/processed/<timestamp>_<FIR>` with `original_log.csv` and `batch_*.txt`.
2. Submit each `batch_*.txt` to InfoByIP; download CSVs and place them in the run folder as `infobyip_batch_001.csv`, `infobyip_batch_002.csv`, ...
3. Click "Process Batches" → backend merges CSVs and writes `master_ip_data.xlsx` in the same run folder.
4. Click "Download Excel" to get the master output.

## Notes
- Original timestamps and IPs are preserved verbatim in `original_log.csv` and final Excel.
- If any rows lack data, they are kept; missing enrichment remains blank.
- For Postgres later, set `DATABASE_URL` env and add async driver; dev uses SQLite to avoid build tools.
