from sqlalchemy.future import select
from app.models import Book, Author, Review, Publisher
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete
from datetime import datetime

async def create_book(db, book):
    new_book = Book(title=book.title, publisher_id=book.publisher_id)
    db.add(new_book)

    pub = await db.get(Publisher, book.publisher_id)
    if pub:
        pub.book_count += 1
        db.add(pub)

    await db.commit()
    await db.refresh(new_book)
    return new_book

async def get_books(db):
    result = await db.execute(select(Book))
    return result.scalars().all()

async def update_book(db, book_id: int, updated_data):
    book = await db.get(Book, book_id)

    if book:
        pub_id = book.publisher_id
        # delete the book
        await db.execute(
            sqlalchemy_delete(Book)
            .where(Book.id == book_id)
            .execution_options(synchronize_session="fetch")
        )
        # decrement publisher count
        pub = await db.get(Publisher, pub_id)
        if pub and pub.book_count > 0:
            pub.book_count -= 1
            db.add(pub)

    await db.commit()

async def delete_book(db, book_id: int):
    query = (
        sqlalchemy_delete(Book)
        .where(Book.id == book_id)
        .execution_options(synchronize_session="fetch")
    )
    await db.execute(query)
    await db.commit()

async def create_author(db, author):
    new_author = Author(name=author.name, biography=author.biography, birth_date=author.birth_date, book_id=author.book_id)
    db.add(new_author)
    await db.commit()
    await db.refresh(new_author)
    return new_author

async def get_authors(db):
    result = await db.execute(select(Author))
    return result.scalars().all()

async def create_review(db, review):
    new_review = Review(rating=review.rating, review_text=review.review_text, date_posted=datetime.utcnow(), book_id=review.book_id)
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    return new_review

async def get_reviews(db, book_id=None):
    if book_id:
        result = await db.execute(select(Review).where(Review.book_id == book_id))
    else:
        result = await db.execute(select(Review))
    reviews = result.scalars().all()
    return reviews

async def create_publisher(db, publisher):
    new_pub = Publisher(
        name=publisher.name,
        email=publisher.email,
        phone_number=publisher.phone_number,
        website=publisher.website,
    )
    db.add(new_pub)
    await db.commit()
    await db.refresh(new_pub)
    return new_pub

async def get_publishers(db):
    result = await db.execute(select(Publisher))
    return result.scalars().all()