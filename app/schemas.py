from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class BookCreate(BaseModel):
    title: str

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
