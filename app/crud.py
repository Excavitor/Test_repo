from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete
from app import models, schemas  # Import base models and schemas
from datetime import datetime, timezone
from fastapi import HTTPException
from typing import List, Optional


# --- Book CRUD ---
async def create_book(db: AsyncSession, book_in: schemas.BookCreate) -> models.Book:
    publisher = await db.get(models.Publisher, book_in.publisher_id)
    if not publisher:
        raise HTTPException(status_code=404, detail=f"Publisher with id {book_in.publisher_id} not found")

    new_book = models.Book(title=book_in.title, publisher_id=book_in.publisher_id)
    db.add(new_book)

    publisher.book_count += 1
    # db.add(publisher) # SQLAlchemy tracks changes to managed objects

    await db.commit()
    await db.refresh(new_book)
    # Eager load publisher if needed for the response, though Book schema doesn't include it by default
    # await db.refresh(publisher)
    return new_book


async def get_books(db: AsyncSession) -> List[models.Book]:
    result = await db.execute(select(models.Book))
    return result.scalars().all()


async def get_book(db: AsyncSession, book_id: int) -> Optional[models.Book]:
    return await db.get(models.Book, book_id)


async def update_book(db: AsyncSession, book_id: int, book_update: schemas.BookCreate) -> Optional[models.Book]:
    book = await db.get(models.Book, book_id)
    if not book:
        return None  # Will be handled as 404 in main.py

    # Handle publisher change and book counts
    if book.publisher_id != book_update.publisher_id:
        # Decrement count for the old publisher if it exists
        if book.publisher_id:
            old_publisher = await db.get(models.Publisher, book.publisher_id)
            if old_publisher and old_publisher.book_count > 0:
                old_publisher.book_count -= 1
                # db.add(old_publisher)

        # Increment count for the new publisher
        new_publisher = await db.get(models.Publisher, book_update.publisher_id)
        if not new_publisher:
            # This case should ideally be caught by schema if publisher_id is always required and valid
            raise HTTPException(status_code=404, detail=f"New Publisher ID {book_update.publisher_id} not found.")
        new_publisher.book_count += 1
        # db.add(new_publisher)
        book.publisher_id = book_update.publisher_id

    book.title = book_update.title
    # book.write_date is handled by the model's onupdate

    # db.add(book) # SQLAlchemy tracks changes
    await db.commit()
    await db.refresh(book)
    return book


async def delete_book(db: AsyncSession, book_id: int) -> bool:
    book_to_delete = await db.get(models.Book, book_id)
    if not book_to_delete:
        raise HTTPException(status_code=404, detail="Book not found")

    # Decrement publisher count if publisher exists
    if book_to_delete.publisher_id:
        publisher = await db.get(models.Publisher, book_to_delete.publisher_id)
        if publisher and publisher.book_count > 0:
            publisher.book_count -= 1
            # db.add(publisher)

    # Authors and Reviews associated with this book will be deleted due to
    # cascade="all, delete-orphan" in Book model relationships
    await db.delete(book_to_delete)
    await db.commit()
    return True


# --- Author CRUD ---
async def create_author(db: AsyncSession, author_in: schemas.AuthorCreate) -> models.Author:
    book = await db.get(models.Book, author_in.book_id)
    if not book:
        raise HTTPException(status_code=404, detail=f"Book with id {author_in.book_id} not found for author.")

    new_author = models.Author(
        name=author_in.name,
        biography=author_in.biography,
        birth_date=author_in.birth_date,
        book_id=author_in.book_id
    )
    db.add(new_author)
    await db.commit()
    await db.refresh(new_author)
    return new_author


async def get_authors(db: AsyncSession, book_id: Optional[int] = None) -> List[models.Author]:
    query = select(models.Author)
    if book_id:
        # If you want to fetch authors for a specific book
        query = query.where(models.Author.book_id == book_id)
    result = await db.execute(query)
    return result.scalars().all()


async def get_author(db: AsyncSession, author_id: int) -> Optional[models.Author]:
    return await db.get(models.Author, author_id)


async def update_author(db: AsyncSession, author_id: int, author_in: schemas.AuthorUpdate) -> Optional[models.Author]:
    author = await db.get(models.Author, author_id)
    if not author:
        return None  # Will be 404 in main.py

    update_data = author_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(author, key, value)

    # author.write_date is handled by the model's onupdate
    # db.add(author) # SQLAlchemy tracks changes
    await db.commit()
    await db.refresh(author)
    return author


