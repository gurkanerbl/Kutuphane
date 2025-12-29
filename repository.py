"""
repository 

"""
from entity import db, User, Book, Lending, Fine


class UserRepository:
    @staticmethod
    def create(email, name, password, role='student'):
        user = User(email=email, name=name, role=role)  # type ignore
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def find_by_email(email):
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def find_by_id(id):
        return User.query.get(id)
    
    @staticmethod
    def find_all():
        return User.query.all()
    
    @staticmethod
    def delete(user):
        db.session.delete(user)
        db.session.commit()


class BookRepository:
    @staticmethod
    def create(title, author, category, quantity=1):
        book = Book(title=title, author=author, category=category, quantity=quantity, available=quantity)  # type ignore
        db.session.add(book)
        db.session.commit()
        return book
    
    @staticmethod
    def find_by_id(id):
        return Book.query.get(id)
    
    @staticmethod
    def find_all():
        return Book.query.all()
    
    @staticmethod
    def search(query):
        return Book.query.filter(
            (Book.title.ilike(f'%{query}%')) | (Book.author.ilike(f'%{query}%'))
        ).all()
    
    @staticmethod
    def delete(book):
        db.session.delete(book)
        db.session.commit()
    
    @staticmethod
    def save():
        db.session.commit()
    
    @staticmethod
    def find_most_borrowed(limit=5):
        from sqlalchemy import func
        result = db.session.query(
            Book, func.count(Lending.id).label('borrow_count')
        ).join(Lending).group_by(Book.id).order_by(func.count(Lending.id).desc()).limit(limit).all()
        return result


class LendingRepository:
    @staticmethod
    def create(user_id, book_id):
        lending = Lending(user_id=user_id, book_id=book_id)
        db.session.add(lending)
        db.session.commit()
        return lending
    
    @staticmethod
    def find_by_id(id):
        return Lending.query.get(id)
    
    @staticmethod
    def find_by_user(user_id):
        return Lending.query.filter_by(user_id=user_id).order_by(Lending.id.desc()).all()
    
    @staticmethod
    def find_active_by_user_and_book(user_id, book_id):
        return Lending.query.filter_by(user_id=user_id, book_id=book_id, returned=False).first()
    
    @staticmethod
    def find_all():
        return Lending.query.order_by(Lending.id.desc()).all()
    
    @staticmethod
    def find_overdue():
        from datetime import datetime
        return Lending.query.filter(Lending.returned == False, Lending.due_date < datetime.utcnow()).all()  # type ignore
    
    @staticmethod
    def save():
        db.session.commit()


class FineRepository:
    @staticmethod
    def create(lending_id, amount):
        fine = Fine(lending_id=lending_id, amount=amount)  # type ignore
        db.session.add(fine)
        db.session.commit()
        return fine
    
    @staticmethod
    def find_by_lending(lending_id):
        return Fine.query.filter_by(lending_id=lending_id).first()
