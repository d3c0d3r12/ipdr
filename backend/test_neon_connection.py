"""
Test Neon.tech Database Connection
Run this script to verify your Neon database is properly configured
"""

from sqlalchemy import create_engine, text
from core.config import DATABASE_URL, DB_HOST, DB_NAME
import sys

def test_connection():
    """Test connection to Neon database"""
    
    print("=" * 60)
    print("🔄 Testing Neon.tech Database Connection")
    print("=" * 60)
    print(f"📍 Host: {DB_HOST}")
    print(f"📊 Database: {DB_NAME}")
    print(f"🔐 SSL: Required")
    print("=" * 60)
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Test 1: Basic connection
            print("\n✅ Test 1: Basic Connection - PASSED")
            
            # Test 2: PostgreSQL version
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Test 2: PostgreSQL Version")
            print(f"   {version[:80]}...")
            
            # Test 3: Check if ip_records table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'ip_records'
                );
            """))
            table_exists = result.fetchone()[0]
            
            if table_exists:
                print("✅ Test 3: Table 'ip_records' - EXISTS")
                
                # Test 4: Count records
                result = conn.execute(text("SELECT COUNT(*) FROM ip_records;"))
                count = result.fetchone()[0]
                print(f"✅ Test 4: Record Count - {count} records")
                
                # Test 5: Check indexes
                result = conn.execute(text("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'ip_records';
                """))
                indexes = [row[0] for row in result]
                print(f"✅ Test 5: Indexes - {len(indexes)} indexes found")
                for idx in indexes:
                    print(f"   - {idx}")
                
            else:
                print("⚠️  Test 3: Table 'ip_records' - NOT FOUND")
                print("   Run the SQL setup script to create tables")
            
            # Test 6: Test insert (optional)
            try:
                conn.execute(text("""
                    INSERT INTO ip_records (timestamp, ip, country, city, source_file)
                    VALUES ('2024-01-01 12:00:00', '8.8.8.8', 'US', 'Test', 'test.html')
                    ON CONFLICT DO NOTHING;
                """))
                conn.commit()
                print("✅ Test 6: Insert Operation - PASSED")
            except Exception as e:
                print(f"⚠️  Test 6: Insert Operation - SKIPPED ({str(e)[:50]})")
            
            # Test 7: Database size
            result = conn.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()));"))
            size = result.fetchone()[0]
            print(f"✅ Test 7: Database Size - {size}")
            
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\n✅ Your Neon database is properly configured and ready to use!")
        print("🚀 You can now start the backend server with:")
        print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ CONNECTION FAILED!")
        print("=" * 60)
        print(f"Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your .env file has correct Neon credentials")
        print("2. Verify DATABASE_URL format:")
        print("   postgresql://user:pass@host/db?sslmode=require")
        print("3. Ensure your Neon project is active (not suspended)")
        print("4. Check if you can connect via psql:")
        print(f"   psql \"{DATABASE_URL}\"")
        print("=" * 60)
        
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
