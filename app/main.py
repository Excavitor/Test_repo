from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import models, crud, schemas
from app.database import engine, SessionLocal, Base
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import create_access_token, authenticate_user, get_password_hash, get_current_user

app = FastAPI()

@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with SessionLocal() as session:
        yield session

@app.get("/secure-data/")
async def secure_route(current_user: models.User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.username}, you are authenticated!"}


@app.post("/register/")
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    return {"message": "User created"}

@app.post("/token", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}



# @app.get("/")
# async def index():
#     return "hello, world"

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


@app.get("/api/books/reviews/", response_model=list[schemas.ReviewOut])
async def list_reviews_by_book(book_id: int = None, db: AsyncSession = Depends(get_db)):
    reviews = await crud.get_reviews(db, book_id)
    return reviews


@app.get("/api/reviews/", response_model=list[schemas.ReviewOut])
async def list_all_reviews(db: AsyncSession = Depends(get_db)):
    return await crud.get_reviews(db)