async def delete_author(db: AsyncSession, author_id: int) -> bool:
    author = await db.get(models.Author, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    # Deleting an author directly. The association with book is on the Author model.
    # Cascade delete from Book to Author might also handle this if a book is deleted.
    await db.delete(author)
    await db.commit()
    return True


# --- Review CRUD ---
async def create_review(db: AsyncSession, review_in: schemas.ReviewCreate, current_user: models.User) -> models.Review:
    book = await db.get(models.Book, review_in.book_id)
    if not book:
        raise HTTPException(status_code=404, detail=f"Book with id {review_in.book_id} not found for review.")

    new_review = models.Review(
        rating=review_in.rating,
        review_text=review_in.review_text,
        date_posted=datetime.now(timezone.utc),
        book_id=review_in.book_id,
        user_id=current_user.id
    )
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    return new_review


async def get_reviews(db: AsyncSession, book_id: Optional[int] = None) -> List[models.Review]:
    query = select(models.Review)
    if book_id:
        query = query.where(models.Review.book_id == book_id)
    result = await db.execute(query)
    return result.scalars().all()


async def update_review(db: AsyncSession, review_id: int, review_update: schemas.ReviewUpdate,
                        current_user: models.User) -> Optional[models.Review]:
    review = await db.get(models.Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user.id and current_user.role != models.Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to update this review")

    update_data = review_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(review, key, value)

    # review.write_date handled by model
    # db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


async def delete_review(db: AsyncSession, review_id: int, current_user: models.User) -> dict:
    review = await db.get(models.Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user.id and current_user.role != models.Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")

    await db.delete(review)
    await db.commit()
    return {"detail": "Review deleted successfully"}


# --- Publisher CRUD ---
async def create_publisher(db: AsyncSession, publisher_in: schemas.PublisherCreate) -> models.Publisher:
    existing_publisher_by_name = await db.execute(
        select(models.Publisher).where(models.Publisher.name == publisher_in.name))
    if existing_publisher_by_name.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Publisher name already exists")

    existing_publisher_by_email = await db.execute(
        select(models.Publisher).where(models.Publisher.email == publisher_in.email))
    if existing_publisher_by_email.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Publisher email already exists")

    new_publisher = models.Publisher(
        name=publisher_in.name,
        email=publisher_in.email,
        phone_number=publisher_in.phone_number,
        website=publisher_in.website,
        book_count=0
    )
    db.add(new_publisher)
    await db.commit()
    await db.refresh(new_publisher)
    return new_publisher


async def get_publishers(db: AsyncSession) -> List[models.Publisher]:
    result = await db.execute(select(models.Publisher))
    return result.scalars().all()


async def get_publisher(db: AsyncSession, publisher_id: int) -> Optional[models.Publisher]:
    return await db.get(models.Publisher, publisher_id)


async def update_publisher(db: AsyncSession, publisher_id: int, publisher_in: schemas.PublisherUpdate) -> Optional[
    models.Publisher]:
    publisher = await db.get(models.Publisher, publisher_id)
    if not publisher:
        return None  # Will be 404 in main.py

    update_data = publisher_in.model_dump(exclude_unset=True)

    # Check for uniqueness if name or email is being updated
    if "name" in update_data and update_data["name"] != publisher.name:
        existing = await db.execute(select(models.Publisher).where(models.Publisher.name == update_data["name"]))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Publisher name already exists.")

    if "email" in update_data and update_data["email"] != publisher.email:
        existing = await db.execute(select(models.Publisher).where(models.Publisher.email == update_data["email"]))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Publisher email already exists.")

    for key, value in update_data.items():
        setattr(publisher, key, value)

    # publisher.write_date handled by model
    # db.add(publisher)
    await db.commit()
    await db.refresh(publisher)
    return publisher


async def delete_publisher(db: AsyncSession, publisher_id: int) -> bool:
    publisher = await db.get(models.Publisher, publisher_id)
    if not publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")

    # IMPORTANT: The Publisher model has `books = relationship("Book", ..., cascade="all, delete-orphan")`.
    # This means deleting a publisher will delete all its associated books.
    # If this is not desired, you might want to:
    # 1. Check if publisher.books is empty before allowing deletion.
    # 2. Or, change the cascade behavior in models.py (e.g., set books' publisher_id to null if allowed, or prevent delete).
    # For this implementation, we proceed with the cascade delete.

    # If you want to prevent deletion if books exist:
    # if publisher.books: # This requires eager/lazy loading of publisher.books
    #     # For async, you might need to query the count
    #     book_count_result = await db.execute(select(func.count(models.Book.id)).where(models.Book.publisher_id == publisher_id))
    #     book_count = book_count_result.scalar_one()
    #     if book_count > 0:
    #         raise HTTPException(status_code=400, detail=f"Cannot delete publisher: Publisher has {book_count} associated books. Please reassign or delete them first.")

    await db.delete(publisher)
    await db.commit()
    return True