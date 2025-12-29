"""
service

"""
from repository import UserRepository, BookRepository, LendingRepository, FineRepository
from datetime import datetime, timedelta
import jwt
import os


class AuthService:
    TOKEN_EXPIRY_HOURS = 1  # 1 saatlik token süresi
    
    @staticmethod
    def register(email, name, password):
        if UserRepository.find_by_email(email):
            raise ValueError('Email zaten kayıtlı')
        return UserRepository.create(email, name, password)
    
    @staticmethod
    def login(email, password):
        user = UserRepository.find_by_email(email)
        if not user or not user.check_password(password):
            raise ValueError('Email veya şifre hatalı')
        
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=AuthService.TOKEN_EXPIRY_HOURS)
        }, os.getenv('JWT_SECRET'), algorithm='HS256')
        return {'token': token, 'user': user.to_dict()}
    
    @staticmethod
    def get_user_from_token(token):
        try:
            data = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
            return UserRepository.find_by_id(data['user_id'])
        except jwt.ExpiredSignatureError:
            return None  # token expired
        except:
            return None


class BookService:
    @staticmethod
    def get_all():
        return [b.to_dict() for b in BookRepository.find_all()]
    
    @staticmethod
    def search(query):
        return [b.to_dict() for b in BookRepository.search(query)]
    
    @staticmethod
    def get_by_id(id):
        book = BookRepository.find_by_id(id)
        return book.to_dict() if book else None
    
    @staticmethod
    def create(title, author, category, quantity=1):
        book = BookRepository.create(title, author, category, quantity)
        return book.to_dict()
    
    @staticmethod
    def delete(id):
        book = BookRepository.find_by_id(id)
        if book:
            BookRepository.delete(book)
            return True
        return False
    
    @staticmethod
    def get_most_borrowed(limit=5):
        result = BookRepository.find_most_borrowed(limit)
        return [{'book': book.to_dict(), 'borrow_count': count} for book, count in result]


class LendingService:
    @staticmethod
    def borrow(user_id, book_id):
        book = BookRepository.find_by_id(book_id)
        if not book:
            raise ValueError('Kitap bulunamadı')
        if book.available <= 0:
            raise ValueError('Kitap mevcut değil')
        
        existing = LendingRepository.find_active_by_user_and_book(user_id, book_id)
        if existing:
            raise ValueError('Bu kitabı zaten ödünç almışsınız')
        
        lending = LendingRepository.create(user_id, book_id)
        book.available -= 1
        BookRepository.save()
        return lending.to_dict()
    
    @staticmethod
    def return_book(lending_id, user):
        lending = LendingRepository.find_by_id(lending_id)
        if not lending:
            raise ValueError('Kayıt bulunamadı')
        if lending.user_id != user.id and user.role != 'admin':
            raise ValueError('Yetkiniz yok')
        if lending.returned:
            raise ValueError('Zaten iade edilmiş')
        
        lending.returned = True
        lending.return_date = datetime.utcnow()
        lending.book.available += 1
        
        fine = None
        if lending.is_overdue:
            # stored procedure ceza hesaplamasi
            from entity import db
            result = db.session.execute(
                db.text("SELECT calculate_fine(:lending_id)"),
                {'lending_id': lending_id}
            ).scalar()
            fine_amount = result if result else lending.days_overdue * 1
            fine = FineRepository.create(lending.id, fine_amount)
            EmailService.send_fine_notification(lending.user, fine)
        
        LendingRepository.save()
        return {'lending': lending.to_dict(), 'fine': fine.to_dict() if fine else None}
    
    @staticmethod
    def get_user_lendings(user_id):
        return [l.to_dict() for l in LendingRepository.find_by_user(user_id)]
    
    @staticmethod
    def get_all_lendings():
        return [l.to_dict() for l in LendingRepository.find_all()]
    
    @staticmethod
    def check_overdue_and_notify():
        # stored procedure ceza kitaplari
        from entity import db
        result = db.session.execute(db.text("SELECT * FROM get_overdue_books()")).fetchall()
        
        for row in result:
            user = UserRepository.find_by_id(row.user_id) if hasattr(row, 'user_id') else None
            if user:
                EmailService.send_overdue_notification_raw(row.user_email, row.user_name, row.book_title, row.days_overdue)
        return len(result)


class UserService:
    @staticmethod
    def get_all():
        return [u.to_dict() for u in UserRepository.find_all()]
    
    @staticmethod
    def delete(id):
        user = UserRepository.find_by_id(id)
        if user:
            UserRepository.delete(user)
            return True
        return False


class EmailService:
    
    @staticmethod
    def send_overdue_notification(user, book, days_overdue):
        print(f"""
        ════════════════════════════════════════════
              GECİKME BİLDİRİMİ
        ════════════════════════════════════════════
        Alıcı: {user.email}
        Konu: Kitap İade Hatırlatması
        
        Sayın {user.name},
        
        "{book.title}" kitabını iade süreniz {days_overdue} gün geçmiştir.
        Lütfen en kısa sürede iade ediniz.
        
        Ceza: {days_overdue} TL
        ════════════════════════════════════════════
        """)
    
    @staticmethod
    def send_overdue_notification_raw(email, name, book_title, days_overdue):
        print(f"""
        ════════════════════════════════════════════
              GECİKME BİLDİRİMİ (SP)
        ════════════════════════════════════════════
        Alıcı: {email}
        Konu: Kitap İade Hatırlatması
        
        Sayın {name},
        
        "{book_title}" kitabını iade süreniz {days_overdue} gün geçmiştir.
        Lütfen en kısa sürede iade ediniz.
        
        Ceza: {days_overdue} TL
        ════════════════════════════════════════════
        """)
    
    @staticmethod
    def send_fine_notification(user, fine):
        print(f"""
        ════════════════════════════════════════════
                CEZA BİLDİRİMİ
        ════════════════════════════════════════════
        Alıcı: {user.email}
        Konu: Gecikme Cezası
        
        Sayın {user.name},
        
        Gecikme cezanız: {fine.amount} TL
        ════════════════════════════════════════════
        """)
