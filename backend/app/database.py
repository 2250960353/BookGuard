from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with engine.begin() as conn:
        result = await conn.execute(text("PRAGMA table_info(pages)"))
        columns = {row[1] for row in result.fetchall()}
        if "is_reviewed" not in columns:
            await conn.execute(text("ALTER TABLE pages ADD COLUMN is_reviewed BOOLEAN DEFAULT 0"))
        if "is_deleted" not in columns:
            await conn.execute(text("ALTER TABLE pages ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))
            await conn.execute(text("ALTER TABLE pages ADD COLUMN deleted_at DATETIME NULL"))
    async with engine.begin() as conn:
        result = await conn.execute(text("PRAGMA table_info(books)"))
        columns = {row[1] for row in result.fetchall()}
        if "is_deleted" not in columns:
            await conn.execute(text("ALTER TABLE books ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))
            await conn.execute(text("ALTER TABLE books ADD COLUMN deleted_at DATETIME NULL"))
    async with async_session() as session:
        from sqlalchemy import select
        from app.models.models import User
        from app.auth import get_password_hash
        result = await session.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            session.add(User(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                real_name="系统管理员",
                role="admin",
            ))
            await session.commit()
