# 👥 **USER REGISTRATION GUIDE**

## ✅ **NEW FEATURE: User Signup/Registration**

I've created a complete user registration system for your IPDR Tracking Hub!

---

## 🎯 **HOW TO REGISTER NEW USERS:**

### **Method 1: Via Web Interface (Recommended)**

1. **Go to Login Page:**
   ```
   http://localhost:3000/login
   ```

2. **Click "Register Here" Link:**
   - At the bottom of login form
   - Or directly go to: `http://localhost:3000/signup`

3. **Fill Registration Form:**
   - **Username** - Badge number or unique ID
   - **Email** - Official email address
   - **Full Name** - Officer's full name
   - **Badge Number** - Official badge number
   - **Department** - Select from dropdown:
     - Cyber Cell
     - Crime Branch
     - Special Cell
     - Intelligence
     - Forensics
     - Other
   - **Role** - Select from dropdown:
     - Officer
     - Investigator
     - Analyst
     - Admin
   - **Password** - Must meet requirements
   - **Confirm Password** - Re-enter password

4. **Password Requirements:**
   - ✓ At least 8 characters
   - ✓ One uppercase letter
   - ✓ One lowercase letter
   - ✓ One number
   - ✓ One special character (!@#$%^&*(),.?":{}|<>)

5. **Submit:**
   - Click "CREATE ACCOUNT"
   - Wait for success message
   - Auto-redirected to login page

---

## 📋 **REGISTRATION FORM FIELDS:**

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| Username | ✅ Yes | Unique identifier | `officer_123` |
| Email | ✅ Yes | Official email | `officer@delhipolice.gov.in` |
| Full Name | ✅ Yes | Complete name | `Inspector Rajesh Kumar` |
| Badge Number | ❌ No | Badge/ID number | `DCP/CC/2025/001` |
| Department | ✅ Yes | Department name | `Cyber Cell` |
| Role | ✅ Yes | User role | `Investigator` |
| Password | ✅ Yes | Strong password | `Admin@123456` |
| Confirm Password | ✅ Yes | Match password | `Admin@123456` |

---

## 🔐 **PASSWORD SECURITY:**

The system enforces strong passwords:

**Valid Password Example:**
```
Admin@123456
```

**Why it's valid:**
- ✓ 12 characters (>8)
- ✓ Has uppercase: A
- ✓ Has lowercase: dmin
- ✓ Has number: 123456
- ✓ Has special: @

**Invalid Password Examples:**
```
admin123      ❌ No uppercase, no special char
ADMIN123      ❌ No lowercase, no special char
Admin@        ❌ Too short (< 8 chars)
AdminTest     ❌ No number, no special char
```

---

## 🎨 **SIGNUP PAGE FEATURES:**

- ✅ CyberForensics dark theme
- ✅ Animated background
- ✅ Real-time password validation
- ✅ Visual feedback for requirements
- ✅ Form validation
- ✅ Error/Success messages
- ✅ Auto-redirect after signup
- ✅ Link back to login

---

## 🚀 **COMPLETE REGISTRATION FLOW:**

```
1. Visit http://localhost:3000
   ↓
2. Redirected to /login
   ↓
3. Click "Register Here"
   ↓
4. Fill signup form
   ↓
5. Password validation (real-time)
   ↓
6. Submit form
   ↓
7. Account created
   ↓
8. Auto-redirect to /login
   ↓
9. Login with new credentials
   ↓
10. Access dashboard
```

---

## 💻 **API ENDPOINT:**

The signup page calls:
```
POST http://localhost:8000/api/auth/signup

Body:
{
  "username": "officer_123",
  "email": "officer@delhipolice.gov.in",
  "password": "Admin@123456",
  "full_name": "Inspector Rajesh Kumar",
  "badge_number": "DCP/CC/2025/001",
  "department": "Cyber Cell",
  "role": "investigator"
}

Response:
{
  "message": "User created successfully",
  "user_id": 2,
  "username": "officer_123"
}
```

---

## 🎯 **USER ROLES:**

| Role | Permissions | Description |
|------|-------------|-------------|
| **Admin** | Full access | System administrators |
| **Investigator** | Create/View FIRs | Lead investigators |
| **Analyst** | View/Analyze data | Data analysts |
| **Officer** | Basic access | Field officers |

---

## 📝 **EXAMPLE REGISTRATION:**

**Scenario:** Register a new Cyber Cell investigator

1. **Go to:** http://localhost:3000/signup

2. **Fill Form:**
   ```
   Username: investigator_raj
   Email: raj.kumar@delhipolice.gov.in
   Full Name: Inspector Raj Kumar
   Badge Number: DCP/CC/2025/002
   Department: Cyber Cell
   Role: Investigator
   Password: Secure@2025
   Confirm Password: Secure@2025
   ```

3. **Click:** CREATE ACCOUNT

4. **Result:**
   ```
   ✅ Account created successfully! Redirecting to login...
   ```

5. **Login:**
   ```
   Username: investigator_raj
   Password: Secure@2025
   ```

6. **Access:** Full dashboard and FIR management

---

## 🔧 **TESTING:**

### **Test 1: Valid Registration**
```
Username: test_officer
Email: test@delhipolice.gov.in
Full Name: Test Officer
Department: Cyber Cell
Role: Officer
Password: Test@123456
Confirm: Test@123456

Expected: ✅ Success
```

### **Test 2: Weak Password**
```
Password: test123

Expected: ❌ Error - Password does not meet requirements
```

### **Test 3: Password Mismatch**
```
Password: Test@123456
Confirm: Test@123457

Expected: ❌ Error - Passwords do not match
```

### **Test 4: Duplicate Username**
```
Username: admin (already exists)

Expected: ❌ Error - Username already exists
```

---

## 🎨 **UI SCREENSHOTS:**

### **Signup Page:**
- Dark CyberForensics theme
- Animated grid background
- Two-column form layout
- Real-time password validation
- Visual requirement checklist
- Success/Error notifications

### **Password Requirements:**
Shows live validation:
- ✓ At least 8 characters (Green when valid)
- ✓ One uppercase letter (Green when valid)
- ✓ One lowercase letter (Green when valid)
- ✓ One number (Green when valid)
- ✓ One special character (Green when valid)

---

## 📱 **RESPONSIVE DESIGN:**

The signup page is fully responsive:
- **Desktop:** Two-column form
- **Tablet:** Two-column form
- **Mobile:** Single-column form

---

## 🔗 **NAVIGATION:**

### **From Login to Signup:**
```
Login Page → "Register Here" link → Signup Page
```

### **From Signup to Login:**
```
Signup Page → "Login Here" link → Login Page
```

### **After Signup:**
```
Signup Success → Auto-redirect (2 seconds) → Login Page
```

---

## ✅ **WHAT'S INCLUDED:**

1. **Signup Page** (`/signup`)
   - Complete registration form
   - Password validation
   - Department/Role selection
   - Success/Error handling

2. **Login Page Updated** (`/login`)
   - Added "Register Here" link
   - Styled to match theme

3. **Backend API** (Already exists)
   - `/api/auth/signup` endpoint
   - Password hashing
   - Email validation
   - Duplicate checking

---

## 🚀 **QUICK START:**

### **1. Restart Frontend:**
```bash
cd frontend
npm run dev
```

### **2. Test Registration:**
1. Go to: http://localhost:3000/signup
2. Fill the form
3. Create account
4. Login with new credentials

---

## 📊 **ADMIN FEATURES:**

As an admin, you can:
- View all registered users (future feature)
- Manage user permissions (future feature)
- Approve/Reject registrations (future feature)
- Deactivate users (future feature)

---

## 🎯 **BEST PRACTICES:**

1. **Use Official Emails:**
   - `@delhipolice.gov.in`
   - `@police.delhi.gov.in`

2. **Strong Passwords:**
   - Mix of characters
   - At least 12 characters
   - Unique per user

3. **Proper Roles:**
   - Assign based on job function
   - Review periodically

4. **Badge Numbers:**
   - Use official badge numbers
   - Keep records updated

---

## 🔐 **SECURITY NOTES:**

- ✅ Passwords are hashed (PBKDF2 + SHA256)
- ✅ Email validation
- ✅ Username uniqueness check
- ✅ Strong password enforcement
- ✅ All registrations logged
- ✅ Account lockout after failed attempts

---

## 📞 **SUPPORT:**

If you encounter issues:
1. Check password meets requirements
2. Ensure email is valid
3. Verify username is unique
4. Check backend is running
5. Review browser console for errors

---

## 🎉 **SUMMARY:**

**You can now register new users via:**

1. **Web Interface:** http://localhost:3000/signup
2. **From Login Page:** Click "Register Here"
3. **Direct API:** POST to `/api/auth/signup`

**All users can:**
- Self-register
- Choose their role
- Set strong passwords
- Login immediately after registration

---

**START REGISTERING USERS NOW!** 🚀

Go to: **http://localhost:3000/signup**
