# 🐘 PHP Backend for Police Intelligence System

## Overview

This is a **PHP alternative backend** for the Police Intelligence System. It provides the same functionality as the Python FastAPI backend but uses PHP with PostgreSQL.

---

## 📁 Project Structure

```
backend-php/
├── index.php                    # Main entry point & router
├── .htaccess                    # Apache rewrite rules
│
├── config/
│   ├── database.php            # Database connection (PDO)
│   └── config.php              # App configuration
│
├── controllers/
│   ├── AuthController.php      # JWT authentication
│   ├── UploadController.php    # File upload handling
│   ├── DataController.php      # Data retrieval
│   └── ProcessController.php   # Data processing
│
├── models/
│   └── IPRecord.php            # IP record model (ORM-like)
│
├── utils/
│   └── HTMLParser.php          # HTML parsing utility
│
├── uploads/                    # Uploaded files
├── processed/                  # Processing folders
└── logs/                       # Application logs
```

---

## 🚀 Requirements

- **PHP 8.0+** (with PDO PostgreSQL extension)
- **PostgreSQL 16**
- **Apache/Nginx** web server
- **Composer** (optional, for dependencies)

---

## ⚙️ Installation

### Step 1: Install PHP Extensions

```bash
# Ubuntu/Debian
sudo apt install php8.1 php8.1-pgsql php8.1-mbstring php8.1-xml php8.1-curl

# Windows (enable in php.ini)
extension=pdo_pgsql
extension=mbstring
extension=dom
```

### Step 2: Configure Database

Edit `config/database.php` or set environment variables:

```php
DB_HOST=localhost
DB_NAME=police_data
DB_USER=police_user
DB_PASS=StrongPass
```

### Step 3: Setup Web Server

#### **Apache**

```apache
<VirtualHost *:80>
    ServerName localhost
    DocumentRoot "C:/Users/saheb/Downloads/New FIR/backend-php"
    
    <Directory "C:/Users/saheb/Downloads/New FIR/backend-php">
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
```

#### **Nginx**

```nginx
server {
    listen 80;
    server_name localhost;
    root /path/to/backend-php;
    index index.php;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        fastcgi_pass 127.0.0.1:9000;
        fastcgi_index index.php;
        include fastcgi_params;
    }
}
```

### Step 4: Set Permissions

```bash
chmod -R 755 backend-php/
chmod -R 777 backend-php/uploads/
chmod -R 777 backend-php/processed/
chmod -R 777 backend-php/logs/
```

### Step 5: Start Server

#### **Built-in PHP Server (Development)**

```bash
cd backend-php
php -S localhost:8000
```

#### **Apache/Nginx (Production)**

```bash
# Apache
sudo systemctl start apache2

# Nginx
sudo systemctl start nginx
sudo systemctl start php8.1-fpm
```

---

## 📡 API Endpoints

All endpoints match the Python FastAPI backend:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/auth/login` | POST | Login with JWT |
| `/api/upload/` | POST | Upload HTML file |
| `/api/data/` | GET | Get IP records |
| `/api/data/summary` | GET | Get statistics |
| `/api/process/extract` | GET | Extract IPs from HTML |
| `/api/process/merge` | POST | Merge InfoByIP CSVs |
| `/api/process/export` | GET | Download Excel file |

---

## 🔧 Usage Examples

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"inspector","password":"secure@123"}'
```

### Upload HTML File

```bash
curl -X POST http://localhost:8000/api/upload/ \
  -F "file=@subscriber.html" \
  -F "fir=FIR/2025/001"
```

### Get Records

```bash
curl http://localhost:8000/api/data/?limit=50
```

### Get Summary

```bash
curl http://localhost:8000/api/data/summary
```

---

## 🗄️ Database Integration

The PHP backend uses **PDO (PHP Data Objects)** for PostgreSQL:

```php
// Example: Insert record
$ipRecord = new IPRecord($db);
$ipRecord->timestamp = '2025-01-01 12:00:00';
$ipRecord->ip = '8.8.8.8';
$ipRecord->country = 'US';
$ipRecord->city = 'Mountain View';
$ipRecord->isp = 'Google';
$ipRecord->source_file = 'subscriber.html';
$id = $ipRecord->create();
```

---

## 🔐 Security Features

