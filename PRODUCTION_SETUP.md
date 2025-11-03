# 🚀 **PRODUCTION DEPLOYMENT - COMPLETE GUIDE**

## 🎯 **ISSUE: Login Not Working on Production**

**Cause:** Admin user doesn't exist in production database yet.

---

## ✅ **SOLUTION: Initialize Production Database**

### **Step 1: Access Production Server**

**If using SSH:**
```bash
ssh user@your-server.com
```

**If using hosting panel:**
- Login to your hosting control panel
- Open terminal/SSH access

---

### **Step 2: Navigate to Backend Directory**

```bash
cd /path/to/your/backend
# Example: cd /var/www/ipdr-tracking-hub/backend
```

---

### **Step 3: Run Database Initialization**

```bash
python init_database.py
```

**Expected Output:**
```
======================================================================
  IPDR TRACKING HUB - DATABASE INITIALIZATION
  Delhi Police Cyber Cell
======================================================================

🔧 Initializing database...
✅ All tables created successfully!

👤 Creating initial admin user...
✅ Admin user created successfully!
   Username: admin
   Password: Admin@123456
   ⚠️  PLEASE CHANGE THIS PASSWORD IMMEDIATELY!

📋 Create sample FIR case for testing? (y/n): n

======================================================================
✅ Database initialization complete!
======================================================================
```

---

### **Step 4: Verify Database Connection**

**Check if production DATABASE_URL is set:**

```bash
# Check .env file
cat .env | grep DATABASE_URL
```

**Should show:**
```
DATABASE_URL=postgresql://username:password@host:port/database
```

**If missing, create .env file:**
```bash
nano .env
```

**Add:**
```
DATABASE_URL=your_production_database_url
SECRET_KEY=your_secret_key
ENVIRONMENT=production
```

---

## 🔑 **PRODUCTION CREDENTIALS:**

After running `init_database.py`:

```
Username: admin
Password: Admin@123456
```

**⚠️ IMPORTANT: Change this password immediately after first login!**

---

## 🐛 **COMMON PRODUCTION ISSUES:**

### **Issue 1: "Database connection failed"**

**Cause:** DATABASE_URL not set or incorrect

**Fix:**
```bash
# Check .env file exists
ls -la .env

# Check DATABASE_URL
cat .env | grep DATABASE_URL

# If missing, add it:
echo "DATABASE_URL=your_neon_db_url" >> .env
```

---

### **Issue 2: "Module not found"**

**Cause:** Dependencies not installed

**Fix:**
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements_auth.txt
```

---

### **Issue 3: "Permission denied"**

**Cause:** File permissions

**Fix:**
```bash
# Fix permissions
chmod +x init_database.py
chmod 644 .env
```

---

### **Issue 4: "Table already exists"**

**Cause:** Database already initialized (this is OK!)

**Fix:**
```bash
# Just create admin user manually
python -c "
from core.db import SessionLocal
from services.auth_service import AuthService

db = SessionLocal()
admin, msg = AuthService.create_user(
    db=db,
    username='admin',
    email='admin@delhipolice.gov.in',
    password='Admin@123456',
    full_name='System Administrator',
    role='admin'
)
if admin:
    admin.is_verified = True
    admin.is_active = True
    db.commit()
    print('✅ Admin created')
else:
    print(f'❌ Error: {msg}')
db.close()
"
```

---

## 📊 **PRODUCTION CHECKLIST:**

### **Backend:**
- [ ] Code pushed to production
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] .env file created with DATABASE_URL
- [ ] Database initialized (`python init_database.py`)
- [ ] Admin user created
- [ ] Backend server running (uvicorn/gunicorn)
- [ ] Port 8000 accessible

### **Frontend:**
- [ ] Code pushed to production
- [ ] Dependencies installed (`npm install`)
- [ ] Built for production (`npm run build`)
- [ ] Environment variables set (API_URL)
- [ ] Frontend server running (port 3000)
- [ ] Domain/subdomain configured

### **Database:**
- [ ] Neon PostgreSQL database created
- [ ] Connection string obtained
- [ ] DATABASE_URL set in .env
- [ ] Tables created
- [ ] Admin user exists

---

## 🌐 **ENVIRONMENT VARIABLES:**

### **Backend (.env):**
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Environment
ENVIRONMENT=production
DEBUG=False

# CORS (if needed)
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

### **Frontend (.env):**
```bash
# API URL
NUXT_PUBLIC_API_URL=https://api.your-domain.com

