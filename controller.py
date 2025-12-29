"""
controller

"""
from flask import Blueprint, request, jsonify
from functools import wraps
from service import AuthService, BookService, LendingService, UserService

api = Blueprint('api', __name__)


# json web token

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Token gerekli'}), 401
        user = AuthService.get_user_from_token(token)
        if not user:
            return jsonify({'error': 'Geçersiz token'}), 401
        request.user = user  # type ignore
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.user.role != 'admin':  # type ignore
            return jsonify({'error': 'Admin yetkisi gerekli'}), 403
        return f(*args, **kwargs)
    return decorated


@api.route('/register', methods=['POST'])
def register():
    """Kayit ol
    ---
    tags: [Auth]
    parameters:
      - in: body
        name: body
        schema:
          properties:
            email: {type: string}
            password: {type: string}
            name: {type: string}
    responses:
      201: {description: Basarili}
    """
    try:
        data = request.json  # type: ignore
        user = AuthService.register(data['email'], data['name'], data['password'])  # type ignore
        return jsonify({'message': 'Kayıt başarılı', 'user': user.to_dict()}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@api.route('/login', methods=['POST'])
def login():
    """Giris yap
    ---
    tags: [Auth]
    parameters:
      - in: body
        name: body
        schema:
          properties:
            email: {type: string}
            password: {type: string}
    responses:
      200: {description: Token}
    """
    try:
        data = request.json  # type: ignore
        result = AuthService.login(data['email'], data['password'])  # type ignore
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': str(e)}), 401

@api.route('/profile', methods=['GET'])
@token_required
def profile():
    """Profil bilgisi
    ---
    tags: [Auth]
    security: [{Bearer: []}]
    responses:
      200: {description: User}
    """
    return jsonify({'user': request.user.to_dict()})  # type ignore

@api.route('/books', methods=['GET'])
def get_books():
    """Kitap listesi
    ---
    tags: [Books]
    parameters:
      - name: search
        in: query
        type: string
    responses:
      200: {description: Kitaplar}
    """
    search = request.args.get('search', '')
    books = BookService.search(search) if search else BookService.get_all()
    return jsonify({'books': books})

@api.route('/books/popular', methods=['GET'])
def get_popular_books():
    """En cok okunan kitaplar
    ---
    tags: [Books]
    responses:
      200: {description: Populer kitaplar}
    """
    books = BookService.get_most_borrowed(5)
    return jsonify({'books': books})

@api.route('/books', methods=['POST'])
@admin_required
def create_book():
    """Kitap ekle
    ---
    tags: [Books]
    security: [{Bearer: []}]
    parameters:
      - in: body
        name: body
        schema:
          properties:
            title: {type: string}
            author: {type: string}
            category: {type: string}
            quantity: {type: integer}
    responses:
      201: {description: Eklendi}
    """
    data = request.json  # type: ignore
    book = BookService.create(data['title'], data['author'], data['category'], data.get('quantity', 1))  # type ignore
    return jsonify({'message': 'Kitap eklendi', 'book': book}), 201

@api.route('/books/<int:id>', methods=['DELETE'])
@admin_required
def delete_book(id):
    """Kitap sil
    ---
    tags: [Books]
    security: [{Bearer: []}]
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200: {description: Silindi}
    """
    BookService.delete(id)
    return jsonify({'message': 'Silindi'})

@api.route('/borrow/<int:book_id>', methods=['POST'])
@token_required
def borrow_book(book_id):
    """Odunc al
    ---
    tags: [Lending]
    security: [{Bearer: []}]
    parameters:
      - name: book_id
        in: path
        type: integer
        required: true
    responses:
      201: {description: Odunc alindi}
    """
    try:
        lending = LendingService.borrow(request.user.id, book_id)  # type ignore
        return jsonify({'message': 'Ödünç alındı', 'lending': lending}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@api.route('/return/<int:lending_id>', methods=['POST'])
@token_required
def return_book(lending_id):
    """Iade et
    ---
    tags: [Lending]
    security: [{Bearer: []}]
    parameters:
      - name: lending_id
        in: path
        type: integer
        required: true
    responses:
      200: {description: Iade edildi}
    """
    try:
        result = LendingService.return_book(lending_id, request.user)  # type ignore
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@api.route('/my-lendings', methods=['GET'])
@token_required
def my_lendings():
    """Odunclerim
    ---
    tags: [Lending]
    security: [{Bearer: []}]
    responses:
      200: {description: Odunc listesi}
    """
    lendings = LendingService.get_user_lendings(request.user.id)  # type ignore
    return jsonify({'lendings': lendings})

@api.route('/all-lendings', methods=['GET'])
@admin_required
def all_lendings():
    """Tum oduncler
    ---
    tags: [Lending]
    security: [{Bearer: []}]
    responses:
      200: {description: Tum oduncler}
    """
    lendings = LendingService.get_all_lendings()
    return jsonify({'lendings': lendings})

@api.route('/check-overdue', methods=['POST'])
@admin_required
def check_overdue():
    """Gecikme kontrolu
    ---
    tags: [Lending]
    security: [{Bearer: []}]
    responses:
      200: {description: Bildirim gonderildi}
    """
    count = LendingService.check_overdue_and_notify()
    return jsonify({'message': f'{count} gecikmiş kitap için bildirim gönderildi'})

# user cont
@api.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Kullanici listesi
    ---
    tags: [Users]
    security: [{Bearer: []}]
    responses:
      200: {description: Kullanicilar}
    """
    return jsonify({'users': UserService.get_all()})

@api.route('/users/<int:id>', methods=['DELETE'])
@admin_required
def delete_user(id):
    """Kullanici sil
    ---
    tags: [Users]
    security: [{Bearer: []}]
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200: {description: Silindi}
    """
    UserService.delete(id)
    return jsonify({'message': 'Silindi'})
