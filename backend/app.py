from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///streamix.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref='movies')

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({'message': 'Erabiltzailea existitzen da'}), 400
    hashed = generate_password_hash(data.get('password'))
    new_user = User(username=data.get('username'), email=data.get('email'), password_hash=hashed)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Erregistratua'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data.get('username') == 'Admin' and data.get('password') == 'Admin':
        token = jwt.encode({'user_id': 0, 'role': 'admin', 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token, 'role': 'admin'}), 200
    user = User.query.filter_by(username=data.get('username')).first()
    if user and check_password_hash(user.password_hash, data.get('password')):
        token = jwt.encode({'user_id': user.id, 'role': user.role, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token, 'role': user.role}), 200
    return jsonify({'message': 'Kredentzial okerrak'}), 401

@app.route('/profile', methods=['GET'])
def get_profile():
    token = request.headers.get('Authorization')
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if data['user_id'] == 0:
            return jsonify({'username': 'Admin', 'role': 'admin'}), 200
        user = User.query.get(data['user_id'])
        return jsonify({'username': user.username, 'role': user.role}), 200
    except:
        return jsonify({'message': 'Token okerra'}), 401

@app.route('/api/movies', methods=['GET', 'POST'])
def handle_movies():
    if request.method == 'POST':
        data = request.get_json()
        new_movie = Movie(title=data['title'], description=data.get('description', ''))
        db.session.add(new_movie)
        db.session.commit()
        return jsonify({'message': 'Gordeta'}), 201
    movies = Movie.query.all()
    return jsonify([{'id': m.id, 'title': m.title, 'description': m.description} for m in movies])

@app.route('/api/movies/<int:id>', methods=['DELETE'])
def delete_movie(id):
    movie = Movie.query.get(id)
    if movie:
        Favorite.query.filter_by(movie_id=id).delete()
        db.session.delete(movie)
        db.session.commit()
    return jsonify({'message': 'Ezabatua'}), 200

@app.route('/api/favorites', methods=['GET', 'POST'])
def handle_favorites():
    token = request.headers.get('Authorization')
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    user_id = data['user_id']

    if request.method == 'POST':
        movie_id = request.get_json().get('movie_id')
        exists = Favorite.query.filter_by(user_id=user_id, movie_id=movie_id).first()
        if not exists:
            new_fav = Favorite(user_id=user_id, movie_id=movie_id)
            db.session.add(new_fav)
            db.session.commit()
        return jsonify({'message': 'Gogokoetara gehituta'}), 200

    favs = Favorite.query.filter_by(user_id=user_id).all()
    movie_ids = [f.movie_id for f in favs]
    movies = Movie.query.filter(Movie.id.in_(movie_ids)).all()
    return jsonify([{'id': m.id, 'title': m.title, 'description': m.description} for m in movies])

@app.route('/api/favorites/<int:movie_id>', methods=['DELETE'])
def remove_favorite(movie_id):
    token = request.headers.get('Authorization')
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    fav = Favorite.query.filter_by(user_id=data['user_id'], movie_id=movie_id).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
    return jsonify({'message': 'Gogokoetatik kenduta'}), 200

@app.route('/api/categories', methods=['GET'])
def get_categories():
    kategoriak = Category.query.all()
    return jsonify([{'id': k.id, 'name': k.name} for k in kategoriak])
    
@app.route('/api/categories', methods=['POST'])
def create_category():
    token = request.headers.get('Authorization')
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if data.get('role') != 'admin':
            return jsonify({'mezua': 'Admin bakarrik'}), 403
    except:
        return jsonify({'mezua': 'Token okerra'}), 401

    cat_data = request.get_json()
    if not cat_data.get('name'):
        return jsonify({'mezua': 'Izena beharrezkoa'}), 400
    kategoria = Category(name=cat_data['name'])
    db.session.add(kategoria)
    db.session.commit()
    return jsonify({'id': kategoria.id, 'name': kategoria.name}), 201

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
