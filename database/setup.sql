CREATE TABLE IF NOT EXISTS ip_records (
	id SERIAL PRIMARY KEY,
	timestamp TEXT,
	ip TEXT,
	country TEXT,
	region TEXT,
	city TEXT,
	isp TEXT,
	source_file TEXT,
	created_at TIMESTAMP DEFAULT NOW()
);





