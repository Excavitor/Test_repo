from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Enum as DBEnum # Renamed Enum to avoid clash
from sqlalchemy.orm import relationship
from datetime import datetime, timezone # Added timezone
from app.database import Base
import enum # Python's enum module

# Define Role enum here as the single source of truth
class Role(str, enum.Enum):
    ADMIN = "admin"
    PUBLISHER = "publisher"
    CUSTOMER = "customer"

class BaseModel(Base):
    __abstract__ = True
    # Using lambda for default ensures the function is called at the time of insert/update
    write_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class User(Base):
    # __tablename__ = "public" # MISTAKE: "public" is often a schema name. Changed to "users".
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    # Use the Role enum defined in this file
    role = Column(DBEnum(Role), default=Role.CUSTOMER, nullable=False)

    reviews = relationship("Review", back_populates="user")

class Book(BaseModel):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True, index=True) # Added index=True for primary key
    title = Column(String(255), nullable=False)
    publisher_id = Column(Integer, ForeignKey('publishers.id'), nullable=False)

    publisher = relationship("Publisher", back_populates="books")
    # If an Author can write multiple books, this relationship needs to be many-to-many
    # Current setup: A Book has multiple 'Author' entries, each 'Author' entry belongs to this one Book.
    authors = relationship("Author", back_populates="book", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")

class Author(BaseModel):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    biography = Column(Text, nullable=True)
    birth_date = Column(Date, nullable=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    book = relationship("Book", back_populates="authors")

class Review(BaseModel):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Integer, nullable=False)
    review_text = Column(Text, nullable=True)
    date_posted = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)) # Timezone aware

    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    book = relationship("Book", back_populates="reviews")

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="reviews")

class Publisher(BaseModel):
    __tablename__ = "publishers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(50), nullable=False)
    website = Column(String(255), nullable=True)
    book_count = Column(Integer, default=0, nullable=False)
    books = relationship("Book", back_populates="publisher", cascade="all, delete-orphan")