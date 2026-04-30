# Environment Setup Guide

**Last Updated**: March 19, 2026

## Required Environment Variables

### Backend (.env or docker-compose.yml)

```bash
# CRITICAL - Must be set!
JWT_SECRET=your-super-secure-random-string-here-minimum-32-chars

# Database URL (asyncpg format)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/police_data

# Optional but recommended
ENVIRONMENT=production  # or "development"
JWT_REFRESH_SECRET=another-secure-random-string-here
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Directories
UPLOAD_DIR=/app/uploads
PROCESSED_DIR=/app/processed
MASTER_DIR=/app/master
LOG_DIR=/app/logs

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# Redis (if using)
REDIS_URL=redis://localhost:6379/0

# External services
INFOBYIP_URL=https://www.infobyip.com/ipbulklookup.php
```

## How to Generate Secure JWT_SECRET

### Option 1: Using OpenSSL (Linux/Mac)
```bash
openssl rand -base64 32
# Output example: iB9kL3+dXs7mN1vQp8rT2wJ5yH6gF4cE=
```

### Option 2: Using Python
```python
import secrets
print(secrets.token_urlsafe(32))
# Output: iB9kL3-dXs7mN1vQp8rT2wJ5yH6gF4cE
```

### Option 3: Using Node.js
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

## Docker Compose Setup

If using docker-compose, update the environment section:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: police_data
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: your-db-password
    volumes:
      - db_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      # Critical settings
      JWT_SECRET: iB9kL3-dXs7mN1vQp8rT2wJ5yH6gF4cE
      DATABASE_URL: postgresql+asyncpg://postgres:your-db-password@postgres:5432/police_data
      
      # Optional
      ENVIRONMENT: production
      ALLOWED_ORIGINS: http://localhost:3000,http://localhost:3001
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    ports:
      - "3001:3000"
    environment:
      VITE_API_BASE: http://localhost:8000

volumes:
  db_data:
```

## Running the Application

### With Docker Compose
```bash
# Build and start all services
docker-compose up -d

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down
```

### Without Docker (Local Development)

#### Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with required variables
cat > .env << EOF
JWT_SECRET=your-generated-secret-here
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/police_data
ENVIRONMENT=development
EOF

# Run migrations (if using alembic)
alembic upgrade head

# Start server
python main.py
```

#### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Create .env.local (optional, uses localhost:8000 by default)
echo "VITE_API_BASE=http://localhost:8000" > .env.local

# Start dev server
npm run dev
```

## Verification Checklist

After setting up environment variables:

- [ ] Backend starts without "Missing required environment variables" error
- [ ] Can login successfully at `http://localhost:3001/login`
- [ ] JWT tokens are generated (check browser localStorage/sessionStorage)
- [ ] Password reset page loads without error
- [ ] Form validation hook works (try submitting empty form)
- [ ] Error boundary catches errors (check dev console)
- [ ] Rate limiting works (try 6 login attempts in 5 minutes)

## Troubleshooting

### "Missing required environment variables"
**Solution**: Set `JWT_SECRET` and `DATABASE_URL` environment variables before starting backend.

### "Invalid or expired token" on every page load
**Solution**: Make sure `JWT_SECRET` is consistent across app restarts. Check that .env file is being loaded.

### "Cannot connect to backend" on frontend
**Solution**: 
- Verify backend is running on port 8000
- Check `VITE_API_BASE` is set correctly
- Check CORS `ALLOWED_ORIGINS` includes frontend URL

### "Request timeout" errors
**Solution**: 
- Default timeout is 30 seconds, increase if needed
- Check backend performance and network latency

## Production Deployment

Before deploying to production:

1. **Generate strong secrets**:
   ```bash
   JWT_SECRET=$(openssl rand -base64 32)
   DB_PASSWORD=$(openssl rand -base64 32)
   ```

2. **Use environment-specific values**:
   - Set `ENVIRONMENT=production`
   - Use production database URL
   - Set `ALLOWED_ORIGINS` to your production domain

3. **Store secrets securely**:
   - Use AWS Secrets Manager / HashiCorp Vault
   - Never commit secrets to git
   - Use strong random values for all secrets

4. **Enable HTTPS**:
   - Update cookie settings: `secure=True`
   - Set correct CORS origin (https://domain.com)

5. **Database migrations**:
   ```bash
   # Run before deploying
   alembic upgrade head
   ```

## Security Best Practices

✅ **DO:**
- Use strong random secrets (minimum 32 characters)
- Rotate JWT_SECRET periodically (users will need to re-login)
- Use environment variables, never hardcode secrets
- Enable HTTPS in production
- Use secure database passwords
- Monitor rate limiting hits for abuse attempts

❌ **DON'T:**
- Commit .env files to git
- Use same secret across dev/prod
- Share secrets in logs or error messages
- Use weak or predictable secrets
- Expose BACKEND_URL to frontend (use relative paths)

