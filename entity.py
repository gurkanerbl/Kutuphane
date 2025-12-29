"""
entity

"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import bcrypt

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='student')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())
    
    def to_dict(self):
        return {'id': self.id, 'email': self.email, 'name': self.name, 'role': self.role}


class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    available = db.Column(db.Integer, default=1)
    
    def to_dict(self):
        return {
            'id': self.id, 'title': self.title,
            'author': self.author, 'category': self.category,
            'quantity': self.quantity, 'available': self.available,
            'is_available': self.available > 0
        }


class Lending(db.Model):
    __tablename__ = 'lendings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    return_date = db.Column(db.DateTime)
    returned = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='lendings')
    book = db.relationship('Book', backref='lendings')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.due_date:
            self.due_date = datetime.utcnow() + timedelta(days=14)
    
    @property
    def is_overdue(self):
        return not self.returned and datetime.utcnow() > self.due_date
    
    @property
    def days_overdue(self):
        if not self.is_overdue: return 0
        return (datetime.utcnow() - self.due_date).days
    
    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.to_dict() if self.user else None,
            'book': self.book.to_dict() if self.book else None,
            'borrow_date': self.borrow_date.isoformat(),
            'due_date': self.due_date.isoformat(),
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'returned': self.returned,
            'is_overdue': self.is_overdue,
            'days_overdue': self.days_overdue
        }


class Fine(db.Model):
    __tablename__ = 'fines'
    
    id = db.Column(db.Integer, primary_key=True)
    lending_id = db.Column(db.Integer, db.ForeignKey('lendings.id'), nullable=False)
    amount = db.Column(db.Float, default=0)
    paid = db.Column(db.Boolean, default=False)
    
    lending = db.relationship('Lending', backref='fine')
    
    def to_dict(self):
        return {'id': self.id, 'lending_id': self.lending_id, 'amount': self.amount, 'paid': self.paid}
