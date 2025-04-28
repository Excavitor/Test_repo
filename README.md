# FastAPI Book Management Application

This is a simple CRUD (Create, Read, Update, Delete) application for managing books using FastAPI, SQLAlchemy (Async), and SQLite.

## How to Run

1. Clone the repository
2. Create and activate a virtual environment
3. Install the dependencies
4. Start the FastAPI server 
5. go to Test_repo directory using `cd test_1\Test_repo`
6. then type: `uvicorn app.main:app --reload`

The application will run at:  
http://127.0.0.1:8000

Swagger UI (API testing):  
http://127.0.0.1:8000/docs

## API Endpoints

| Method | URL                   | Description        |
|--------|------------------------|--------------------|
| POST   | /books/                 | Create a new book  |
| GET    | /books/                 | Read all books     |
| PUT    | /books/{book_id}        | Update a book      |
| DELETE | /books/{book_id}        | Delete a book      |


## Notes

- The database will be created automatically.
- Use Swagger UI for testing APIs directly.
- Make sure to run commands inside the correct directory where `app/` folder exists.
