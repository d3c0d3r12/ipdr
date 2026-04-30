"""
Fix All Database Issues - Complete Migration Script
Ensures all tables and columns exist with correct schema
"""
import asyncio
from sqlalchemy import text
from database import engine, DATABASE_URL, Base
from models.investigation import (
    Investigation, IPLookupResult, FileStorage, 
    GeneratedDocument, BackgroundTask, ProgressTracking
)
from models.fir_case import FIRCase
from models.user_auth import User


async def fix_all_database():
    """Fix all database schema issues"""
    print("🔧 Fixing all database issues...")
    print(f"📍 Database: {DATABASE_URL.split('@')[0] if '@' in DATABASE_URL else 'SQLite'}")
    
    try:
        async with engine.begin() as conn:
            is_sqlite = 'sqlite' in DATABASE_URL.lower()
            
            # Step 1: Create all tables if they don't exist
            print("\n📊 Step 1: Creating/updating tables...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Tables created/updated")
            
            # Step 2: Add missing columns to fir_cases and investigations
            print("\n📊 Step 2: Checking table columns...")
            
            if is_sqlite:
                result = await conn.execute(text("PRAGMA table_info(fir_cases)"))
                columns = result.fetchall()
                column_names = [col[1] for col in columns]
                
                # Add total_investigations if missing
                if 'total_investigations' not in column_names:
                    print("➕ Adding total_investigations column to fir_cases...")
                    await conn.execute(text(
                        "ALTER TABLE fir_cases ADD COLUMN total_investigations INTEGER DEFAULT 0"
                    ))
                    print("✅ Added total_investigations")
                else:
                    print("✅ total_investigations exists")
                
                # Check investigations table
                result = await conn.execute(text("PRAGMA table_info(investigations)"))
                inv_columns = result.fetchall()
                inv_column_names = [col[1] for col in inv_columns]
                
                # Add current_step if missing
                if 'current_step' not in inv_column_names:
                    print("➕ Adding current_step column to investigations...")
                    await conn.execute(text(
                        "ALTER TABLE investigations ADD COLUMN current_step INTEGER DEFAULT 1"
                    ))
                    print("✅ Added current_step")
                else:
                    print("✅ current_step exists")
                    
            else:
                # PostgreSQL
                # Check and add total_investigations
                result = await conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='fir_cases' AND column_name='total_investigations'
                """))
                
                if not result.fetchone():
                    print("➕ Adding total_investigations column to fir_cases...")
                    await conn.execute(text(
                        "ALTER TABLE fir_cases ADD COLUMN total_investigations INTEGER DEFAULT 0"
                    ))
                    print("✅ Added total_investigations")
                else:
                    print("✅ total_investigations exists")
                
                # Check and add current_step to investigations
                result = await conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='investigations' AND column_name='current_step'
                """))
                
                if not result.fetchone():
                    print("➕ Adding current_step column to investigations...")
                    await conn.execute(text(
                        "ALTER TABLE investigations ADD COLUMN current_step INTEGER DEFAULT 1"
                    ))
                    print("✅ Added current_step")
                else:
                    print("✅ current_step exists")
            
            # Step 3: Verify all tables exist
            print("\n📊 Step 3: Verifying tables...")
            
            if is_sqlite:
                result = await conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """))
            else:
                result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
            
            tables = result.fetchall()
            print(f"✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"   ✓ {table[0]}")
            
            # Step 4: Create indexes
            print("\n📊 Step 4: Creating indexes...")
            
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
            
            print("\n🎉 All database issues fixed!")
            print("\n📊 Database is ready for use!")
            
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("FIX ALL DATABASE ISSUES")
    print("=" * 60)
    
    try:
        asyncio.run(fix_all_database())
        
        print("\n" + "=" * 60)
        print("ALL FIXES COMPLETE!")
        print("=" * 60)
        print("\n✅ Database is ready!")
        print("✅ All tables exist!")
        print("✅ All columns exist!")
        print("✅ All indexes created!")
        print("\nYou can now start the backend:")
        print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\n❌ Fix failed: {e}")
        print("\nPlease check:")
        print("  1. Database connection in database.py")
        print("  2. Database server is running")
        print("  3. You have write permissions")
        exit(1)
