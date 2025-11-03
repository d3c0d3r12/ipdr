# 🔐 **SSH ACCESS GUIDE - Get Production Server Access**

## 🎯 **HOW TO GET SSH ACCESS:**

SSH access depends on your hosting provider. Here are the most common options:

---

## 📊 **COMMON HOSTING PROVIDERS:**

### **1. Vercel (Most Common for Next.js)**

**❌ No SSH Access** - Vercel is serverless

**Alternative Solutions:**
- Use Vercel CLI to run commands
- Use Vercel Environment Variables
- Use Vercel Postgres (built-in database)

**To initialize database on Vercel:**
```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Link project
vercel link

# Run command
vercel env pull
vercel dev
```

---

### **2. Netlify**

**❌ No SSH Access** - Netlify is serverless

**Alternative:**
- Use Netlify CLI
- Use Netlify Functions
- Use external database (Neon, Supabase)

---

### **3. Railway**

**✅ Has SSH-like access**

**How to access:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# Open shell
railway shell

# Run commands
python init_database.py
```

---

### **4. Render**

**✅ Has Shell access**

**How to access:**
1. Go to: https://dashboard.render.com
2. Select your service
3. Click "Shell" tab
4. Run commands directly in browser

**Or use Render CLI:**
```bash
# Install
npm install -g render-cli

# Login
render login

# Open shell
render shell <service-name>
```

---

### **5. DigitalOcean / AWS / Azure / GCP**

**✅ Full SSH Access**

**How to access:**
```bash
ssh username@your-server-ip

# Or with key
ssh -i /path/to/key.pem username@your-server-ip
```

**Get credentials from:**
- DigitalOcean: Dashboard → Droplets → Access
- AWS: EC2 Console → Instances → Connect
- Azure: Virtual Machines → Connect
- GCP: Compute Engine → SSH

---

### **6. Heroku**

**✅ Has Shell access**

**How to access:**
```bash
# Install Heroku CLI
npm install -g heroku

# Login
heroku login

# Run bash
heroku run bash -a your-app-name

# Run commands
python init_database.py
```

---

### **7. cPanel / Shared Hosting**

**✅ Usually has SSH**

**How to enable:**
1. Login to cPanel
2. Go to "Terminal" or "SSH Access"
3. Enable SSH access
4. Get credentials

**Connect:**
```bash
ssh username@your-domain.com
# Or
ssh username@server-ip
```

---

## 🔍 **HOW TO FIND YOUR HOSTING PROVIDER:**

### **Check your deployment:**

1. **Look at your Git repository settings**
   - GitHub → Settings → Pages
   - Check deployment provider

2. **Check your domain DNS**
   - Use: https://www.whatsmydns.net
   - Check CNAME records

3. **Check deployment URL**
   - Vercel: `*.vercel.app`
   - Netlify: `*.netlify.app`
   - Railway: `*.railway.app`
   - Render: `*.onrender.com`
   - Heroku: `*.herokuapp.com`

---

## 🎯 **ALTERNATIVE: NO SSH NEEDED**

If you can't get SSH access, you can initialize the database differently:

### **Option 1: Use Database GUI**

**For Neon PostgreSQL:**
```
1. Go to: https://console.neon.tech
2. Select your database
3. Click "SQL Editor"
4. Run SQL commands directly
```

**SQL to create admin user:**
```sql
-- Create admin user
INSERT INTO users (
    username, 
    email, 
    hashed_password, 
    full_name, 
    role, 
    is_active, 
    is_verified,
    department,
    designation
) VALUES (
    'admin',
    'admin@delhipolice.gov.in',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg7Iq', -- Admin@123456
    'System Administrator',
    'admin',
    true,
    true,
    'Delhi Police Cyber Cell',
    'System Administrator'
);
```

---

### **Option 2: Use API Endpoint**

**Create a temporary endpoint:**

Add to `backend/routers/auth_secure.py`:
```python
@router.post("/setup-admin")
async def setup_admin(secret: str, db: Session = Depends(get_db)):
    # Only allow if secret matches
    if secret != "YOUR_SECRET_SETUP_KEY":
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    # Check if admin exists
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        return {"message": "Admin already exists"}
    
    # Create admin
    admin, message = AuthService.create_user(
        db=db,
        username="admin",
        email="admin@delhipolice.gov.in",
        password="Admin@123456",
        full_name="System Administrator",
        role="admin"
    )
    
    if admin:
        admin.is_verified = True
        admin.is_active = True
        db.commit()
        return {"message": "Admin created successfully"}
    
    raise HTTPException(status_code=500, detail=message)
```

**Then call it:**
```bash
curl -X POST https://your-domain.com/api/auth/setup-admin \
  -H "Content-Type: application/json" \
  -d '{"secret": "YOUR_SECRET_SETUP_KEY"}'
```

---

### **Option 3: Use Environment Variables**

**Set in hosting platform:**
```
INIT_ADMIN=true
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin@123456
```

**Add to backend startup:**
```python
# In main.py
@app.on_event("startup")
async def startup_event():
    if os.getenv("INIT_ADMIN") == "true":
        db = SessionLocal()
        # Create admin user
        # ... (same logic as init_database.py)
        db.close()
```

---

## 📝 **RECOMMENDED APPROACH:**

### **For Serverless (Vercel/Netlify):**
1. Use Neon SQL Editor to create admin user
2. Or use temporary API endpoint
3. Or use environment-based initialization

### **For Server-based (Railway/Render/Heroku):**
1. Use built-in shell/terminal
2. Run `python init_database.py`
3. Much easier and cleaner

### **For VPS (DigitalOcean/AWS):**
1. Use SSH access
2. Full control
3. Best option

---

## 🎯 **QUICK QUESTIONS TO IDENTIFY YOUR SETUP:**

**Answer these to know your hosting:**

1. **Where did you deploy?**
   - GitHub Pages? → Static only, need backend elsewhere
   - Vercel? → Serverless, use Neon SQL Editor
   - Railway? → Use Railway shell
   - Own server? → Use SSH

2. **What's your backend URL?**
   - `*.vercel.app` → Vercel
   - `*.railway.app` → Railway
   - `*.onrender.com` → Render
   - `*.herokuapp.com` → Heroku
   - Custom domain → Check DNS

3. **Where's your database?**
   - Neon → Use SQL Editor
   - Supabase → Use Dashboard
   - Railway → Use Railway shell
   - Own PostgreSQL → Use SSH

---

## 🚀 **EASIEST SOLUTION (NO SSH NEEDED):**

### **Use Neon SQL Editor:**

```
1. Go to: https://console.neon.tech
2. Login to your account
3. Select your database
4. Click "SQL Editor"
5. Paste this SQL:
```

```sql
-- Create admin user (password: Admin@123456)
INSERT INTO users (
    username, email, hashed_password, full_name, role, 
    is_active, is_verified, department, designation,
    created_at, updated_at
) VALUES (
    'admin',
    'admin@delhipolice.gov.in',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg7Iq',
    'System Administrator',
    'admin',
    true,
    true,
    'Delhi Police Cyber Cell',
    'System Administrator',
    NOW(),
    NOW()
) ON CONFLICT (username) DO NOTHING;
```

```
6. Click "Run"
7. ✅ Admin user created!
8. Test login: admin / Admin@123456
```

---

## 📊 **SUMMARY:**

**Tell me:**
1. Where did you deploy your site?
2. What's your website URL?
3. Where's your database hosted?

**Then I can give you exact steps!** 🎯

---

**EASIEST: USE NEON SQL EDITOR TO CREATE ADMIN USER!** ✅

No SSH needed! 🚀
