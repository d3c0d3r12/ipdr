"""
Database Migration Script - Cloud Storage Tables
Creates all tables for multi-file per FIR cloud storage system
Run this once to set up the database
"""
import asyncio
from sqlalchemy import text
from database import engine, Base, DATABASE_URL
from models.investigation import (
    Investigation, IPLookupResult, FileStorage, 
    GeneratedDocument, BackgroundTask, ProgressTracking
)
from models.fir_case import FIRCase
from models.user_auth import User


async def create_tables():
    """Create all cloud storage tables"""
    print("🚀 Creating cloud storage tables...")
    print(f"📍 Database: {DATABASE_URL.split('@')[0] if '@' in DATABASE_URL else 'SQLite'}")
    
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
            print("✅ Tables created successfully!")
            
            # Get table names (works for both SQLite and PostgreSQL)
            is_sqlite = 'sqlite' in DATABASE_URL.lower()
            
            if is_sqlite:
                # SQLite query
                result = await conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """))
            else:
                # PostgreSQL query
                result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
            
            tables = result.fetchall()
            print(f"\n📋 Created {len(tables)} tables:")
            for table in tables:
                print(f"   ✓ {table[0]}")
            
            # Create indexes for performance
            print("\n🔧 Creating indexes...")
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_investigations_fir_number ON investigations(fir_number)",
                "CREATE INDEX IF NOT EXISTS idx_investigations_user_id ON investigations(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_investigations_status ON investigations(status)",
                "CREATE INDEX IF NOT EXISTS idx_ip_results_investigation ON ip_lookup_results(investigation_id)",
                "CREATE INDEX IF NOT EXISTS idx_ip_results_ip ON ip_lookup_results(ip_address)",
                "CREATE INDEX IF NOT EXISTS idx_ip_results_isp ON ip_lookup_results(isp)",
                "CREATE INDEX IF NOT EXISTS idx_file_storage_investigation ON file_storage(investigation_id)",
                "CREATE INDEX IF NOT EXISTS idx_file_storage_type ON file_storage(file_type)",
                "CREATE INDEX IF NOT EXISTS idx_documents_investigation ON generated_documents(investigation_id)",
                "CREATE INDEX IF NOT EXISTS idx_documents_type ON generated_documents(document_type)",
                "CREATE INDEX IF NOT EXISTS idx_tasks_task_id ON background_tasks(task_id)",
                "CREATE INDEX IF NOT EXISTS idx_tasks_status ON background_tasks(status)",
            ]
            
            for index_sql in indexes:
                try:
                    await conn.execute(text(index_sql))
                except Exception as e:
                    print(f"   ⚠️  Index warning: {e}")
            
            print(f"✅ Indexes created")
            
            print("\n🎉 Database setup complete!")
            print("\n📊 Schema Summary:")
            print("   • users - User accounts")
            print("   • fir_cases - Store FIR metadata")
            print("   • investigations - Multiple investigations per FIR")
            print("   • ip_lookup_results - IP data for each investigation")
            print("   • file_storage - Binary file storage (CSV, ZIP)")
            print("   • generated_documents - ISP letters, reports")
            print("   • background_tasks - Task tracking")
            print("   • progress_tracking - Resume capability")
            print("\n✅ Ready for cloud storage!")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("CLOUD STORAGE DATABASE SETUP")
    print("=" * 60)
    
    try:
        asyncio.run(create_tables())
        
        print("\n" + "=" * 60)
        print("SETUP COMPLETE - Database ready for use!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("\nPlease check:")
        print("  1. Database connection in database.py")
        print("  2. All required packages are installed")
        print("  3. Database server is running (if using PostgreSQL)")
        exit(1)