1. **JWT Authentication** - Token-based auth with HS256
2. **SQL Injection Prevention** - PDO prepared statements
3. **File Type Validation** - Only HTML files allowed
4. **CORS Headers** - Configurable cross-origin access
5. **Input Sanitization** - All inputs validated

---

## 🆚 PHP vs Python Backend

| Feature | PHP Backend | Python Backend |
|---------|-------------|----------------|
| Language | PHP 8+ | Python 3.10+ |
| Framework | Native PHP | FastAPI |
| Database | PDO (PostgreSQL) | SQLAlchemy |
| Performance | Good | Excellent |
| Async Support | Limited | Full (async/await) |
| Deployment | Apache/Nginx | Uvicorn |
| Learning Curve | Easy | Moderate |
| Community | Large | Growing |

---

## 🎯 When to Use PHP Backend?

✅ **Use PHP if:**
- You have existing PHP infrastructure
- Your team is more familiar with PHP
- You need Apache/cPanel hosting
- You want simpler deployment

✅ **Use Python if:**
- You need async processing
- You want modern API features
- You prefer type hints and validation
- You need better performance

---

## 🔄 Switching Between Backends

The frontend works with **both backends**! Just change the API base URL:

```typescript
// In frontend/nuxt.config.ts
export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      // Python backend
      apiBase: 'http://localhost:8000'
      
      // OR PHP backend
      apiBase: 'http://localhost:80/backend-php'
    }
  }
})
```

---

## 📊 Features Implemented

✅ File upload with validation  
✅ HTML parsing (DOMDocument)  
✅ IP extraction with validation  
✅ Batch creation (100 IPs per batch)  
✅ Database CRUD operations  
✅ JWT authentication  
✅ Statistics & analytics  
✅ CSV merging  
✅ Error handling  
✅ CORS support  

---

## 🐛 Troubleshooting

### "Call to undefined function pg_connect"
```bash
# Install PostgreSQL extension
sudo apt install php-pgsql
# Enable in php.ini
extension=pdo_pgsql
```

### "Permission denied" errors
```bash
chmod -R 777 uploads/ processed/ logs/
```

### ".htaccess not working"
```bash
# Enable mod_rewrite in Apache
sudo a2enmod rewrite
sudo systemctl restart apache2
```

### "CORS errors"
Check that `.htaccess` has CORS headers or add them to `index.php`

---

## 📈 Performance Tips

1. **Enable OPcache** - Speeds up PHP execution
2. **Use Connection Pooling** - For database connections
3. **Enable Gzip Compression** - Reduce response size
4. **Use CDN** - For static assets
5. **Implement Caching** - Redis/Memcached for sessions

---

## 🚀 Production Deployment

### Using Apache

```bash
# Copy files to web root
sudo cp -r backend-php /var/www/html/

# Set ownership
sudo chown -R www-data:www-data /var/www/html/backend-php

# Restart Apache
sudo systemctl restart apache2
```

### Using Docker

```dockerfile
FROM php:8.1-apache

# Install extensions
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && docker-php-ext-install pdo pdo_pgsql

# Enable mod_rewrite
RUN a2enmod rewrite

# Copy application
COPY . /var/www/html/

# Set permissions
RUN chmod -R 755 /var/www/html/
RUN chmod -R 777 /var/www/html/uploads /var/www/html/processed

EXPOSE 80
```

---

## 📝 Environment Variables

Create a `.env` file:

```env
DB_HOST=localhost
DB_NAME=police_data
DB_USER=police_user
DB_PASS=StrongPass
JWT_SECRET=supersecurekey
```

Load in PHP:

```php
// Load .env file
$env = parse_ini_file('.env');
foreach ($env as $key => $value) {
    putenv("$key=$value");
}
```

---

## ✅ Testing

```bash
# Test health endpoint
curl http://localhost:8000/

# Test login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"inspector","password":"secure@123"}'

# Test data endpoint
curl http://localhost:8000/api/data/summary
```

---

## 🎉 Summary

You now have **two backend options**:

1. **Python FastAPI** - Modern, fast, async
2. **PHP** - Traditional, widely supported, easy to deploy

Both backends:
- ✅ Use the same PostgreSQL database
- ✅ Provide identical API endpoints
- ✅ Work with the same Nuxt frontend
- ✅ Support JWT authentication
- ✅ Handle file uploads and processing

Choose the one that fits your infrastructure and team expertise!

---

**Built for Delhi Police Cyber Cell** 🚔
