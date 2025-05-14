from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


# app/database.py
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import sessionmaker, declarative_base # declarative_base for SQLAlchemy < 2.0
#
# DATABASE_URL = "sqlite+aiosqlite:///./test.db" # Example, use your actual DB URL (from .env)
#
# engine = create_async_engine(DATABASE_URL, echo=True) # echo=True for debugging
# SessionLocal = sessionmaker(
#     autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
# )
# Base = declarative_base()
#
# async def get_db() -> AsyncSession: # Add return type hint
#     async with SessionLocal() as session:
#         try:
#             yield session
#             await session.commit() # Commit here if all operations in request were successful
#         except Exception:
#             await session.rollback() # Rollback on error
#             raise
#         finally:
#             await session.close()