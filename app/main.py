from fastapi import FastAPI, Depends, HTTPException, APIRouter, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app import models, crud, schemas
from app.database import engine, SessionLocal, Base
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import (
    create_access_token, authenticate_user, get_password_hash, get_current_user,
    has_admin_permission, has_publisher_permission, has_customer_permission
)
from app.models import Role
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI()
public = APIRouter()
admin_router = APIRouter(dependencies=[Depends(has_admin_permission)])
publisher_router = APIRouter(dependencies=[Depends(has_publisher_permission)])
customer_router = APIRouter(dependencies=[Depends(has_customer_permission)])

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@public.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with SessionLocal() as session:
        yield session

# serve login page
@public.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# serve registration page
@public.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# serve dashboard (requires auth in JS)
@public.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@public.post("/register/", response_model=schemas.UserResponse)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@public.post("/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}

@public.get("/")
async def index():
    return "hello, world"

@publisher_router.post("/books/", response_model=schemas.Book)
async def create_book(book: schemas.BookCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_book(db, book)

@customer_router.get("/books/", response_model=list[schemas.Book])
async def read_books(db: AsyncSession = Depends(get_db)):
    return await crud.get_books(db)

@publisher_router.put("/books/{book_id}")
async def update_book(book_id: int, book: schemas.BookCreate, db: AsyncSession = Depends(get_db)):
    await crud.update_book(db, book_id, book)
    return {"message": "Book updated successfully"}

@publisher_router.delete("/books/{book_id}")
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    await crud.delete_book(db, book_id)
    return {"message": "Book deleted successfully"}

@publisher_router.post("/api/authors/", response_model=schemas.AuthorOut)
async def create_author(author: schemas.AuthorCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_author(db, author)

@customer_router.get("/api/authors/", response_model=list[schemas.AuthorOut])
async def list_authors(db: AsyncSession = Depends(get_db)):
    return await crud.get_authors(db)

@customer_router.post("/api/reviews/", response_model=schemas.ReviewOut)
async def create_review(
    review: schemas.ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return await crud.create_review(db, review, current_user)

@customer_router.get("/api/reviews/", response_model=list[schemas.ReviewOut])
async def list_all_reviews(db: AsyncSession = Depends(get_db)):
    return await crud.get_reviews(db)

@customer_router.put("/api/reviews/{review_id}", response_model=schemas.ReviewOut)
async def update_review(
    review_id: int,
    review: schemas.ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return await crud.update_review(db, review_id, review, current_user)

@customer_router.delete("/api/reviews/{review_id}")
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return await crud.delete_review(db, review_id, current_user)

@admin_router.post("/publishers/", response_model=schemas.PublisherOut)
async def create_publisher(publisher: schemas.PublisherCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_publisher(db, publisher)

@customer_router.get("/publishers/", response_model=list[schemas.PublisherOut])
async def list_publishers(db: AsyncSession = Depends(get_db)):
    return await crud.get_publishers(db)

app.include_router(public)
app.include_router(admin_router)
app.include_router(publisher_router)
app.include_router(customer_router)