from sqlalchemy.future import select
from app.models import Book
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete

async def create_book(db, book):
    new_book = Book(title=book.title, author=book.author, published_date=book.published_date)
    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)
    return new_book

async def get_books(db):
    result = await db.execute(select(Book))
    return result.scalars().all()

async def update_book(db, book_id: int, updated_data):
    query = (
        sqlalchemy_update(Book)
        .where(Book.id == book_id)
        .values(**updated_data.dict())
        .execution_options(synchronize_session="fetch")
    )
    await db.execute(query)
    await db.commit()

async def delete_book(db, book_id: int):
    query = (
        sqlalchemy_delete(Book)
        .where(Book.id == book_id)
        .execution_options(synchronize_session="fetch")
    )
    await db.execute(query)
    await db.commit()