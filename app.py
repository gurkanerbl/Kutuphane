from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from dotenv import load_dotenv
import os

from entity import db, User, Book
from controller import api

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
CORS(app)
Swagger(app, template={
    "info": {"title": "Library API", "version": "1.0"},
    "securityDefinitions": {
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}
    }
})

app.register_blueprint(api, url_prefix='/api')

@app.route('/')
def index():
    return {'message': 'Library API', 'docs': '/apidocs'}


def seed_data():

    if User.query.first():
        return
    
    from repository import UserRepository, BookRepository
    
    # default hesaplar

    UserRepository.create('admin@test.com', 'Admin', 'admintest123', 'admin')
    UserRepository.create('user@test.com', 'Test User', 'test123', 'student')
    UserRepository.create('gurkan@test.com', 'Gurkan', 'test123', 'admin')
    
    # default kitaplar

    BookRepository.create('Clean Code', 'Robert C. Martin', 'Programming', 10)
    BookRepository.create('Python Crash Course', 'Eric Matthes', 'Programming', 10)
    BookRepository.create('Sapiens', 'Yuval Noah Harari', 'History', 10)
    BookRepository.create('1984', 'George Orwell', 'Fiction', 10)
    BookRepository.create('For Whom The Bell', 'George Orwell', 'Fiction', 10)
    
    print(' Örnek veriler eklendi. ')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    
    print('\n' + '='*50)
    print(' Kütüphane Yönetim Sistemi ')
    print('='*50)
    print(' API: http://localhost:5000 ')
    print(' Docs: http://localhost:5000/apidocs ')
    print('='*50 + '\n')
    
    app.run(debug=True, port=5000)
