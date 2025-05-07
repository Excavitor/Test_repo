from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum

class Role(str, enum.Enum):
    ADMIN = "admin"
    PUBLISHER = "publisher"
    CUSTOMER = "customer"

class BaseModel(Base):
    __abstract__ = True
    write_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base):
    __tablename__ = "public"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(Role), default=Role.CUSTOMER, nullable=False)


class Book(BaseModel):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    publisher_id = Column(Integer, ForeignKey('publishers.id'), nullable=True)
    publisher = relationship("Publisher", back_populates="books")
    authors = relationship("Author", back_populates="book", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")

class Author(BaseModel):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    biography = Column(Text)
    birth_date = Column(Date)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    book = relationship("Book", back_populates="authors")

class Review(BaseModel):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    rating = Column(Integer, nullable=False)
    review_text = Column(Text)
    date_posted = Column(DateTime, default=datetime.utcnow)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    book = relationship("Book", back_populates="reviews")

class Publisher(BaseModel):
    __tablename__ = "publishers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone_number = Column(Integer, nullable=True)
    website = Column(String(255), nullable=True)
    book_count = Column(Integer, default=0, nullable=False)
    books = relationship("Book", back_populates="publisher", cascade="all, delete-orphan")
