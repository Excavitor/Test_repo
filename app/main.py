from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import models, crud, schemas
from app.database import engine, SessionLocal, Base

app = FastAPI()

@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with SessionLocal() as session:
        yield session

@app.get("/")
async def index():
    return "hello, world"


@app.post("/books/", response_model=schemas.Book)
async def create_book(book: schemas.BookCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_book(db, book)


@app.get("/books/", response_model=list[schemas.Book])
async def read_books(db: AsyncSession = Depends(get_db)):
    return await crud.get_books(db)


@app.put("/books/{book_id}")
async def update_book(book_id: int, book: schemas.BookCreate, db: AsyncSession = Depends(get_db)):
    await crud.update_book(db, book_id, book)
    return {"message": "Book updated successfully"}


@app.delete("/books/{book_id}")
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    await crud.delete_book(db, book_id)
    return {"message": "Book deleted successfully"}


@app.post("/api/authors/", response_model=schemas.AuthorOut)
async def create_author(author: schemas.AuthorCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_author(db, author)


@app.get("/api/authors/", response_model=list[schemas.AuthorOut])
async def list_authors(db: AsyncSession = Depends(get_db)):
    return await crud.get_authors(db)


@app.post("/api/reviews/", response_model=schemas.ReviewOut)
async def create_review(review: schemas.ReviewCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_review(db, review)


@app.get("/api/books/{book_id}/reviews/", response_model=list[schemas.ReviewOut])
async def list_reviews_by_book(book_id: int, db: AsyncSession = Depends(get_db)):
    reviews = await crud.get_reviews(db, book_id)
    return reviews


@app.get("/api/reviews/", response_model=list[schemas.ReviewOut])
async def list_all_reviews(db: AsyncSession = Depends(get_db)):
    return await crud.get_reviews(db)
