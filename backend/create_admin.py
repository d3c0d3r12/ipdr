#!/usr/bin/env python3
"""
Create default admin user for IPDR Tracking
"""
import asyncio
import sys
from datetime import datetime
import hashlib
import secrets
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
import os
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ipdr_tracking.db")

async def create_admin_user():
    """Create admin user in database"""
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        # Create tables first
        from database import Base
        await conn.run_sync(Base.metadata.create_all)
    
    # Now insert the admin user
    async with AsyncSessionLocal() as session:
        username = "admin"
        email = "admin@localhost"
        password = "Admin@123456"
        
        # Hash password with salt (PBKDF2-HMAC-SHA256, same as AuthService)
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        
        # Insert admin user
        insert_sql = text("""
            INSERT INTO users (username, email, password_hash, salt, full_name, role, is_active, created_at)
            VALUES (:username, :email, :password_hash, :salt, :full_name, :role, :is_active, :created_at)
        """)
        
        try:
            await session.execute(insert_sql, {
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "salt": salt,
                "full_name": "Administrator",
                "role": "admin",
                "is_active": True,
                "created_at": datetime.utcnow()
            })
            await session.commit()
            print(f"✅ Admin user created successfully!")
            print(f"   Username: {username}")
            print(f"   Password: {password}")
            print(f"   Email: {email}")
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                print(f"⚠️  Admin user already exists")
            else:
                print(f"❌ Error creating admin user: {e}")
                await session.rollback()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_admin_user())
