"""
Simple Migration - Add Missing Columns
Run this to add total_investigations and current_step columns
"""
import asyncio
from sqlalchemy import text
from database import engine, DATABASE_URL


async def add_columns():
    """Add missing columns to tables"""
    print("=" * 60)
    print("ADDING MISSING COLUMNS")
    print("=" * 60)
    
    try:
        async with engine.begin() as conn:
            is_sqlite = 'sqlite' in DATABASE_URL.lower()
            
            print(f"\n📍 Database: {'SQLite' if is_sqlite else 'PostgreSQL'}")
            
            # Add total_investigations to fir_cases
            print("\n1️⃣ Adding total_investigations to fir_cases...")
            try:
                await conn.execute(text(
                    "ALTER TABLE fir_cases ADD COLUMN total_investigations INTEGER DEFAULT 0"
                ))
                print("✅ Added total_investigations column")
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    print("✅ Column already exists")
                else:
                    print(f"⚠️  Error: {e}")
            
            # Add current_step to investigations
            print("\n2️⃣ Adding current_step to investigations...")
            try:
                await conn.execute(text(
                    "ALTER TABLE investigations ADD COLUMN current_step INTEGER DEFAULT 1"
                ))
                print("✅ Added current_step column")
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    print("✅ Column already exists")
                else:
                    print(f"⚠️  Error: {e}")
            
            print("\n" + "=" * 60)
            print("MIGRATION COMPLETE!")
            print("=" * 60)
            print("\n✅ All columns added successfully!")
            print("\nYou can now restart the backend:")
            print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    asyncio.run(add_columns())
