"""
Migration Script - Add missing column to fir_cases table
Adds total_investigations column to existing fir_cases table
"""
import asyncio
from sqlalchemy import text
from database import engine, DATABASE_URL


async def migrate_fir_cases():
    """Add missing column to fir_cases table"""
    print("🔧 Migrating fir_cases table...")
    print(f"📍 Database: {DATABASE_URL.split('@')[0] if '@' in DATABASE_URL else 'SQLite'}")
    
    try:
        async with engine.begin() as conn:
            # Check if column exists
            is_sqlite = 'sqlite' in DATABASE_URL.lower()
            
            if is_sqlite:
                # SQLite: Check if column exists
                result = await conn.execute(text("PRAGMA table_info(fir_cases)"))
                columns = result.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'total_investigations' not in column_names:
                    print("➕ Adding total_investigations column...")
                    await conn.execute(text(
                        "ALTER TABLE fir_cases ADD COLUMN total_investigations INTEGER DEFAULT 0"
                    ))
                    print("✅ Column added successfully!")
                else:
                    print("✅ Column already exists")
            else:
                # PostgreSQL: Check if column exists
                result = await conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='fir_cases' AND column_name='total_investigations'
                """))
                
                if not result.fetchone():
                    print("➕ Adding total_investigations column...")
                    await conn.execute(text(
                        "ALTER TABLE fir_cases ADD COLUMN total_investigations INTEGER DEFAULT 0"
                    ))
                    print("✅ Column added successfully!")
                else:
                    print("✅ Column already exists")
            
            print("\n🎉 Migration complete!")
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("FIR CASES TABLE MIGRATION")
    print("=" * 60)
    
    try:
        asyncio.run(migrate_fir_cases())
        
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETE!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        exit(1)
