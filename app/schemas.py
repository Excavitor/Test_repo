from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    PUBLISHER = "publisher"
    CUSTOMER = "customer"

class UserCreate(BaseModel):
    username: str
    password: str
    role: Role = Role.CUSTOMER

class UserResponse(BaseModel):
    id: int
    username: str
    role: Role

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str


class BookCreate(BaseModel):
    title: str
    publisher_id: int

class Book(BookCreate):
    id: int
    write_date: datetime

    class Config:
        orm_mode = True

class AuthorCreate(BaseModel):
    name: str
    biography: Optional[str] = None
    birth_date: Optional[date] = None
    book_id: int

class AuthorOut(AuthorCreate):
    id: int
    write_date: datetime

    class Config:
        orm_mode = True

class ReviewCreate(BaseModel):
    rating: int
    review_text: Optional[str] = None
    book_id: int

class ReviewOut(ReviewCreate):
    id: int
    date_posted: datetime
    write_date: datetime

    class Config:
        orm_mode = True

class PublisherCreate(BaseModel):
    name: str
    email: EmailStr
    phone_number: Optional[str] = None
    website: Optional[str] = None

class PublisherOut(PublisherCreate):
    id: int
    book_count: int

    class Config:
        orm_mode = True