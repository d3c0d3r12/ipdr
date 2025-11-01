# 🔒 User Tracking System - Setup Guide

## Overview

This system automatically tracks all user visits, activities, and sessions with detailed information including:

- **IP Address & Geolocation** (Country, City, ISP)
- **Device Details** (Type, Browser, OS, Screen Resolution)
- **Session Duration** (Start time, End time, Total duration)
- **User Activities** (Page views, Clicks, Uploads, Downloads)
- **Network Information** (Connection type, Speed)
- **Security Details** (Incognito mode, Do Not Track)

---

## 📊 What Gets Tracked

### 1. **Session Information**
- Unique session ID
- IP address with geolocation
- Entry and exit pages
- Session duration
- Last activity timestamp

### 2. **Device & Browser**
- Device type (Desktop, Mobile, Tablet)
- Browser name and version
- Operating system
- Screen resolution
- Viewport size
- Color depth

### 3. **User Activities**
- Page views
- Button clicks
- Form submissions
- File uploads/downloads
- Search queries
- Login/logout events

### 4. **Network Details**
- Connection type (WiFi, Cellular, Ethernet)
- Effective connection speed (4G, 3G, etc.)
- Download speed
- Round-trip time (RTT)

### 5. **Privacy Settings**
- Cookies enabled/disabled
- Do Not Track preference
- Incognito mode detection
- JavaScript enabled

---

## 🚀 Installation Steps

### **Step 1: Install Required Python Packages**

```bash
cd backend
pip install user-agents httpx
```

### **Step 2: Create Database Tables**

Run the SQL schema to create tracking tables:

```bash
# Using psql
psql -h your-neon-host -U your-user -d your-database -f database/user_tracking_schema.sql

# Or using Python
python -c "from core.db import engine; from models.user_session import Base; Base.metadata.create_all(engine)"
```

This creates 3 tables:
- `user_sessions` - Main session tracking
- `user_activities` - Activity logs
- `page_views` - Page navigation tracking

### **Step 3: Backend is Already Configured**

The tracking router is already added to `main.py`:
```python
app.include_router(tracking.router, prefix="/api/tracking", tags=["User Tracking"])
```

### **Step 4: Initialize Tracking in Frontend**

Add to your main app layout or `app.vue`:

```vue
<script setup>
import { useTracking } from '~/composables/useTracking'
import { onMounted } from 'vue'

const { initTracking } = useTracking()

onMounted(() => {
  // Start tracking for anonymous users
  initTracking()
  
  // Or for authenticated users:
  // initTracking('username', 'role', true)
})
</script>
```

---

## 📝 Usage Examples

### **1. Track User Login**

```typescript
import { useTracking } from '~/composables/useTracking'

const { updateSessionUser, logActivity } = useTracking()

// After successful login
await updateSessionUser('john_doe', 'inspector')
await logActivity('login', 'User logged in successfully')
```

### **2. Track File Upload**

```typescript
const { logActivity } = useTracking()

// When user uploads a file
await logActivity(
  'upload',
  'Uploaded FIR document',
  {
    filename: 'evidence.html',
    filesize: 1024000,
    fir_number: 'FIR/2025/1234'
  },
  'success'
)
```

### **3. Track Search/Filter**

```typescript
await logActivity(
  'search',
  'Searched for IP records',
  {
    query: '192.168.1.1',
    filters: { country: 'India', date_range: '2025-01-01' }
  }
)
```

### **4. Track Download**

```typescript
await logActivity(
  'download',
  'Downloaded Excel report',
  {
    filename: 'ip_report.xlsx',
    record_count: 500
  }
)
```

### **5. Track Errors**

```typescript
await logActivity(
  'error',
  'Failed to process file',
  {
    error_code: 'INVALID_FORMAT',
    error_message: 'File format not supported'
  },
  'error'
)
```

---

## 🎯 Automatic Tracking

The following are tracked **automatically** without any code:

✅ **Page Views** - Every page navigation  
✅ **Button Clicks** - All button interactions  
✅ **Link Clicks** - All link navigations  
✅ **Form Submissions** - All form submits  
✅ **Session Start** - When user enters site  
✅ **Session End** - When user leaves site  
✅ **Page Visibility** - Tab switching  
✅ **Activity Heartbeat** - Every 30 seconds  

---

## 📊 Admin Dashboard

### **Access the Dashboard**

Navigate to: `/admin/sessions`

### **Features:**

1. **Session Statistics**
   - Total sessions
   - Unique visitors
   - Authenticated users
   - Average duration

2. **Active Sessions**
   - Real-time list of online users
   - IP addresses
   - Locations
   - Device types
   - Last activity

3. **Device Breakdown**
   - Desktop vs Mobile vs Tablet
   - Percentage distribution

4. **Top Countries**
   - Geographic distribution
   - Visit counts

5. **Recent Activities**
   - Latest 20 user actions
   - Activity types
   - Timestamps

### **Auto-Refresh**

Dashboard auto-refreshes every 30 seconds to show real-time data.

---

## 🔍 API Endpoints

### **Session Management**

```bash
# Start a new session
POST /api/tracking/session/start
Body: {
  "username": "john_doe",
  "user_role": "inspector",
  "is_authenticated": true,
  "user_agent": "Mozilla/5.0...",
  "screen_resolution": "1920x1080",
  ...
}

# End a session
POST /api/tracking/session/end
Body: {
  "session_id": "uuid-here",
  "exit_page": "/dashboard"
}
```

### **Activity Logging**

