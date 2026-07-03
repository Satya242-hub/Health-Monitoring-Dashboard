"""
Database engine and session setup.

Defaults to a local SQLite file so the app runs instantly with zero setup.
Point DATABASE_URL at Postgres for production - SQLAlchemy's async layer
means no application code changes are needed, only the connection string
and driver.

  Dev (default):   sqlite+aiosqlite:///./health.db
  Prod (Postgres): postgresql+asyncpg://user:password@host:5432/providence
"""
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./health.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_async_engine(DATABASE_URL, echo=False, connect_args=connect_args)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
