# 🔍 **TROUBLESHOOTING - Let's Fix This Step by Step**

## 🐛 **What's Not Working?**

Please tell me **exactly** what you're seeing:

### **Question 1: Where does it fail?**

- [ ] A. Upload page doesn't show the button
- [ ] B. Button appears but redirect doesn't work
- [ ] C. Redirects but terminal page shows error
- [ ] D. Terminal page loads but doesn't start
- [ ] E. Something else (describe below)

### **Question 2: What do you see after upload?**

After clicking "Upload & Extract", do you see:

- [ ] A. Success message with green box
- [ ] B. "Start Unlimited IP Lookup" button
- [ ] C. "Redirecting to IP Lookup..." message
- [ ] D. Nothing happens
- [ ] E. Error message (what does it say?)

### **Question 3: Browser Console Errors?**

Open browser console (F12) and check for errors:

```
Right-click → Inspect → Console tab
```

Copy any red error messages here:
```
[Paste errors here]
```

---

## 🔧 **Quick Tests:**

### **Test 1: Check if backend is running**

Open in browser:
```
http://localhost:8000/docs
```

Do you see the API documentation? 
- [ ] Yes - API is working
- [ ] No - Backend is not running

### **Test 2: Check if IP lookup endpoint exists**

In the API docs, look for:
```
GET /api/lookup/stream
GET /api/lookup/status
POST /api/lookup/start
```

Do you see these endpoints?
- [ ] Yes - Endpoints exist
- [ ] No - Endpoints missing (need to restart backend)

### **Test 3: Manual navigation test**

Try going directly to:
```
http://localhost:3000/ip-lookup
```

What happens?
- [ ] A. Page loads with directory input
- [ ] B. Page shows error
- [ ] C. Page not found (404)
- [ ] D. Blank page

### **Test 4: Test with manual path**

If the page loads, try entering this path manually:
```
backend/processed/20251102_104516_205
```

Then click "Load Directory". What happens?
- [ ] A. Shows "Loaded X IPs"
- [ ] B. Shows error message
- [ ] C. Nothing happens

---

## 🚀 **Quick Fix Steps:**

### **Fix 1: Restart Backend**

```bash
cd backend
python -m uvicorn main:app --reload
```

Look for this line in output:
```
INFO:     Application startup complete.
```

### **Fix 2: Restart Frontend**

```bash
cd frontend
npm run dev
```

Look for:
```
✓ Vite server running at http://localhost:3000
```

### **Fix 3: Clear Browser Cache**

```
Ctrl + Shift + Delete
→ Clear cached images and files
→ Clear for "All time"
→ Click "Clear data"
```

Then refresh the page (Ctrl + F5)

---

## 📋 **Detailed Debugging:**

### **Check 1: Is the route registered?**

Run this in backend directory:
```bash
python -c "from main import app; print([r.path for r in app.routes if 'lookup' in r.path])"
```

Should show:
```
['/api/lookup/stream', '/api/lookup/start', '/api/lookup/status']
```

### **Check 2: Is the page file present?**

Check if this file exists:
```
frontend/pages/ip-lookup.vue
```

### **Check 3: Is the component present?**

Check if this file exists:
```
frontend/components/IPLookupTerminal.vue
```

---

## 🔍 **Common Issues:**

### **Issue 1: "navigateTo is not defined"**

**Symptom:** Button click does nothing, console shows error

**Fix:** Update `upload.vue`:
```vue
// Change this:
navigateTo(`/ip-lookup?...`)

// To this:
window.location.href = `/ip-lookup?...`
```

### **Issue 2: "Page not found"**

**Symptom:** Redirects to 404 page

**Fix:** Check if `frontend/pages/ip-lookup.vue` exists

### **Issue 3: "API endpoint not found"**

**Symptom:** Terminal loads but shows connection error

**Fix:** Restart backend server

### **Issue 4: "EventSource failed"**

**Symptom:** Terminal shows "Connection error"

**Fix:** Check CORS settings in backend

---

## 🎯 **Let's Debug Together:**

Please answer these questions:

1. **What's your current URL after upload?**
   ```
   Example: http://localhost:3000/upload
   ```

2. **Do you see the green success box?**
   - [ ] Yes
   - [ ] No

3. **Do you see the "Start Unlimited IP Lookup" button?**
   - [ ] Yes
   - [ ] No

4. **When you click the button, what happens?**
   ```
   [Describe what you see]
   ```

5. **Are there any errors in browser console?**
   ```
   [Copy errors here]
   ```

6. **Is your backend running on port 8000?**
   - [ ] Yes
   - [ ] No (what port?)

7. **Is your frontend running on port 3000?**
   - [ ] Yes
   - [ ] No (what port?)

---

## 🔥 **Emergency Simple Fix:**

If nothing works, let's try the simplest approach:

### **Option A: Direct Link**

After upload shows success, manually go to:
```
http://localhost:3000/ip-lookup?run_dir=backend/processed/20251102_104516_205&auto_start=true
```

Replace `20251102_104516_205` with your actual run directory.

### **Option B: Use the standalone script**

```bash
cd "c:\Users\saheb\Downloads\New FIR"
python direct_ip_lookup.py
```

Then when it asks for file path, enter:
```
backend/processed/20251102_104516_205/original_log.csv
```

---

## 📸 **Screenshots Needed:**

Can you send screenshots of:

1. **Upload page after success** (showing the green box)
2. **Browser console** (F12 → Console tab)
3. **Network tab** (F12 → Network tab, after clicking button)
4. **Backend terminal** (showing the running server)

---

## 🆘 **Quick Contact:**

Tell me:
1. What exactly happens when you click "Upload & Extract"?
2. Do you see any button after success?
3. What's in the browser console (F12)?
4. Is the backend running and showing logs?

Once I know where it's failing, I can give you the exact fix! 🎯
