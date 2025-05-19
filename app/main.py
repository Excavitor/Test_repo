from fastapi import FastAPI, Depends, HTTPException, APIRouter, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app import models, crud, schemas  # Ensure schemas is imported
from app.database import engine, SessionLocal, Base  # Ensure Base is imported
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import (
    create_access_token, authenticate_user, get_password_hash, get_current_user,
    has_admin_permission, has_publisher_permission  # Removed has_customer_permission if not used explicitly
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Optional

app = FastAPI()
public = APIRouter()  # For non-token protected HTML pages and auth endpoints

# API routers
# Admin router for operations requiring admin privileges
admin_router = APIRouter(tags=["Admin Operations"], dependencies=[Depends(has_admin_permission)])
# Publisher router for operations requiring publisher or admin privileges
publisher_router = APIRouter(tags=["Publisher Operations"], dependencies=[Depends(has_publisher_permission)])
# Customer router for general authenticated user operations (or can be more granular)
# For simplicity, let's assume most data viewing might need authentication
customer_router = APIRouter(tags=["Authenticated User Operations"], dependencies=[Depends(get_current_user)])

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with SessionLocal() as session:
        yield session


# --- HTML Serving Endpoints (on public router) ---
@public.get("/", response_class=HTMLResponse, summary="Serve Login Page")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@public.get("/register", response_class=HTMLResponse, summary="Serve Registration Page")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# Dashboard requires authentication, token will be checked by JS or a dependency
@public.get("/dashboard", response_class=HTMLResponse, summary="Serve Dashboard Page")
async def dashboard_page(request: Request):  # JS will handle token check for initial load
    return templates.TemplateResponse("dashboard.html", {"request": request})


# --- Authentication Endpoints (on public router) ---
@public.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED,
             summary="Register New User")
async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user_check = await db.execute(select(models.User).where(models.User.username == user.username))
    if existing_user_check.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    # Enforce default role or validate provided role for public registration
    # For now, using the role from input, assuming register.html controls this adequately
    # Or, enforce: user_role = models.Role.CUSTOMER
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except Exception as e:  # pragma: no cover
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration failed: {str(e)}")


@public.post("/login", response_model=schemas.Token, summary="User Login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value, "user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


# --- Book Endpoints ---
@publisher_router.post("/books", response_model=schemas.Book, status_code=status.HTTP_201_CREATED,
                       summary="Create New Book")
async def create_new_book(book: schemas.BookCreate, db: AsyncSession = Depends(get_db)):
    # current_user dependency is handled by the router
    return await crud.create_book(db, book)


@customer_router.get("/books", response_model=List[schemas.Book], summary="List All Books")
async def read_all_books(db: AsyncSession = Depends(get_db)):
    return await crud.get_books(db)


@publisher_router.put("/books/{book_id}", response_model=schemas.Book, summary="Update Book by ID")
async def update_existing_book(book_id: int, book: schemas.BookCreate, db: AsyncSession = Depends(get_db)):
    # Using BookCreate for update means all fields must be sent.
    # Consider a BookUpdate schema for partial updates if needed.
    updated_book = await crud.update_book(db, book_id, book)
    if updated_book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return updated_book


@publisher_router.delete("/books/{book_id}", status_code=status.HTTP_200_OK, summary="Delete Book by ID")
async def delete_existing_book(book_id: int, db: AsyncSession = Depends(get_db)):
    success = await crud.delete_book(db, book_id)
    if not success:  # Should be handled by HTTPException in crud if not found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found or could not be deleted")
    return {"message": "Book deleted successfully"}


# --- Author Endpoints ---
@publisher_router.post("/authors", response_model=schemas.AuthorOut, status_code=status.HTTP_201_CREATED,
                       summary="Create New Author")
async def create_new_author(author: schemas.AuthorCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_author(db, author)


@customer_router.get("/authors", response_model=List[schemas.AuthorOut], summary="List All Authors")
async def list_all_authors(book_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    return await crud.get_authors(db, book_id=book_id)


@publisher_router.put("/authors/{author_id}", response_model=schemas.AuthorOut, summary="Update Author by ID")
async def update_existing_author(author_id: int, author: schemas.AuthorUpdate, db: AsyncSession = Depends(get_db)):
    updated_author = await crud.update_author(db, author_id, author)
    if updated_author is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Author not found")
    return updated_author


@publisher_router.delete("/authors/{author_id}", status_code=status.HTTP_200_OK, summary="Delete Author by ID")
async def delete_existing_author(author_id: int, db: AsyncSession = Depends(get_db)):
    success = await crud.delete_author(db, author_id)
    if not success:  # Should be handled by HTTPException in crud if not found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Author not found or could not be deleted")
    return {"message": "Author deleted successfully"}


# --- Review Endpoints ---
@customer_router.post("/reviews", response_model=schemas.ReviewOut, status_code=status.HTTP_201_CREATED,
                      summary="Create New Review")
async def create_new_review(
        review: schemas.ReviewCreate,
        db: AsyncSession = Depends(get_db),
        current_user: models.User = Depends(get_current_user)  # Explicitly get user for ownership
):
    return await crud.create_review(db, review, current_user)


@customer_router.get("/reviews", response_model=List[schemas.ReviewOut], summary="List Reviews (optionally for a book)")
async def list_all_reviews(book_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    return await crud.get_reviews(db, book_id=book_id)


@customer_router.put("/reviews/{review_id}", response_model=schemas.ReviewOut, summary="Update Review by ID")
async def update_existing_review(
        review_id: int,
        review: schemas.ReviewUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: models.User = Depends(get_current_user)  # Auth check in CRUD
):
    return await crud.update_review(db, review_id, review, current_user)


@customer_router.delete("/reviews/{review_id}", status_code=status.HTTP_200_OK, summary="Delete Review by ID")
async def delete_existing_review(
        review_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: models.User = Depends(get_current_user)  # Auth check in CRUD
):
    result = await crud.delete_review(db, review_id, current_user)  # Returns a dict
    return result


# --- Publisher Endpoints ---
@admin_router.post("/publishers", response_model=schemas.PublisherOut, status_code=status.HTTP_201_CREATED,
                   summary="Create New Publisher")
async def create_new_publisher(publisher: schemas.PublisherCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_publisher(db, publisher)


@customer_router.get("/publishers", response_model=List[schemas.PublisherOut], summary="List All Publishers")
async def list_all_publishers(db: AsyncSession = Depends(get_db)):
    return await crud.get_publishers(db)


@admin_router.put("/publishers/{publisher_id}", response_model=schemas.PublisherOut, summary="Update Publisher by ID")
async def update_existing_publisher(publisher_id: int, publisher: schemas.PublisherUpdate,
                                    db: AsyncSession = Depends(get_db)):
    updated_publisher = await crud.update_publisher(db, publisher_id, publisher)
    if updated_publisher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publisher not found")
    return updated_publisher


@admin_router.delete("/publishers/{publisher_id}", status_code=status.HTTP_200_OK, summary="Delete Publisher by ID")
async def delete_existing_publisher(publisher_id: int, db: AsyncSession = Depends(get_db)):
    success = await crud.delete_publisher(db, publisher_id)
    if not success:  # Should be handled by HTTPException in crud
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publisher not found or could not be deleted")
    return JSONResponse(content={"message": "Publisher deleted successfully"})


app.include_router(public)
app.include_router(admin_router, prefix="/api/v1")
app.include_router(publisher_router, prefix="/api/v1")
app.include_router(customer_router, prefix="/api/v1")