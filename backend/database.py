import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Default to SQLite for local dev; override via env (e.g., in Docker) with Postgres URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./police_app.db")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
	pass

async def get_session():
	async with AsyncSessionLocal() as session:
		yield session
