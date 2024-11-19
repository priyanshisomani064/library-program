from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "library_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'user'

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    available = db.Column(db.Boolean, default=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=False)
    remarks = db.Column(db.String(200), nullable=True)
    fine_paid = db.Column(db.Boolean, default=False)

# Routes
@app.route("/")
def index():
    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            if user.role == "admin":
                return redirect(url_for("admin"))
            return redirect(url_for("reports"))
        flash("Invalid credentials", "error")
    return render_template("login.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/reports")
def reports():
    books = Book.query.all()
    return render_template("reports.html", books=books)

@app.route("/issue-book", methods=["GET", "POST"])
def issue_book():
    if request.method == "POST":
        book_id = request.form.get("book_id")
        user_id = request.form.get("user_id")
        book = Book.query.get(book_id)
        if not book or not book.available:
            flash("Book not available", "error")
            return redirect(url_for("issue_book"))

        book.available = False
        issue_date = datetime.today().date()
        return_date = issue_date + timedelta(days=15)

        transaction = Transaction(book_id=book_id, user_id=user_id, issue_date=issue_date, return_date=return_date)
        db.session.add(transaction)
        db.session.commit()
        flash("Book issued successfully", "success")
        return redirect(url_for("reports"))

    books = Book.query.filter_by(available=True).all()
    return render_template("issue_book.html", books=books)

@app.route("/return-book", methods=["GET", "POST"])
def return_book():
    if request.method == "POST":
        transaction_id = request.form.get("transaction_id")
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            flash("Invalid transaction", "error")
            return redirect(url_for("return_book"))

        fine_paid = request.form.get("fine_paid") == "on"
        transaction.fine_paid = fine_paid
        transaction.book.available = True  # Mark book as available
        db.session.commit()
        flash("Book returned successfully", "success")
        return redirect(url_for("reports"))

    transactions = Transaction.query.all()
    return render_template("return_book.html", transactions=transactions)

if __name__ == "__main__":
    db.create_all()  # Initialize database
    app.run(debug=True)
