*Library Management System*

A simple library management system built with Flask, SQLAlchemy, and basic authentication.

*Features*

- User registration and login
- Book catalog management (add, view)
- Borrow request management (submit, approve, deny)
- Personal borrow history

*Requirements*

- Python 3.x
- Flask
- Flask-SQLAlchemy
- Flask-HTTPAuth
- Flask-CORS

*Setup*

1. Clone the repository
2. Install requirements with `pip install -r requirements.txt`
3. Create a database (e.g., SQLite)

*API Endpoints*

- `/api/librarian/create_user`: Create a new librarian user
- `/api/librarian/add_book`: Add a new book to the catalog
- `/api/user/books`: Get a list of available books
- `/api/user/borrow_request`: Submit a borrow request
- `/api/user/borrow_history`: View personal borrow history