# Or if same domain:
NUXT_PUBLIC_API_URL=https://your-domain.com/api
```

---

## 🚀 **DEPLOYMENT STEPS:**

### **Option 1: Manual Deployment**

**Backend:**
```bash
# 1. SSH to server
ssh user@server

# 2. Navigate to project
cd /var/www/ipdr-tracking-hub

# 3. Pull latest code
git pull origin main

# 4. Install dependencies
cd backend
pip install -r requirements.txt

# 5. Initialize database
python init_database.py

# 6. Restart backend
systemctl restart ipdr-backend
# Or: pm2 restart ipdr-backend
```

**Frontend:**
```bash
# 1. Navigate to frontend
cd /var/www/ipdr-tracking-hub/frontend

# 2. Pull latest code
git pull origin main

# 3. Install dependencies
npm install

# 4. Build
npm run build

# 5. Restart frontend
pm2 restart ipdr-frontend
```

---

### **Option 2: Using CI/CD (GitHub Actions)**

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy Backend
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.SERVER_HOST }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /var/www/ipdr-tracking-hub
          git pull origin main
          cd backend
          pip install -r requirements.txt
          systemctl restart ipdr-backend
    
    - name: Deploy Frontend
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.SERVER_HOST }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /var/www/ipdr-tracking-hub/frontend
          npm install
          npm run build
          pm2 restart ipdr-frontend
```

---

## 🔒 **SECURITY CHECKLIST:**

- [ ] Change default admin password
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS (SSL certificate)
- [ ] Set proper CORS origins
- [ ] Disable DEBUG mode
- [ ] Set secure cookie flags
- [ ] Use environment variables (not hardcoded)
- [ ] Restrict database access
- [ ] Enable firewall rules
- [ ] Regular security updates

---

## 📝 **QUICK FIX FOR PRODUCTION:**

If login not working on production:

```bash
# 1. SSH to production server
ssh user@your-server.com

# 2. Navigate to backend
cd /path/to/backend

# 3. Run init script
python init_database.py

# 4. Test login
# Go to: https://your-domain.com/login
# Username: admin
# Password: Admin@123456

# 5. Change password immediately!
```

---

## 🎯 **VERIFY PRODUCTION:**

### **Test Backend:**
```bash
curl https://your-domain.com/api/health
# Should return: {"status": "ok"}
```

### **Test Database:**
```bash
curl https://your-domain.com/api/auth/login \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@123456"}'
# Should return: {"access_token": "..."}
```

### **Test Frontend:**
```
1. Go to: https://your-domain.com/login
2. Enter: admin / Admin@123456
3. Should login successfully
```

---

## 🐛 **DEBUGGING PRODUCTION:**

### **Check Backend Logs:**
```bash
# If using systemd
journalctl -u ipdr-backend -f

# If using PM2
pm2 logs ipdr-backend

# If using Docker
docker logs ipdr-backend
```

### **Check Frontend Logs:**
```bash
# PM2
pm2 logs ipdr-frontend

# Docker
docker logs ipdr-frontend
```

### **Check Database Connection:**
```bash
# Test connection
python -c "
from core.db import engine
try:
    conn = engine.connect()
    print('✅ Database connected')
    conn.close()
except Exception as e:
    print(f'❌ Error: {e}')
"
```

---

## 📊 **PRODUCTION ARCHITECTURE:**

```
User Browser
    ↓
Frontend (Port 3000)
    ↓
Backend API (Port 8000)
    ↓
PostgreSQL Database (Neon)
```

---

## 🎉 **AFTER SETUP:**

1. ✅ Database initialized
2. ✅ Admin user created
3. ✅ Backend running
4. ✅ Frontend running
5. ✅ Can login with admin credentials
6. ✅ Change admin password
7. ✅ Create additional users
8. ✅ System ready for use

---

## 📝 **IMPORTANT NOTES:**

1. **Always backup database** before updates
2. **Test in staging** before production
3. **Monitor logs** regularly
4. **Keep dependencies updated**
5. **Regular security audits**
6. **Document all changes**

---

**RUN `python init_database.py` ON PRODUCTION SERVER!** 🚀

This will create the admin user and fix the login issue! ✅
