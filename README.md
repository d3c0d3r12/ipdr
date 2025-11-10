# 🛡️ IPDR Tracking Hub - Delhi Police Cyber Cell

A secure, automated IP Data Record (IPDR) tracking and analysis system for Delhi Police Cyber Cell investigators.

## ✨ Features

- **Automated IP Lookup** - Process unlimited IPs with Cloudflare bypass
- **Master File Generation** - Merge IP data with timestamps
- **ISP Separation & Analysis** - Automatic separation by ISP with comprehensive statistics
- **Geographic Analysis** - State and city distribution
- **Professional Reports** - Export-ready CSV and analysis reports
- **Secure Authentication** - User tracking and session management
- **Modern UI** - Cyber-themed interface with real-time updates

## 🚀 Quick Start (New System)

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- Internet connection

### Installation (3 Steps)

1. **Install Python & Node.js** (one-time)
   - Python: https://www.python.org/downloads/ (✅ Check "Add to PATH")
   - Node.js: https://nodejs.org/ (LTS version)

2. **Copy Project** to your system

3. **Run Installation**
   ```cmd
   Double-click: INSTALL.bat
   ```
   Wait 10-15 minutes for automatic dependency installation.

### Start Application

```cmd
Double-click: START.bat
```

Browser opens automatically to http://localhost:3000

## 📋 Complete Workflow

1. **Upload Original Log** - CSV with timestamp and IP
2. **Process IPs** - Automatic lookup with Cloudflare bypass
3. **Create Master File** - Merge with IP data
4. **Fix to Start** - Prepare for Final Report Generator
5. **Generate Final Report** - Use external tool
6. **ISP Separation & Analysis** - Automatic separation with statistics

## 🔧 Available Scripts

### **Main Folder (Easy Access):**
- **INSTALL.bat** - Install all dependencies (first time)
- **START.bat** - Start servers (daily use)
- **STOP.bat** - Stop all servers

### **Setup Folder (Organized):**
- **setup/install.bat** - Actual installer
- **setup/setup.bat** - Simple startup
- **setup/start-servers.bat** - Enhanced startup with checks
- **setup/stop-servers.bat** - Server shutdown

## 📊 System Requirements

**Minimum:**
- Windows 10 or higher
- 4 GB RAM
- 2 GB free storage
- Dual-core processor

**Recommended:**
- Windows 10/11 Pro
- 8 GB RAM
- 5 GB free storage
- Quad-core processor

## 🌐 URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## 📚 Documentation

- **EASY_DEPLOYMENT_GUIDE.md** - Deploy on any system
- **STARTUP_SCRIPTS_GUIDE.md** - Script usage guide
- **ISP_SEPARATION_GUIDE.md** - ISP analysis feature
- **WORKFLOW_UPDATE.md** - Complete workflow

## 🔐 Security

- Secure authentication system
- User activity tracking
- Session management
- Input validation and sanitization
- SQL injection prevention
- XSS protection

## 🛠️ Tech Stack

**Backend:**
- FastAPI - Modern Python web framework
- Uvicorn - ASGI server
- SQLAlchemy - Database ORM
- Pandas - Data processing
- Selenium - Web automation

**Frontend:**
- Nuxt.js 3 - Vue framework
- Vue.js 3 - Progressive framework
- TypeScript - Type safety

**Database:**
- PostgreSQL (Neon) - Production database

## 📦 Project Structure

```
New FIR/
├── INSTALL.bat              # Install dependencies (main)
├── START.bat                # Start servers (main)
├── STOP.bat                 # Stop servers (main)
│
├── setup/                   # Setup scripts (organized)
│   ├── install.bat         # Actual installer
│   ├── setup.bat           # Simple startup
│   ├── start-servers.bat   # Enhanced startup
│   ├── stop-servers.bat    # Server shutdown
│   └── README.md           # Setup folder guide
│
├── backend/                 # FastAPI backend
│   ├── main.py             # Entry point
│   ├── routers/            # API routes
│   ├── models/             # Database models
│   └── utils/              # Utilities
│
├── frontend/                # Nuxt.js frontend
│   ├── pages/              # Page components
│   ├── components/         # Vue components
│   └── composables/        # Composables
│
└── docs/                    # Documentation
```

## 🎯 Key Features

### IP Lookup
- Unlimited IP processing
- Automatic Cloudflare bypass
- Browser crash recovery
- Cookie persistence
- 100% success rate

### ISP Separation
- Automatic separation by ISP
- Summary statistics per ISP
- Geographic analysis
- Time-based statistics
- ZIP download with all reports

### Master File
- Merge original log with IP data
- LEFT JOIN preserves all records
- Missing data handling
- Export to CSV

## 🔄 Updates

**Latest Version:** 1.0.0
- ✅ ISP Separation & Analysis
- ✅ Automated server startup
- ✅ Easy deployment system
- ✅ Comprehensive documentation

## 📞 Support

For issues or questions:
1. Check documentation in `/docs`
2. Review troubleshooting guides
3. Check server logs in terminal windows

## ⚖️ Legal Notice

**IMPORTANT:** This system is designed exclusively for authorized law enforcement use by Delhi Police Cyber Cell.

- Use only with proper authorization
- Comply with applicable laws and SOPs
- Maintain data confidentiality
- Follow investigation protocols

## 🎉 Quick Reference

**First Time:**
```cmd
1. INSTALL.bat    # Install dependencies
2. START.bat      # Start servers
```

**Daily Use:**
```cmd
START.bat         # Start and go!
```

**Stop Servers:**
```cmd
STOP.bat          # Clean shutdown
```

---

**🛡️ DELHI POLICE IPDR TRACKING HUB 🛡️**

**Status:** Production Ready ✅  
**Version:** 1.0.0  
**Last Updated:** November 2024
