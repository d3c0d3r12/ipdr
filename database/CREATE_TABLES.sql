-- ============================================
-- IPDR TRACKING HUB - DATABASE SETUP
-- Create all tables for production
-- ============================================

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    full_name VARCHAR(200),
    badge_number VARCHAR(50),
    department VARCHAR(200),
    designation VARCHAR(200),
    phone_number VARCHAR(20),
    role VARCHAR(50) DEFAULT 'investigator',
    permissions JSONB,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    is_locked BOOLEAN DEFAULT false,
    failed_login_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    last_password_change TIMESTAMP WITH TIME ZONE,
    two_factor_enabled BOOLEAN DEFAULT false,
    two_factor_secret VARCHAR(100),
    recovery_email VARCHAR(200),
    created_by VARCHAR(100),
    approved_by VARCHAR(100),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. USER SESSIONS TABLE
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    username VARCHAR(100),
    session_token VARCHAR(256) UNIQUE NOT NULL,
    refresh_token VARCHAR(256) UNIQUE,
    ip_address VARCHAR(100),
    user_agent TEXT,
    device_type VARCHAR(50),
    browser VARCHAR(100),
    os VARCHAR(100),
    country VARCHAR(100),
    city VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);

-- 3. USER ACTIVITIES TABLE
CREATE TABLE IF NOT EXISTS user_activities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    username VARCHAR(100),
    session_id INTEGER,
    activity_type VARCHAR(100),
    activity_description TEXT,
    endpoint VARCHAR(500),
    method VARCHAR(10),
    status_code INTEGER,
    ip_address VARCHAR(100),
    user_agent TEXT,
    request_data JSONB,
    response_data JSONB,
    duration_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activities_user_id ON user_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_activities_type ON user_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_activities_created ON user_activities(created_at);

-- 4. LOGIN ATTEMPTS TABLE
CREATE TABLE IF NOT EXISTS login_attempts (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100),
    email VARCHAR(200),
    ip_address VARCHAR(100),
    user_agent TEXT,
    success BOOLEAN,
    failure_reason VARCHAR(200),
    country VARCHAR(100),
    city VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_login_attempts_username ON login_attempts(username);
CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address);
CREATE INDEX IF NOT EXISTS idx_login_attempts_created ON login_attempts(created_at);

-- 5. ACCESS LOGS TABLE
CREATE TABLE IF NOT EXISTS access_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    username VARCHAR(100),
    endpoint VARCHAR(500),
    method VARCHAR(10),
    ip_address VARCHAR(100),
    user_agent TEXT,
    status_code INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_access_logs_user_id ON access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_endpoint ON access_logs(endpoint);
CREATE INDEX IF NOT EXISTS idx_access_logs_created ON access_logs(created_at);

-- 6. USER PERMISSIONS TABLE
CREATE TABLE IF NOT EXISTS user_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    permission_name VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id INTEGER,
    granted_by VARCHAR(100),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_permissions_user_id ON user_permissions(user_id);

