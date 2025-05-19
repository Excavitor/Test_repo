from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime # Ensure datetime is imported for type hints
from typing import Optional, List
from app.models import Role

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=150)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: Role = Role.CUSTOMER # Default role

class UserResponse(UserBase):
    id: int
    role: Role

    class Config:
        from_attributes = True # Changed from orm_mode for Pydantic v2, or keep orm_mode = True for v1

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    # role: Optional[Role] = None # If role is also in token

# --- Book Schemas ---
class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    publisher_id: int

class BookCreate(BookBase):
    pass

class Book(BookBase): # For response
    id: int
    write_date: datetime

    class Config:
        from_attributes = True

# --- Author Schemas ---
class AuthorBase(BaseModel):
    name: str = Field(..., max_length=255)
    biography: Optional[str] = None
    birth_date: Optional[date] = None

class AuthorCreate(AuthorBase):
    book_id: int # Required when creating an author and associating with a book

class AuthorUpdate(BaseModel): # For partial updates of an existing author
    name: Optional[str] = Field(None, max_length=255)
    biography: Optional[str] = None
    birth_date: Optional[date] = None
    # book_id is typically not changed here. If author needs to be moved to another book,
    # it might be a delete and recreate, or a more specific operation.

class AuthorOut(AuthorBase):
    id: int
    write_date: datetime # This comes from BaseModel
    book_id: int

    class Config:
        from_attributes = True

# --- Review Schemas ---
class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5) # Example: rating between 1 and 5
    review_text: Optional[str] = None
    book_id: int

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel): # For partial updates
    rating: Optional[int] = Field(None, ge=1, le=5)
    review_text: Optional[str] = None
    # book_id: Optional[int] = None # Usually book_id is not changed for an existing review

class ReviewOut(ReviewBase):
    id: int
    user_id: int
    date_posted: datetime
    write_date: datetime
    # Optional: include user details if needed
    # user: Optional[UserResponse] = None (requires UserResponse to be defined)

    class Config:
        from_attributes = True

# --- Publisher Schemas ---
class PublisherBase(BaseModel):
    name: str = Field(..., max_length=255)
    email: EmailStr
    phone_number: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)

class PublisherCreate(PublisherBase):
    pass

class PublisherUpdate(BaseModel): # For partial updates
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)
    # book_count is managed by the system, not updated directly via API

class PublisherOut(PublisherBase):
    id: int
    book_count: int
    write_date: datetime # Added write_date to PublisherOut

    class Config:
        from_attributes = True

# Forward references if needed, for example if Book schema needs PublisherOut
# if hasattr(Book, 'model_rebuild'): # Pydantic v2+
# Book.model_rebuild()
# PublisherOut.model_rebuild()
# ReviewOut.model_rebuild()
# AuthorOut.model_rebuild()
