"""
Create all database tables - ASYNC VERSION
Run this to create investigations and other tables
"""
import asyncio
from sqlalchemy import text
from database import engine, DATABASE_URL


async def create_all_tables():
    """Create all tables in the database"""
    print("=" * 60)
    print("CREATING ALL DATABASE TABLES")
    print("=" * 60)
    print(f"\n📍 Database: {DATABASE_URL[:50]}...")
    
    try:
        async with engine.begin() as conn:
            # Create investigations table
            print("\n📊 Creating investigations table...")
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS investigations (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(255) UNIQUE NOT NULL,
                    fir_id INTEGER,
                    fir_number VARCHAR(100),
                    user_id INTEGER,
                    investigation_name VARCHAR(255),
                    description TEXT,
                    status VARCHAR(50) DEFAULT 'pending',
                    current_step INTEGER DEFAULT 1,
                    total_ips INTEGER DEFAULT 0,
                    completed_ips INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    progress_percentage NUMERIC(5,2) DEFAULT 0,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✅ investigations table created!")
            
            # Create ip_lookup_results table
            print("\n📊 Creating ip_lookup_results table...")
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ip_lookup_results (
                    id SERIAL PRIMARY KEY,
                    investigation_id INTEGER REFERENCES investigations(id) ON DELETE CASCADE,
                    ip_address VARCHAR(45) NOT NULL,
                    timestamp TIMESTAMP,
                    country VARCHAR(100),
                    region VARCHAR(100),
                    city VARCHAR(100),
                    isp VARCHAR(255),
                    postal_code VARCHAR(20),
                    latitude NUMERIC(10, 8),
                    longitude NUMERIC(11, 8),
                    timezone VARCHAR(50),
                    lookup_source VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✅ ip_lookup_results table created!")
            
            # Create file_storage table
            print("\n📊 Creating file_storage table...")
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS file_storage (
                    id SERIAL PRIMARY KEY,
                    investigation_id INTEGER REFERENCES investigations(id) ON DELETE CASCADE,
                    filename VARCHAR(255) NOT NULL,
                    file_data BYTEA NOT NULL,
                    file_type VARCHAR(50),
                    mime_type VARCHAR(100),
                    file_size INTEGER,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✅ file_storage table created!")
            
            # Create generated_documents table
            print("\n📊 Creating generated_documents table...")
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS generated_documents (
                    id SERIAL PRIMARY KEY,
                    investigation_id INTEGER REFERENCES investigations(id) ON DELETE CASCADE,
                    document_type VARCHAR(50),
                    filename VARCHAR(255),
                    file_data BYTEA,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✅ generated_documents table created!")
            
            # Create background_tasks table
            print("\n📊 Creating background_tasks table...")
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS background_tasks (
                    id SERIAL PRIMARY KEY,
                    task_id VARCHAR(255) UNIQUE NOT NULL,
                    investigation_id INTEGER,
                    task_type VARCHAR(50),
                    status VARCHAR(50) DEFAULT 'pending',
                    progress INTEGER DEFAULT 0,
                    result TEXT,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """))
            print("✅ background_tasks table created!")
            
            # Create progress_tracking table
            print("\n📊 Creating progress_tracking table...")
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS progress_tracking (
                    id SERIAL PRIMARY KEY,
                    investigation_id INTEGER REFERENCES investigations(id) ON DELETE CASCADE,
                    completed_ips TEXT,
                    remaining_ips TEXT,
                    last_processed_ip VARCHAR(45),
                    can_resume BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✅ progress_tracking table created!")
            
            # Add total_investigations to fir_cases if not exists
            print("\n📊 Adding total_investigations to fir_cases...")
            try:
                await conn.execute(text("""
                    ALTER TABLE fir_cases ADD COLUMN IF NOT EXISTS total_investigations INTEGER DEFAULT 0
                """))
                print("✅ total_investigations column added!")
            except Exception as e:
                print(f"⚠️  Column might already exist: {e}")
            
            # Create indexes
            print("\n📊 Creating indexes...")
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_investigations_fir_number ON investigations(fir_number)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_investigations_run_id ON investigations(run_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ip_lookup_investigation_id ON ip_lookup_results(investigation_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_file_storage_investigation_id ON file_storage(investigation_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_background_tasks_task_id ON background_tasks(task_id)"))
            print("✅ All indexes created!")
            
        print("\n" + "=" * 60)
        print("DATABASE SETUP COMPLETE!")
        print("=" * 60)
        print("\n✅ All tables are ready!")
        print("\n🚀 Now restart your backend:")
        print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    asyncio.run(create_all_tables())