```bash
# Log an activity
POST /api/tracking/activity/log
Body: {
  "session_id": "uuid-here",
  "activity_type": "upload",
  "activity_description": "Uploaded file",
  "action_data": { "filename": "test.html" },
  "status": "success"
}

# Log a page view
POST /api/tracking/pageview/log
Body: {
  "session_id": "uuid-here",
  "page_url": "/dashboard",
  "page_title": "Dashboard",
  "previous_page": "/login"
}
```

### **Analytics**

```bash
# Get active sessions
GET /api/tracking/sessions/active

# Get session statistics
GET /api/tracking/sessions/stats?days=7

# Get recent activities
GET /api/tracking/activities/recent?limit=50
```

---

## 🔒 Privacy & Security

### **Data Protection**

1. **IP Anonymization** (Optional)
   - Can hash IP addresses
   - Store only first 3 octets

2. **GDPR Compliance**
   - Respect Do Not Track
   - Allow data deletion
   - Provide data export

3. **Data Retention**
   - Set retention period (e.g., 90 days)
   - Auto-delete old sessions
   - Archive important data

### **Security Measures**

1. **Access Control**
   - Admin-only dashboard
   - JWT authentication required
   - Role-based permissions

2. **Data Encryption**
   - HTTPS for all requests
   - Encrypted database storage
   - Secure session IDs

3. **Rate Limiting**
   - Prevent tracking abuse
   - Limit API calls
   - Throttle requests

---

## 📈 Database Queries

### **Find sessions by IP**

```sql
SELECT * FROM user_sessions 
WHERE ip_address = '192.168.1.1'
ORDER BY session_start DESC;
```

### **Get user activity history**

```sql
SELECT 
  s.username,
  s.ip_address,
  a.activity_type,
  a.activity_description,
  a.timestamp
FROM user_sessions s
JOIN user_activities a ON s.session_id = a.session_id
WHERE s.username = 'john_doe'
ORDER BY a.timestamp DESC;
```

### **Most active users**

```sql
SELECT 
  username,
  COUNT(DISTINCT session_id) as session_count,
  COUNT(a.id) as activity_count,
  SUM(session_duration) as total_time
FROM user_sessions s
LEFT JOIN user_activities a ON s.session_id = a.session_id
WHERE username IS NOT NULL
GROUP BY username
ORDER BY activity_count DESC
LIMIT 10;
```

### **Sessions by country**

```sql
SELECT 
  country,
  COUNT(*) as session_count,
  COUNT(DISTINCT ip_address) as unique_ips
FROM user_sessions
WHERE session_start >= NOW() - INTERVAL '7 days'
GROUP BY country
ORDER BY session_count DESC;
```

---

## 🎯 Use Cases

### **1. Security Monitoring**
- Detect suspicious activity
- Track unauthorized access
- Monitor failed login attempts
- Identify unusual patterns

### **2. User Analytics**
- Understand user behavior
- Track feature usage
- Measure engagement
- Optimize user experience

### **3. Compliance & Auditing**
- Maintain access logs
- Track data access
- Generate audit reports
- Prove compliance

### **4. Performance Monitoring**
- Track page load times
- Monitor user interactions
- Identify bottlenecks
- Measure response times

---

## 🔧 Configuration

### **Environment Variables**

Add to `.env`:

```env
# Tracking Configuration
TRACKING_ENABLED=true
TRACKING_IP_ANONYMIZE=false
TRACKING_RETENTION_DAYS=90
TRACKING_GEOLOCATION_API=http://ip-api.com/json/
```

### **Disable Tracking**

To disable tracking for specific pages:

```typescript
// In your page component
definePageMeta({
  tracking: false
})
```

---

## 📊 Reports & Analytics

### **Generate Session Report**

```python
from models.user_session import UserSession
from sqlalchemy import func
from datetime import datetime, timedelta

# Last 30 days report
cutoff = datetime.utcnow() - timedelta(days=30)

report = db.query(
    func.date(UserSession.session_start).label('date'),
    func.count(UserSession.id).label('sessions'),
    func.count(func.distinct(UserSession.ip_address)).label('unique_visitors'),
    func.avg(UserSession.session_duration).label('avg_duration')
).filter(
    UserSession.session_start >= cutoff
).group_by(
    func.date(UserSession.session_start)
).all()
```

---

## 🎉 Benefits

### **For Administrators:**
- 👁️ **Real-time visibility** into user activity
- 🔒 **Security monitoring** and threat detection
- 📊 **Usage analytics** and insights
- 📝 **Audit trail** for compliance

### **For Users:**
- 🚀 **Better experience** through optimization
- 🔒 **Enhanced security** through monitoring
- 📱 **Device-optimized** interface
- ⚡ **Faster performance** through insights

---

## 🆘 Troubleshooting

### **Sessions not being tracked**

1. Check if tracking is initialized in `app.vue`
2. Verify API endpoint is accessible
3. Check browser console for errors
4. Ensure database tables exist

### **Geolocation not working**

1. Check IP-API service is accessible
2. Verify internet connection
3. Try alternative geolocation service
4. Check rate limits

### **Admin dashboard not loading**

1. Verify user has admin role
2. Check API endpoints are working
3. Ensure database connection
4. Check browser console

---

## 📚 Additional Resources

- **Database Schema**: `database/user_tracking_schema.sql`
- **Backend Models**: `models/user_session.py`
- **API Router**: `routers/tracking.py`
- **Frontend Composable**: `composables/useTracking.ts`
- **Admin Dashboard**: `pages/admin/sessions.vue`

---

**🎉 User tracking is now fully implemented and ready to use!**

All user visits, activities, and sessions will be automatically tracked and stored in the database for analysis and security monitoring.
