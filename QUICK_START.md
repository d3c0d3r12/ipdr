# 🚀 Quick Start Guide - Police Intelligence System

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 16
- Git

---

## 🏃 Fast Setup (5 minutes)

### Step 1: Clone & Navigate
```bash
cd "c:\Users\saheb\Downloads\New FIR"
```

### Step 2: Setup Backend
```bash
cd backend
pip install -r requirements.txt
```

### Step 3: Setup Frontend
```bash
cd ../frontend
npm install
```

### Step 4: Configure Environment
Create/verify `.env` file in root:
```env
DATABASE_URL=postgresql+psycopg2://police_user:StrongPass@localhost/police_data
JWT_SECRET=supersecurekey
INFOBYIP_URL=https://www.infobyip.com/ipbulklookup.php
```

### Step 5: Setup Database
```bash
# Create database
psql -U postgres
CREATE DATABASE police_data;
CREATE USER police_user WITH PASSWORD 'StrongPass';
GRANT ALL PRIVILEGES ON DATABASE police_data TO police_user;
\q

# Run schema
psql -U police_user -d police_data -f database/setup.sql
```

### Step 6: Start Backend (Terminal 1)
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 7: Start Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```

### Step 8: Access Application
- 🌐 **Frontend**: http://localhost:3000
- 🌐 **Backend API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs

---

## 🐳 Docker Quick Start (Even Faster!)

```bash
# Start everything with one command
docker-compose up -d

# Access:
# Frontend: http://localhost:3001
# Backend: http://localhost:8000
```

---

## 🔑 Login Credentials

**Demo Accounts:**
- Inspector: `inspector` / `secure@123`
- Analyst: `analyst` / `an@123`

---

## 📤 Test Upload

1. Go to http://localhost:3000
2. Click "Upload HTML Log"
3. Enter FIR number (e.g., `FIR/2025/001`)
4. Select HTML file from `uploads/` folder
5. Click "Upload & Extract"
6. View results in "View IP Records"

---

## 🛠️ Troubleshooting

### Backend won't start?
```bash
# Check Python version
python --version  # Should be 3.10+

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Frontend won't start?
```bash
# Check Node version
node --version  # Should be 18+

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Database connection error?
```bash
# Check PostgreSQL is running
pg_isready

# Verify credentials in .env match your PostgreSQL setup
```

### Port already in use?
```bash
# Backend (change port)
uvicorn main:app --port 8001

# Frontend (change port in nuxt.config.ts)
```

---

## 📊 API Testing

### Using cURL
```bash
# Health check
curl http://localhost:8000/

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"inspector","password":"secure@123"}'

# Get summary
curl http://localhost:8000/api/data/summary
```

### Using Browser
Visit http://localhost:8000/docs for interactive API documentation

---

## 🎯 Next Steps

1. ✅ Upload test HTML file
2. ✅ View extracted IP records
3. ✅ Check analytics dashboard
4. ✅ Export to Excel
5. ✅ Explore API documentation

---

## 📞 Support

For issues or questions:
1. Check `IMPROVEMENTS_SUMMARY.md` for details
2. Review `README_IMPLEMENTATION.md` for full documentation
3. Check logs in `logs/` directory

---

## ⚡ Performance Tips

- Use Docker for consistent environment
- Enable Redis for caching (already in docker-compose)
- Use PostgreSQL connection pooling for production
- Enable Nuxt production mode: `npm run build && npm start`

---

**Ready to go! 🎉**
