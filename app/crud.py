from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete
from app import models, schemas  # Import base models and schemas
from datetime import datetime, timezone
from fastapi import HTTPException
from typing import List, Optional


# --- Book CRUD ---
async def create_book(db: AsyncSession, book_in: schemas.BookCreate) -> models.Book:
    # Check if publisher exists if publisher_id is provided
    if book_in.publisher_id:
        publisher = await db.get(models.Publisher, book_in.publisher_id)
        if not publisher:
            raise HTTPException(status_code=404, detail=f"Publisher with id {book_in.publisher_id} not found")

    new_book = models.Book(title=book_in.title, publisher_id=book_in.publisher_id)
    db.add(new_book)

    # Increment publisher's book_count if publisher exists
    if book_in.publisher_id and 'publisher' in locals() and publisher:  # ensure publisher was fetched
        publisher.book_count += 1
        db.add(publisher)

    await db.commit()
    await db.refresh(new_book)
    return new_book


async def get_books(db: AsyncSession) -> List[models.Book]:
    result = await db.execute(select(models.Book))
    return result.scalars().all()


async def get_book(db: AsyncSession, book_id: int) -> Optional[models.Book]:
    return await db.get(models.Book, book_id)


async def update_book(db: AsyncSession, book_id: int, book_update: schemas.BookCreate) -> Optional[models.Book]:
    book = await db.get(models.Book, book_id)
    if not book:
        return None

    # Handle publisher change and book counts
    if book.publisher_id != book_update.publisher_id:
        # Decrement count for the old publisher if it exists
        if book.publisher_id:
            old_publisher = await db.get(models.Publisher, book.publisher_id)
            if old_publisher and old_publisher.book_count > 0:
                old_publisher.book_count -= 1
                db.add(old_publisher)

        # Increment count for the new publisher if it exists
        if book_update.publisher_id:
            new_publisher = await db.get(models.Publisher, book_update.publisher_id)
            if not new_publisher:
                raise HTTPException(status_code=404, detail=f"New Publisher ID {book_update.publisher_id} not found.")
            new_publisher.book_count += 1
            db.add(new_publisher)
            book.publisher_id = book_update.publisher_id
        else:  # New publisher_id is None
            book.publisher_id = None

    book.title = book_update.title
    # book.publisher_id = book_update.publisher_id # Handled above

    db.add(book)  # Add book to session for update
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
            db.add(publisher)

    # Consider what to do with related Authors and Reviews if not handled by cascade delete
    # Current model has cascade="all, delete-orphan" for authors and reviews on Book.

    await db.delete(book_to_delete)
    await db.commit()
    return True


# --- Author CRUD ---
# These CRUDs assume Author is tied to one Book as per current models.
async def create_author(db: AsyncSession, author_in: schemas.AuthorCreate) -> models.Author:
    # Check if the associated book exists
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


async def get_authors(db: AsyncSession) -> List[models.Author]:
    result = await db.execute(select(models.Author))
    return result.scalars().all()


# --- Review CRUD ---
async def create_review(db: AsyncSession, review_in: schemas.ReviewCreate, current_user: models.User) -> models.Review:
    # Check if the book exists
    book = await db.get(models.Book, review_in.book_id)
    if not book:
        raise HTTPException(status_code=404, detail=f"Book with id {review_in.book_id} not found for review.")

    new_review = models.Review(
        rating=review_in.rating,
        review_text=review_in.review_text,
        date_posted=datetime.now(timezone.utc),  # Use timezone aware datetime
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

    if review.user_id != current_user.id and current_user.role != models.Role.ADMIN:  # Use models.Role
        raise HTTPException(status_code=403, detail="Not authorized to update this review")

    update_data = review_update.model_dump(exclude_unset=True)  # Pydantic v2
    # update_data = review_update.dict(exclude_unset=True) # Pydantic v1

    for key, value in update_data.items():
        setattr(review, key, value)

    # If book_id is part of ReviewUpdate and changed, validate new book_id
    # if 'book_id' in update_data and review.book_id != update_data['book_id']:
    #     new_book = await db.get(models.Book, update_data['book_id'])
    #     if not new_book:
    #         raise HTTPException(status_code=404, detail=f"New Book ID {update_data['book_id']} not found.")

    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


async def delete_review(db: AsyncSession, review_id: int, current_user: models.User) -> dict:
    review = await db.get(models.Review, review_id)  # Use db.get for simplicity
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user.id and current_user.role != models.Role.ADMIN:  # Use models.Role
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")

    await db.delete(review)
    await db.commit()
    return {"detail": "Review deleted successfully"}


# --- Publisher CRUD ---
async def create_publisher(db: AsyncSession, publisher_in: schemas.PublisherCreate) -> models.Publisher:
    # Check for existing publisher by name or email to prevent duplicates if needed
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
        book_count=0  # Initial book count
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