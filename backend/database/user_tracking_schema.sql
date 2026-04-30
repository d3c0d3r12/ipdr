-- User Sessions Tracking Table
-- Tracks every user visit with detailed information

CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- User Information
    username VARCHAR(100),
    user_role VARCHAR(50),
    is_authenticated BOOLEAN DEFAULT FALSE,
    
    -- IP & Location Details
    ip_address VARCHAR(45) NOT NULL,
    country VARCHAR(100),
    region VARCHAR(100),
    city VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    timezone VARCHAR(50),
    isp VARCHAR(255),
    
    -- Device Information
    user_agent TEXT,
    browser VARCHAR(100),
    browser_version VARCHAR(50),
    os VARCHAR(100),
    os_version VARCHAR(50),
    device_type VARCHAR(50), -- desktop, mobile, tablet
    device_vendor VARCHAR(100),
    device_model VARCHAR(100),
    
    -- Screen & Display
    screen_resolution VARCHAR(50),
    viewport_size VARCHAR(50),
    color_depth INTEGER,
    
    -- Session Timing
    session_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    session_duration INTEGER, -- in seconds
    
    -- Referrer & Entry
    referrer_url TEXT,
    entry_page VARCHAR(500),
    exit_page VARCHAR(500),
    
    -- Network Details
    connection_type VARCHAR(50),
    effective_type VARCHAR(50), -- 4g, 3g, 2g, slow-2g
    downlink DECIMAL(5, 2),
    rtt INTEGER,
    
    -- Browser Features
    cookies_enabled BOOLEAN,
    javascript_enabled BOOLEAN DEFAULT TRUE,
    language VARCHAR(10),
    languages TEXT[], -- Array of accepted languages
    
    -- Security & Privacy
    do_not_track BOOLEAN,
    incognito_mode BOOLEAN,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User Activity Log Table
-- Tracks every action performed by users

CREATE TABLE IF NOT EXISTS user_activities (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    
    -- Activity Details
    activity_type VARCHAR(100) NOT NULL, -- page_view, upload, download, search, etc.
    activity_description TEXT,
    page_url VARCHAR(500),
    page_title VARCHAR(255),
    
    -- Action Details
    action_category VARCHAR(100), -- navigation, file_operation, data_query, etc.
    action_data JSONB, -- Store additional data as JSON
    
    -- Performance
    load_time INTEGER, -- milliseconds
    interaction_time INTEGER, -- time spent on action
    
    -- Result
    status VARCHAR(50), -- success, error, pending
    error_message TEXT,
    
    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Page Views Table
-- Detailed page navigation tracking

CREATE TABLE IF NOT EXISTS page_views (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    
    -- Page Details
    page_url VARCHAR(500) NOT NULL,
    page_title VARCHAR(255),
    page_path VARCHAR(500),
    
    -- Timing
    view_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    view_end TIMESTAMP WITH TIME ZONE,
    time_on_page INTEGER, -- seconds
    
    -- Interaction
    scroll_depth INTEGER, -- percentage
    clicks_count INTEGER DEFAULT 0,
    
    -- Navigation
    previous_page VARCHAR(500),
    next_page VARCHAR(500),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes for Performance
CREATE INDEX idx_sessions_ip ON user_sessions(ip_address);
CREATE INDEX idx_sessions_username ON user_sessions(username);
CREATE INDEX idx_sessions_start ON user_sessions(session_start);
CREATE INDEX idx_sessions_session_id ON user_sessions(session_id);

CREATE INDEX idx_activities_session ON user_activities(session_id);
CREATE INDEX idx_activities_type ON user_activities(activity_type);
CREATE INDEX idx_activities_timestamp ON user_activities(timestamp);

CREATE INDEX idx_pageviews_session ON page_views(session_id);
CREATE INDEX idx_pageviews_url ON page_views(page_url);
CREATE INDEX idx_pageviews_start ON page_views(view_start);

-- Create Views for Easy Querying

-- Active Sessions View
CREATE OR REPLACE VIEW active_sessions AS
SELECT 
    s.session_id,
    s.username,
    s.ip_address,
    s.country,
    s.city,
    s.browser,
    s.os,
    s.device_type,
    s.session_start,
    s.last_activity,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - s.last_activity)) as idle_seconds,
    COUNT(a.id) as activity_count
FROM user_sessions s
LEFT JOIN user_activities a ON s.session_id = a.session_id
WHERE s.session_end IS NULL
GROUP BY s.session_id;

-- Session Summary View
CREATE OR REPLACE VIEW session_summary AS
SELECT 
    DATE(session_start) as date,
    COUNT(*) as total_sessions,
    COUNT(DISTINCT ip_address) as unique_visitors,
    COUNT(CASE WHEN is_authenticated THEN 1 END) as authenticated_sessions,
    AVG(session_duration) as avg_duration,
    COUNT(CASE WHEN device_type = 'mobile' THEN 1 END) as mobile_sessions,
    COUNT(CASE WHEN device_type = 'desktop' THEN 1 END) as desktop_sessions
FROM user_sessions
GROUP BY DATE(session_start)
ORDER BY date DESC;

-- Popular Pages View
CREATE OR REPLACE VIEW popular_pages AS
SELECT 
    page_url,
    page_title,
    COUNT(*) as view_count,
    AVG(time_on_page) as avg_time_on_page,
    SUM(clicks_count) as total_clicks
FROM page_views
GROUP BY page_url, page_title
ORDER BY view_count DESC;

-- User Activity Summary View
CREATE OR REPLACE VIEW user_activity_summary AS
SELECT 
    s.username,
    s.ip_address,
    COUNT(DISTINCT s.session_id) as total_sessions,
    SUM(s.session_duration) as total_time_spent,
    COUNT(a.id) as total_activities,
    MAX(s.last_activity) as last_seen
FROM user_sessions s
LEFT JOIN user_activities a ON s.session_id = a.session_id
WHERE s.username IS NOT NULL
GROUP BY s.username, s.ip_address
ORDER BY last_seen DESC;

-- Comments
COMMENT ON TABLE user_sessions IS 'Tracks all user sessions with detailed device and location information';
COMMENT ON TABLE user_activities IS 'Logs all user actions and interactions within the system';
COMMENT ON TABLE page_views IS 'Tracks page navigation and engagement metrics';
