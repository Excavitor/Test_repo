from sqlalchemy.future import select
from Test_repo.app.models import Book

async def create_book(db, book):
    new_book = Book(title=book.title, author=book.author, published_date=book.published_date)
    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)
    return new_book

async def get_books(db):
    result = await db.execute(select(Book))
    return result.scalars().all()
