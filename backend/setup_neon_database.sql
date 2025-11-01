-- ============================================
-- Police Intelligence System - Neon Database Setup
-- ============================================
-- Run this in Neon SQL Editor or via psql
-- ============================================

-- Create database (if not exists)
-- Note: In Neon, database is usually created automatically
-- CREATE DATABASE police_data;

-- Connect to database
-- \c police_data

-- ============================================
-- Create Tables
-- ============================================

-- IP Records Table
CREATE TABLE IF NOT EXISTS ip_records (
    id SERIAL PRIMARY KEY,
    timestamp TEXT NOT NULL,
    ip TEXT NOT NULL,
    country TEXT,
    region TEXT,
    city TEXT,
    isp TEXT,
    source_file TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- Create Indexes for Performance
-- ============================================

CREATE INDEX IF NOT EXISTS idx_ip_records_ip 
    ON ip_records(ip);

CREATE INDEX IF NOT EXISTS idx_ip_records_country 
    ON ip_records(country);

CREATE INDEX IF NOT EXISTS idx_ip_records_created_at 
    ON ip_records(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ip_records_source_file 
    ON ip_records(source_file);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_ip_records_ip_timestamp 
    ON ip_records(ip, created_at DESC);

-- ============================================
-- Create Application User (Optional)
-- ============================================
-- For better security, create a separate user for the application

-- CREATE USER police_app WITH PASSWORD 'YourStrongPassword123!';
-- GRANT CONNECT ON DATABASE police_data TO police_app;
-- GRANT USAGE ON SCHEMA public TO police_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO police_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO police_app;

-- Revoke dangerous permissions
-- REVOKE CREATE ON SCHEMA public FROM police_app;

-- ============================================
-- Verify Setup
-- ============================================

-- Check tables
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- Check indexes
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Check table structure
\d ip_records

-- Check current database size
SELECT pg_size_pretty(pg_database_size(current_database())) as database_size;

-- Check table size
SELECT 
    pg_size_pretty(pg_total_relation_size('ip_records')) as total_size,
    pg_size_pretty(pg_relation_size('ip_records')) as table_size,
    pg_size_pretty(pg_total_relation_size('ip_records') - pg_relation_size('ip_records')) as indexes_size;

-- ============================================
-- Sample Data (Optional - for testing)
-- ============================================

-- Insert test records
INSERT INTO ip_records (timestamp, ip, country, region, city, isp, source_file)
VALUES 
    ('2024-01-15 10:30:00', '8.8.8.8', 'US', 'California', 'Mountain View', 'Google LLC', 'test_subscriber.html'),
    ('2024-01-15 10:35:00', '1.1.1.1', 'AU', 'Queensland', 'Brisbane', 'Cloudflare', 'test_subscriber.html'),
    ('2024-01-15 10:40:00', '142.250.185.46', 'US', 'California', 'Mountain View', 'Google LLC', 'test_subscriber.html')
ON CONFLICT DO NOTHING;

-- Verify insert
SELECT COUNT(*) as total_records FROM ip_records;

-- ============================================
-- Maintenance Queries
-- ============================================

-- Analyze table for query optimization
ANALYZE ip_records;

-- Vacuum to reclaim space (run periodically)
-- VACUUM ANALYZE ip_records;

-- ============================================
-- Monitoring Queries
-- ============================================

-- Check active connections
SELECT 
    datname,
    usename,
    application_name,
    client_addr,
    state,
    query_start
FROM pg_stat_activity
WHERE datname = current_database()
ORDER BY query_start DESC;

-- Check table statistics
SELECT 
    schemaname,
    tablename,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE tablename = 'ip_records';

-- ============================================
-- Success Message
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '✅ Database setup complete!';
    RAISE NOTICE '📊 Tables created: ip_records';
    RAISE NOTICE '🔍 Indexes created: 5 indexes';
    RAISE NOTICE '🚀 Ready to connect from your application!';
END $$;
