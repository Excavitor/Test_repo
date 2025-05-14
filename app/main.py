from fastapi import FastAPI, Depends, HTTPException, APIRouter, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app import models, crud, schemas
from app.database import engine, SessionLocal, Base
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import (
    create_access_token, authenticate_user, get_password_hash, get_current_user,
    has_admin_permission, has_publisher_permission, has_customer_permission
)
# from app.models import Role # Role is now primarily in models, used by auth dependencies
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI()
public = APIRouter()
api_router = APIRouter(prefix="/api/v1") # Optional: Centralize data APIs under a prefix

# Routers with role-based dependencies
# It's good practice to prefix API routes, e.g., /api/v1/admin, /api/v1/publisher etc.
# For this fix, I'm keeping existing route structures but adding response_model where appropriate.
admin_router = APIRouter(dependencies=[Depends(has_admin_permission)], tags=["Admin"])
publisher_router = APIRouter(dependencies=[Depends(has_publisher_permission)], tags=["Publisher"])
customer_router = APIRouter(dependencies=[Depends(has_customer_permission)], tags=["Customer"])


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with SessionLocal() as session:
        yield session

# --- HTML Serving Endpoints ---
@public.get("/", response_class=HTMLResponse, summary="Serve Login Page")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@public.get("/register", response_class=HTMLResponse, summary="Serve Registration Page")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@public.get("/dashboard", response_class=HTMLResponse, summary="Serve Dashboard Page")
async def dashboard_page(request: Request): # This page will handle auth check via JS
    return templates.TemplateResponse("dashboard.html", {"request": request})

# --- Authentication Endpoints ---
@public.post("/register", response_model=schemas.UserResponse, status_code=201, summary="Register New User")
async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    # existing_user = await db.execute(models.User.select().where(models.User.username == user.username))
    existing_user = await db.execute(select(models.User).where(models.User.username == user.username))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    # Ensure role from user.role is used, not a fixed one, unless intended
    db_user = models.User(username=user.username, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    # await db.commit()
    # await db.refresh(db_user)
    # return db_user
    try:
        await db.commit()
        await db.refresh(db_user)  # Refresh to get the generated ID
        return db_user
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@public.post("/login", response_model=schemas.Token, summary="User Login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, # Corrected status code for login failure
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Book Endpoints ---
# Consider prefixing these with /api/v1 for consistency, e.g., /api/v1/books/
@publisher_router.post("/books", response_model=schemas.Book, status_code=201, summary="Create New Book")
async def create_new_book(book: schemas.BookCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_book(db, book)

@customer_router.get("/books", response_model=list[schemas.Book], summary="List All Books")
async def read_all_books(db: AsyncSession = Depends(get_db)):
    return await crud.get_books(db)

@publisher_router.put("/books/{book_id}", response_model=schemas.Book, summary="Update Book by ID")
async def update_existing_book(book_id: int, book: schemas.BookCreate, db: AsyncSession = Depends(get_db)):
    updated_book = await crud.update_book(db, book_id, book)
    if updated_book is None:
        raise HTTPException(status_code=404, detail="Book not found") # status 204 often used for no content
    return updated_book

@publisher_router.delete("/books/{book_id}", status_code=200, summary="Delete Book by ID")
async def delete_existing_book(book_id: int, db: AsyncSession = Depends(get_db)):
    await crud.delete_book(db, book_id) # crud.delete_book raises HTTPException if not found
    return {"message": "Book deleted successfully"} # Or return status.HTTP_204_NO_CONTENT with no body

# --- Author Endpoints ---
# These are already prefixed with /api. Good.
@publisher_router.post("/api/authors", response_model=schemas.AuthorOut, status_code=201, summary="Create New Author")
async def create_new_author(author: schemas.AuthorCreate, db: AsyncSession = Depends(get_db)):
    # Potential issue: The current model links an Author to a single Book.
    # If an Author can write multiple books, a many-to-many relationship is needed.
    return await crud.create_author(db, author)

@customer_router.get("/api/authors", response_model=list[schemas.AuthorOut], summary="List All Authors")
async def list_all_authors(db: AsyncSession = Depends(get_db)):
    return await crud.get_authors(db)

# --- Review Endpoints ---
@customer_router.post("/api/reviews", response_model=schemas.ReviewOut, status_code=201, summary="Create New Review")
async def create_new_review(
    review: schemas.ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return await crud.create_review(db, review, current_user)

@customer_router.get("/api/reviews", response_model=list[schemas.ReviewOut], summary="List All Reviews")
async def list_all_reviews_for_book(book_id: int = None, db: AsyncSession = Depends(get_db)): # Added optional book_id filter
    return await crud.get_reviews(db, book_id=book_id)

@customer_router.put("/api/reviews/{review_id}", response_model=schemas.ReviewOut, summary="Update Review by ID")
async def update_existing_review(
    review_id: int,
    review: schemas.ReviewUpdate, # Should be ReviewUpdate if partial updates are allowed, or ReviewCreate
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return await crud.update_review(db, review_id, review, current_user)

@customer_router.delete("/api/reviews/{review_id}", status_code=200, summary="Delete Review by ID")
async def delete_existing_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await crud.delete_review(db, review_id, current_user)
    return result

# --- Publisher Endpoints ---
@admin_router.post("/publishers", response_model=schemas.PublisherOut, status_code=201, summary="Create New Publisher")
async def create_new_publisher(publisher: schemas.PublisherCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_publisher(db, publisher)

@customer_router.get("/publishers", response_model=list[schemas.PublisherOut], summary="List All Publishers")
async def list_all_publishers(db: AsyncSession = Depends(get_db)):
    return await crud.get_publishers(db)

app.include_router(public) # For HTML pages and auth
# Include other routers. If you adopt /api/v1 prefix in routers, adjust here.
app.include_router(admin_router, prefix="/api/v1") # Example prefixing
app.include_router(publisher_router, prefix="/api/v1") # Example prefixing
app.include_router(customer_router, prefix="/api/v1") # Example prefixing

# If not using the /api/v1 prefix in the router definitions:
# app.include_router(admin_router)
# app.include_router(publisher_router)
# app.include_router(customer_router)