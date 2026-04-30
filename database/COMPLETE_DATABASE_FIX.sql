-- ============================================
-- COMPLETE DATABASE SETUP - WORKING VERSION
-- Run this in Neon SQL Editor
-- ============================================

-- Drop all tables
DROP TABLE IF EXISTS fir_timeline CASCADE;
DROP TABLE IF EXISTS fir_suspects CASCADE;
DROP TABLE IF EXISTS fir_evidence CASCADE;
DROP TABLE IF EXISTS fir_ip_lookups CASCADE;
DROP TABLE IF EXISTS fir_cases CASCADE;
DROP TABLE IF EXISTS user_permissions CASCADE;
DROP TABLE IF EXISTS access_logs CASCADE;
DROP TABLE IF EXISTS login_attempts CASCADE;
DROP TABLE IF EXISTS user_activities CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================
-- USERS TABLE - Matches User model exactly
-- ============================================
CREATE TABLE users (
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

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- ============================================
-- USER_SESSIONS TABLE - Matches UserSession model exactly
-- ============================================
CREATE TABLE user_sessions (
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

CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_sessions_active ON user_sessions(is_active);

-- ============================================
-- USER_ACTIVITIES TABLE - Matches UserActivity model exactly
-- ============================================
CREATE TABLE user_activities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    username VARCHAR(100),
    session_id INTEGER,
    activity_type VARCHAR(100),
    activity_description TEXT,
    activity_data JSONB,
    page_url VARCHAR(1000),
    page_title VARCHAR(500),
    http_method VARCHAR(10),
    http_status INTEGER,
    ip_address VARCHAR(100),
    ipv4 VARCHAR(50),
    ipv6 VARCHAR(100),
    user_agent TEXT,
    referer VARCHAR(1000),
    device_type VARCHAR(50),
    browser VARCHAR(100),
    browser_version VARCHAR(50),
    os VARCHAR(100),
    os_version VARCHAR(50),
    screen_resolution VARCHAR(50),
    country VARCHAR(100),
    city VARCHAR(100),
    region VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    duration_ms INTEGER,
    cookies JSONB,
    session_data JSONB,
    fir_number VARCHAR(100),
    is_suspicious BOOLEAN DEFAULT false,
    risk_score INTEGER DEFAULT 0,
    notes TEXT
);

CREATE INDEX idx_activities_user_id ON user_activities(user_id);
CREATE INDEX idx_activities_type ON user_activities(activity_type);
CREATE INDEX idx_activities_timestamp ON user_activities(timestamp);
CREATE INDEX idx_activities_fir ON user_activities(fir_number);

-- ============================================
-- LOGIN_ATTEMPTS TABLE - Matches LoginAttempt model exactly
-- ============================================
CREATE TABLE login_attempts (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100),
    email VARCHAR(200),
    ip_address VARCHAR(100),
    user_agent TEXT,
    device_type VARCHAR(50),
    browser VARCHAR(100),
    os VARCHAR(100),
    success BOOLEAN DEFAULT false,
    failure_reason VARCHAR(200),
    country VARCHAR(100),
    city VARCHAR(100),
    is_suspicious BOOLEAN DEFAULT false,
    blocked BOOLEAN DEFAULT false,
    notes TEXT,
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_login_attempts_username ON login_attempts(username);
CREATE INDEX idx_login_attempts_ip ON login_attempts(ip_address);
CREATE INDEX idx_login_attempts_attempted ON login_attempts(attempted_at);

-- ============================================
-- INSERT ADMIN USER
-- Password: Admin@123456
-- ============================================
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
    '10f03f615f1d6c087786c982b60e8e381e0e64837580d703c7c95755fbd3a811',
    'f422e013629d2d7321c73f043e33388759fc377a967f9b06203f0b377a5ae2ff',
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
-- ============================================

-- Check users table
SELECT 'Users table created' as status, COUNT(*) as user_count FROM users;

-- Show admin user
SELECT username, email, role, is_active, is_verified 
FROM users 
WHERE username = 'admin';

-- List all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Verify schema matches models
SELECT 
    'users' as table_name,
    column_name, 
    data_type,
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('password_hash', 'salt', 'username', 'email')
ORDER BY column_name;

SELECT 'Database setup complete! Admin user: admin / Admin@123456' as final_status;