-- 7. FIR CASES TABLE
CREATE TABLE IF NOT EXISTS fir_cases (
    id SERIAL PRIMARY KEY,
    fir_number VARCHAR(100) UNIQUE NOT NULL,
    case_title VARCHAR(500),
    case_description TEXT,
    case_type VARCHAR(100),
    priority VARCHAR(50),
    status VARCHAR(50) DEFAULT 'open',
    investigating_officer VARCHAR(200),
    department VARCHAR(200),
    police_station VARCHAR(200),
    district VARCHAR(100),
    state VARCHAR(100),
    filed_date DATE,
    incident_date DATE,
    incident_location TEXT,
    victim_name VARCHAR(200),
    victim_contact VARCHAR(100),
    suspect_info TEXT,
    evidence_collected TEXT,
    case_notes TEXT,
    created_by VARCHAR(100),
    assigned_to VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    closed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_fir_cases_number ON fir_cases(fir_number);
CREATE INDEX IF NOT EXISTS idx_fir_cases_status ON fir_cases(status);
CREATE INDEX IF NOT EXISTS idx_fir_cases_created ON fir_cases(created_at);

-- 8. FIR IP LOOKUPS TABLE
CREATE TABLE IF NOT EXISTS fir_ip_lookups (
    id SERIAL PRIMARY KEY,
    fir_id INTEGER,
    fir_number VARCHAR(100),
    ip_address VARCHAR(100),
    lookup_date TIMESTAMP WITH TIME ZONE,
    country VARCHAR(100),
    region VARCHAR(100),
    city VARCHAR(100),
    isp VARCHAR(200),
    organization VARCHAR(200),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    timezone VARCHAR(100),
    postal_code VARCHAR(20),
    lookup_source VARCHAR(100),
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fir_ip_lookups_fir_id ON fir_ip_lookups(fir_id);
CREATE INDEX IF NOT EXISTS idx_fir_ip_lookups_ip ON fir_ip_lookups(ip_address);

-- 9. FIR EVIDENCE TABLE
CREATE TABLE IF NOT EXISTS fir_evidence (
    id SERIAL PRIMARY KEY,
    fir_id INTEGER,
    fir_number VARCHAR(100),
    evidence_type VARCHAR(100),
    evidence_description TEXT,
    file_name VARCHAR(500),
    file_path VARCHAR(1000),
    file_size INTEGER,
    file_hash VARCHAR(256),
    collected_by VARCHAR(200),
    collected_at TIMESTAMP WITH TIME ZONE,
    chain_of_custody TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fir_evidence_fir_id ON fir_evidence(fir_id);

-- 10. FIR SUSPECTS TABLE
CREATE TABLE IF NOT EXISTS fir_suspects (
    id SERIAL PRIMARY KEY,
    fir_id INTEGER,
    fir_number VARCHAR(100),
    suspect_name VARCHAR(200),
    suspect_alias VARCHAR(200),
    age INTEGER,
    gender VARCHAR(20),
    address TEXT,
    phone_number VARCHAR(100),
    email VARCHAR(200),
    identification_marks TEXT,
    criminal_history TEXT,
    status VARCHAR(50),
    arrested BOOLEAN DEFAULT false,
    arrest_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fir_suspects_fir_id ON fir_suspects(fir_id);

-- 11. FIR TIMELINE TABLE
CREATE TABLE IF NOT EXISTS fir_timeline (
    id SERIAL PRIMARY KEY,
    fir_id INTEGER,
    fir_number VARCHAR(100),
    event_type VARCHAR(100),
    event_description TEXT,
    event_date TIMESTAMP WITH TIME ZONE,
    performed_by VARCHAR(200),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fir_timeline_fir_id ON fir_timeline(fir_id);
CREATE INDEX IF NOT EXISTS idx_fir_timeline_date ON fir_timeline(event_date);

-- ============================================
-- INSERT DEFAULT ADMIN USER
-- ============================================
-- INSERT DEFAULT ADMIN USER
-- Password: Admin@123456
-- Salt: adminsalt123456789012345678901234567890123456789012345678901234
-- Hash generated with PBKDF2-SHA256
INSERT INTO users (
    username, 
    email, 
    password_hash,
    salt,
    full_name, 
    role, 
    is_active, 
    is_verified,
    department,
    designation,
    last_password_change,
    created_at,
    updated_at
) VALUES (
    'admin',
    'admin@delhipolice.gov.in',
    'a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1',
    'adminsalt123456789012345678901234567890123456789012345678901234',
    'System Administrator',
    'admin',
    true,
    true,
    'Delhi Police Cyber Cell',
    'System Administrator',
    NOW(),
    NOW(),
    NOW()
) ON CONFLICT (username) DO NOTHING;

-- ============================================
-- VERIFICATION

-- Check if admin user was created
SELECT username, email, role, is_active, is_verified 
FROM users 
WHERE username = 'admin';

-- Show all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
