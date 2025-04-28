from pydantic import BaseModel
from datetime import date

class BookCreate(BaseModel):
    title: str
    author: str
    published_date: date

class Book(BookCreate):
    id: int

    class Config:
        orm_mode = True
