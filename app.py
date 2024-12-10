from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS 

from models import User, Book, BookRequest, db  

app = Flask(__name__)

app.config.from_object('config.Config')
db.init_app(app)

CORS(app)

# Basic Authentication setup
users = {
    "admin": generate_password_hash("admin123"),
    "user1": generate_password_hash("user123")
}

# Authentication verification function
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users[username], password):
        return username

# Create a new library user (librarian)
@app.route('/api/librarian/create_user', methods=['POST'])
@auth.login_required
def create_user():
    if auth.current_user() != 'admin':
        return jsonify({'message': 'Permission denied'}), 403
    
    data = request.get_json()
    email = data.get('email')
    password = generate_password_hash(data.get('password'))
    role = data.get('role')  # librarian or user
    
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'User already exists'}), 400
    
    new_user = User(email=email, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

# Admin-only API to add a new book
@app.route('/api/librarian/add_book', methods=['POST'])
@auth.login_required
def add_book():
    if auth.current_user() != 'admin':
        return jsonify({'message': 'Permission denied'}), 403
    
    data = request.get_json()

    # Get book details from the request body
    title = data.get('title')
    author = data.get('author')
    available_copies = data.get('available_copies')

    if not title or not author or not available_copies:
        return jsonify({'message': 'Missing required fields'}), 400

    # Create a new Book
    new_book = Book(title=title, author=author, available_copies=available_copies)

    try:
        # Add the book to the database
        db.session.add(new_book)
        db.session.commit()

        return jsonify({'message': 'Book added successfully', 'book': {
            'id': new_book.id, 'title': new_book.title, 'author': new_book.author, 'available_copies': new_book.available_copies
        }}), 201
    
    except Exception as e:
        print(f"Error while adding book: {e}")
        return jsonify({'message': 'An error occurred while adding the book'}), 500

# Librarian: View all borrow requests
@app.route('/api/librarian/borrow_requests', methods=['GET'])
@auth.login_required
def view_borrow_requests():
    if auth.current_user() != 'admin':
        return jsonify({'message': 'Permission denied'}), 403
    
    requests = BookRequest.query.all()
    requests_data = [{"id": req.id, "user_id": req.user_id, "book_id": req.book_id, 
                      "start_date": req.start_date, "end_date": req.end_date, "status": req.status} for req in requests]
    return jsonify({'borrow_requests': requests_data})

# Librarian: Approve or deny borrow requests
@app.route('/api/librarian/approve_deny_request/<int:req_id>', methods=['PUT'])
@auth.login_required
def approve_deny_request(req_id):
    if auth.current_user() != 'admin':
        return jsonify({'message': 'Permission denied'}), 403

    data = request.get_json()
    status = data.get('status')  # 'approved' or 'denied'
    request = BookRequest.query.get(req_id)
    
    if not request:
        return jsonify({'message': 'Request not found'}), 404

    if status == 'approved':
        overlapping_requests = BookRequest.query.filter(
            BookRequest.book_id == request.book_id,
            (BookRequest.start_date <= request.end_date) & (BookRequest.end_date >= request.start_date)
        ).all()

        if overlapping_requests:
            return jsonify({'message': 'Book is already borrowed for the requested dates'}), 400
        
        request.status = 'approved'
    else:
        request.status = 'denied'
    
    db.session.commit()
    return jsonify({'message': f'Request {status} successfully'})

# User: Get list of books
@app.route('/api/user/books', methods=['GET'])
@auth.login_required
def get_books():
    print("Getting list of books...")

    try:
        books = Book.query.all()
        print(f"Found {len(books)} books.")
        books_data = [{"id": book.id, "title": book.title, "author": book.author, "available_copies": book.available_copies} for book in books]
        return jsonify({'books': books_data})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'message': 'An error occurred while fetching books'}), 500

# User: Submit a borrow request
@app.route('/api/user/borrow_request', methods=['POST'])
@auth.login_required
def borrow_request():
    data = request.get_json()
    user_id = data.get('user_id')
    book_id = data.get('book_id')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    overlapping_requests = BookRequest.query.filter(
        BookRequest.book_id == book_id,
        (BookRequest.start_date <= end_date) & (BookRequest.end_date >= start_date)
    ).all()

    if overlapping_requests:
        return jsonify({'message': 'Book is already borrowed for the requested dates'}), 400

    borrow_request = BookRequest(user_id=user_id, book_id=book_id, start_date=start_date, end_date=end_date)
    db.session.add(borrow_request)
    db.session.commit()
    return jsonify({'message': 'Borrow request submitted successfully'}), 201

# User: View personal borrow history
@app.route('/api/user/borrow_history', methods=['GET'])
@auth.login_required
def borrow_history():
    user_id = request.args.get('user_id')
    requests = BookRequest.query.filter_by(user_id=user_id).all()
    requests_data = [{"id": req.id, "book_id": req.book_id, "start_date": req.start_date, "end_date": req.end_date, "status": req.status} for req in requests]
    return jsonify({'borrow_history': requests_data})

# Main
if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True)
