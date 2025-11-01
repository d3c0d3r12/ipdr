-- ============================================
-- Police Intelligence System - Create Tables Only
-- Use this if database already exists
-- ============================================

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
-- Verify Setup
-- ============================================

-- Check tables
SELECT 'Tables created:' as status;
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- Check indexes
SELECT 'Indexes created:' as status;
SELECT 
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Check table structure
SELECT 'Table structure:' as status;
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'ip_records'
ORDER BY ordinal_position;

-- ============================================
-- Insert Sample Data (Optional - for testing)
-- ============================================

INSERT INTO ip_records (timestamp, ip, country, region, city, isp, source_file)
VALUES 
    ('2024-01-15 10:30:00', '8.8.8.8', 'US', 'California', 'Mountain View', 'Google LLC', 'test_subscriber.html'),
    ('2024-01-15 10:35:00', '1.1.1.1', 'AU', 'Queensland', 'Brisbane', 'Cloudflare', 'test_subscriber.html'),
    ('2024-01-15 10:40:00', '142.250.185.46', 'US', 'California', 'Mountain View', 'Google LLC', 'test_subscriber.html')
ON CONFLICT DO NOTHING;

-- Verify insert
SELECT 'Sample data inserted:' as status;
SELECT COUNT(*) as total_records FROM ip_records;

-- Show sample records
SELECT 'Sample records:' as status;
SELECT * FROM ip_records LIMIT 3;

-- ============================================
-- Analyze table for query optimization
-- ============================================
ANALYZE ip_records;

-- ============================================
-- Success Message
-- ============================================
SELECT '✅ Setup complete! Tables and indexes created successfully.' as message;
