from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
# import asyncio
from Test_repo.app import models, crud, schemas
from Test_repo.app.database import engine, SessionLocal

app = FastAPI()

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()

async def get_db():
    async with SessionLocal() as session:
        yield session

@app.post("/books/", response_model=schemas.Book)
async def create_book(book: schemas.BookCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_book(db, book)

@app.get("/books/", response_model=list[schemas.Book])
async def read_books(db: AsyncSession = Depends(get_db)):
    return await crud.get_books(db)
