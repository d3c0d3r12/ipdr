"""
Database Initialization Script
Creates all tables and sets up initial admin user
"""

from core.db import engine, Base, SessionLocal
from models.user_auth import User, UserSession, UserActivity, LoginAttempt, AccessLog, UserPermission
from models.fir_case import FIRCase, FIRIPLookup, FIREvidence, FIRSuspect, FIRTimeline
from services.auth_service import AuthService
import sys


def init_database():
    """Initialize database with all tables"""
    
    print("🔧 Initializing database...")
    
    # Create all tables
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    # Create initial admin user
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        
        if not admin:
            print("\n👤 Creating initial admin user...")
            
            # Create admin
            admin, message = AuthService.create_user(
                db=db,
                username="admin",
                email="admin@delhipolice.gov.in",
                password="Admin@123456",  # CHANGE THIS IN PRODUCTION!
                full_name="System Administrator",
                role="admin"
            )
            
            if admin:
                admin.is_verified = True
                admin.is_active = True
                admin.department = "Delhi Police Cyber Cell"
                admin.designation = "System Administrator"
                db.commit()
                
                print("✅ Admin user created successfully!")
                print(f"   Username: admin")
                print(f"   Password: Admin@123456")
                print(f"   ⚠️  PLEASE CHANGE THIS PASSWORD IMMEDIATELY!")
            else:
                print(f"❌ Failed to create admin: {message}")
        else:
            print("ℹ️  Admin user already exists")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.close()
        return False


def create_sample_data():
    """Create sample FIR case for testing"""
    
    db = SessionLocal()
    try:
        print("\n📋 Creating sample FIR case...")
        
        from services.fir_service import FIRService
        
        # Check if sample FIR exists
        existing = FIRService.get_fir_case(db, "FIR/2025/SAMPLE/001")
        
        if not existing:
            fir_case, message = FIRService.create_fir_case(
                db=db,
                fir_number="FIR/2025/SAMPLE/001",
                case_title="Sample Cybercrime Investigation",
                case_description="This is a sample FIR case for testing purposes",
                investigating_officer="Admin",
                department="Delhi Police Cyber Cell",
                priority="medium",
                created_by="admin"
            )
            
            if fir_case:
                print(f"✅ Sample FIR created: {fir_case.fir_number}")
            else:
                print(f"❌ Failed to create sample FIR: {message}")
        else:
            print("ℹ️  Sample FIR already exists")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.close()


if __name__ == "__main__":
    print("=" * 70)
    print("  IPDR TRACKING HUB - DATABASE INITIALIZATION")
    print("  Delhi Police Cyber Cell")
    print("=" * 70)
    print()
    
    # Initialize database
    success = init_database()
    
    if success:
        # Create sample data
        create_sample = input("\n📋 Create sample FIR case for testing? (y/n): ")
        if create_sample.lower() == 'y':
            create_sample_data()
        
        print("\n" + "=" * 70)
        print("✅ Database initialization complete!")
        print("=" * 70)
        print()
        print("📝 Next steps:")
        print("   1. Change the admin password")
        print("   2. Start the backend server: uvicorn main:app --reload")
        print("   3. Access API docs: http://localhost:8000/docs")
        print("   4. Login with admin credentials")
        print()
    else:
        print("\n" + "=" * 70)
        print("❌ Database initialization failed!")
        print("=" * 70)
        sys.exit(1)
