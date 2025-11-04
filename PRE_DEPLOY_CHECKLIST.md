# ✅ Pre-Deployment Security Checklist

Before pushing to GitHub and deploying, verify these:

## 🔍 Step 1: Check What Will Be Committed

```powershell
cd "C:\Users\saheb\Downloads\New FIR"
git status
```

**What you should see:**
- ✅ Source code files (`.py`, `.vue`, `.ts`)
- ✅ Configuration templates (`.env.example`)
- ✅ Documentation (`.md` files)
- ✅ `.gitignore`

**What you should NOT see:**
- ❌ `.env` files
- ❌ `venv/` or `node_modules/`
- ❌ Database files (`.db`, `.sqlite`)
- ❌ Real connection strings

---

## 🔍 Step 2: Search for Secrets

```powershell
# Search for common secret patterns
git diff --cached | findstr /i "password secret token key"
```

**Should return:** Nothing (or only in `.env.example` with placeholders)

---

## 🔍 Step 3: Verify .gitignore

```powershell
# Check .gitignore exists and has correct entries
type .gitignore | findstr ".env"
```

**Should show:** `.env` is listed (meaning it's ignored)

---

## 🔍 Step 4: Test Local Ignore

```powershell
# Try to add .env (should fail or be ignored)
git add .env
git status
```

**Should show:** `.env` is NOT in the staged files

---

## 🔍 Step 5: Review Sensitive Files

Check these files contain **placeholders only**:

- ✅ `.env.example` - Has `USERNAME`, `PASSWORD`, `CHANGE_THIS`
- ✅ `backend/ENV_EXAMPLE.txt` - Has placeholder values
- ✅ All code files - No hardcoded secrets

---

## ✅ Ready to Push Checklist

- [ ] `.gitignore` exists and includes `.env`
- [ ] `.env` file is NOT tracked by git
- [ ] All `.env.example` files have placeholders only
- [ ] No hardcoded secrets in code files
- [ ] `venv/` and `node_modules/` are ignored
- [ ] Database files are ignored

---

## 🚀 Safe Push Command

```powershell
# Review what you're about to commit
git status

# Add only safe files
git add .

# Review changes one more time
git diff --cached

# If everything looks good:
git commit -m "Initial deployment-ready code"
git push origin main
```

---

## 🛡️ After Pushing

1. **Visit your GitHub repo**
2. **Browse files** - ensure no `.env` or secrets visible
3. **Search repository** for `DATABASE_URL`, `JWT_SECRET`
4. **Should only find:** Templates and examples ✅

---

**If you see secrets on GitHub → STOP → Follow `SECURITY_GUIDE.md` → Rotate secrets immediately!**


