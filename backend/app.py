from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
import os

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///streamix.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

# Crear carpeta uploads si no existe
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)

migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')
    avatar = db.Column(db.String(10), default='👤')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    poster = db.Column(db.String(500))
    duration = db.Column(db.Integer, nullable=True)  # Opcional
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref='movies')
    comments = db.relationship('Comment', backref='movie', cascade='all, delete-orphan')

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    user = db.relationship('User', backref='comments')

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not username:
            return jsonify({'message': 'Erabiltzailearen izena beharrezkoa'}), 400
        if not email:
            return jsonify({'message': 'Emaila beharrezkoa'}), 400
        if not password:
            return jsonify({'message': 'Pasahitza beharrezkoa'}), 400
        
        # Validar email básico
        if '@' not in email:
            return jsonify({'message': 'Email ez da baliozkoa'}), 400
        
        # Validar que el usuario no exista
        if User.query.filter_by(username=username).first():
            return jsonify({'message': 'Erabiltzailea existitzen da'}), 400
        
        # Validar que el email no exista
        if User.query.filter_by(email=email).first():
            return jsonify({'message': 'Email hau erregistratuta dago'}), 400
        
        hashed = generate_password_hash(password)
        # Detectar si está intentando registrarse como admin
        role = 'admin' if (username == 'Admin' and password == 'Admin') else 'user'
        new_user = User(username=username, email=email, password_hash=hashed, role=role)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'Erregistratuta!', 'role': role}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Errorea: {str(e)}'}), 500

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
            return jsonify({'username': 'Admin', 'email': 'admin@streamix.com', 'role': 'admin', 'avatar': '👑'}), 200
        user = User.query.get(data['user_id'])
        return jsonify({'username': user.username, 'email': user.email, 'role': user.role, 'avatar': user.avatar}), 200
    except:
        return jsonify({'message': 'Token okerra'}), 401

@app.route('/profile', methods=['PUT'])
def update_profile():
    token = request.headers.get('Authorization')
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if data['user_id'] == 0:
            return jsonify({'message': 'Adminaren profila ezin da aldatu'}), 403
        
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'message': 'Erabiltzailea ez da aurkitzen'}), 404
        
        update_data = request.get_json()
        
        # Actualizar username si se proporciona
        if 'username' in update_data and update_data['username'].strip():
            new_username = update_data['username'].strip()
            if new_username != user.username:
                if User.query.filter_by(username=new_username).first():
                    return jsonify({'message': 'Baina erabiltzailea dagoeneko erregistratuta dago'}), 400
                user.username = new_username
        
        # Actualizar email si se proporciona
        if 'email' in update_data and update_data['email'].strip():
            new_email = update_data['email'].strip()
            if '@' not in new_email:
                return jsonify({'message': 'Email baliozkoa ez da'}), 400
            if new_email != user.email:
                if User.query.filter_by(email=new_email).first():
                    return jsonify({'message': 'Email hau dagoeneko erregistratuta dago'}), 400
                user.email = new_email
        
        # Actualizar contraseña si se proporciona
        if 'password' in update_data and update_data['password'].strip():
            new_password = update_data['password'].strip()
            if len(new_password) < 4:
                return jsonify({'message': 'Pasahitza gutxienez 4 karaktere izan behar du'}), 400
            user.password_hash = generate_password_hash(new_password)
        
        # Actualizar avatar si se proporciona
        if 'avatar' in update_data and update_data['avatar'].strip():
            user.avatar = update_data['avatar'].strip()
        
        db.session.commit()
        return jsonify({'message': 'Profila eguneratu da!', 'username': user.username, 'email': user.email, 'role': user.role, 'avatar': user.avatar}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Errorea: {str(e)}'}), 500

@app.route('/api/movies', methods=['GET', 'POST'])
def handle_movies():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description', '')
        category_id = request.form.get('category_id')
        poster_url = request.form.get('poster', '')
        duration = request.form.get('duration', '')
        duration = int(duration) if duration else None  # Opcional

        if Movie.query.filter_by(title=title).first():
            return jsonify({'message': 'Pelikula hau jada existitzen da'}), 400

        poster_path = poster_url
        if 'poster_file' in request.files:
            file = request.files['poster_file']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                poster_path = f'/uploads/{filename}'

        new_movie = Movie(
            title=title,
            description=description,
            poster=poster_path,
            duration=duration,
            category_id=category_id
        )
        db.session.add(new_movie)
        db.session.commit()
        return jsonify({'message': 'Gordeta'}), 201
    movies = Movie.query.order_by(Movie.title).all()
    seen_titles = set()
    result = []
    for m in movies:
        if m.title in seen_titles:
            continue
        seen_titles.add(m.title)
        result.append({
            'id': m.id,
            'title': m.title,
            'description': m.description,
            'poster': m.poster,
            'duration': m.duration,
            'category': {'id': m.category.id, 'name': m.category.name} if m.category else None,
            'comments': [
                {
                    'id': c.id,
                    'text': c.text,
                    'created_at': c.created_at.isoformat() if c.created_at else None,
                    'user': {
                        'id': c.user.id if c.user else 0,
                        'username': c.user.username if c.user else 'Admin',
                        'avatar': c.user.avatar if c.user else '👑'
                    }
                } for c in sorted(m.comments, key=lambda c: c.created_at)
            ]
        })
    return jsonify(result)

@app.route('/api/movies/<int:movie_id>/comments', methods=['GET', 'POST'])
def handle_movie_comments(movie_id):
    movie = Movie.query.get(movie_id)
    if not movie:
        return jsonify({'message': 'Pelikula ez da aurkitzen'}), 404

    if request.method == 'GET':
        return jsonify([
            {
                'id': c.id,
                'text': c.text,
                'created_at': c.created_at.isoformat() if c.created_at else None,
                'user': {
                    'id': c.user.id if c.user else 0,
                    'username': c.user.username if c.user else 'Admin',
                    'avatar': c.user.avatar if c.user else '👑'
                }
            } for c in sorted(movie.comments, key=lambda c: c.created_at)
        ])

    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token beharrezkoa da'}), 401
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except:
        return jsonify({'message': 'Token okerra'}), 401

    text = request.get_json().get('text', '').strip()
    if not text:
        return jsonify({'message': 'Iruzkin bat beharrezkoa da'}), 400

    comment_user_id = None if data['user_id'] == 0 else data['user_id']
    new_comment = Comment(text=text, movie_id=movie_id, user_id=comment_user_id)
    db.session.add(new_comment)
    db.session.commit()
    return jsonify({
        'id': new_comment.id,
        'text': new_comment.text,
        'created_at': new_comment.created_at.isoformat(),
        'user': {
            'id': new_comment.user.id if new_comment.user else 0,
            'username': new_comment.user.username if new_comment.user else 'Admin',
            'avatar': new_comment.user.avatar if new_comment.user else '👑'
        }
    }), 201

@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token beharrezkoa da'}), 401
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except:
        return jsonify({'message': 'Token okerra'}), 401
    
    # Verificar que es admin
    if data.get('role') != 'admin':
        return jsonify({'message': 'Admin bakarrik iruzkinak ezabatu daitezke'}), 403
    
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'message': 'Iruzkin hau ez da aurkitzen'}), 404
    
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'message': 'Iruzkinak ezabatua'}), 200

@app.route('/api/movies/<int:id>', methods=['DELETE', 'PUT'])
def delete_movie(id):
    if request.method == 'PUT':
        movie = Movie.query.get(id)
        if not movie:
            return jsonify({'message': 'Pelikula ez da aurkitzen'}), 404
        data = request.get_json()
        movie.title = data.get('title', movie.title)
        movie.description = data.get('description', movie.description)
        movie.poster = data.get('poster', movie.poster)
        movie.duration = data.get('duration', movie.duration)
        # Note: category_id not updated for simplicity, but could be added
        db.session.commit()
        return jsonify({'message': 'Eguneratua'}), 200
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
    return jsonify([{
        'id': m.id,
        'title': m.title,
        'description': m.description,
        'category': {'id': m.category.id, 'name': m.category.name} if m.category else None
    } for m in movies])

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

def get_or_create_category(name):
    category = Category.query.filter_by(name=name).first()
    if not category:
        category = Category(name=name)
        db.session.add(category)
        db.session.commit()
    return category

def seed_default_movies():
    action = get_or_create_category('Akzioa')
    scifi = get_or_create_category('Zientzia-fikzioa')
    drama = get_or_create_category('Drama')
    adventure = get_or_create_category('Abentura')
    fantasy = get_or_create_category('Fantasia')
    comedy = get_or_create_category('Komedia')
    animation = get_or_create_category('Animazioa')
    crime = get_or_create_category('Krimen')
    thriller = get_or_create_category('Thriller')
    romance = get_or_create_category('Romantzia')
    horror = get_or_create_category('Horror')
    music = get_or_create_category('Musika')

    default_movies = [
        {'title': 'Gladiator', 'description': 'Gladiatzaile bati buruzko film epikoa antzinako Erroman.', 'category_id': action.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/8/8d/Gladiator_ver1.jpg', 'duration': 155},
        {'title': 'Interstellar', 'description': 'Espazio-bidaia eta denborazko sakontasunak deskubritzen dituen zientzia-fikzio filma.', 'category_id': scifi.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/b/bc/Interstellar_film_poster.jpg', 'duration': 169},
        {'title': 'Inception', 'description': 'Ametsak manipulatu eta errealitatea zalantzan jartzen duen thriller psikologikoa.', 'category_id': scifi.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/7/7f/Inception_ver3.jpg', 'duration': 148},
        {'title': 'The Matrix', 'description': 'Erlaitzaren aurrealdeari eta sistema faltsu bati buruzko zientzia-fikzio klasikoa.', 'category_id': scifi.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/c/c1/The_Matrix_Poster.jpg', 'duration': 136},
        {'title': 'The Dark Knight', 'description': 'Batman eta Jokerren arteko ospea eta drama.' , 'category_id': action.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/8/8a/Dark_Knight.jpg', 'duration': 152},
        {'title': 'The Lord of the Rings', 'description': 'Fantasia-epika mundu magiko batean, abentura handia.', 'category_id': fantasy.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/8/87/Ringstrilogy.jpg', 'duration': 178},
        {'title': 'Parasite', 'description': 'Klase sozialen arteko tentsioa eta umorea beltza uztartzen dituen drama.', 'category_id': drama.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/5/53/Parasite_%282019_film%29.png', 'duration': 132},
        {'title': 'Indiana Jones', 'description': 'Abentura klasikoa altxorra aurkitzeari eta arriskuari buruz.', 'category_id': adventure.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/a/a0/Raiders_of_the_Lost_Ark_poster.jpg', 'duration': 115},
        {'title': 'The Shawshank Redemption', 'description': 'Esperantza eta askatasuna bilatzen duen kartzela-drama harrigarria.', 'category_id': drama.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/8/81/ShawshankRedemptionMoviePoster.jpg', 'duration': 142},
        {'title': 'Forrest Gump', 'description': 'Mundu modernoaren historia ikuspegi xume eta bihotzez inguruan.', 'category_id': drama.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/6/67/Forrest_Gump_poster.jpg', 'duration': 142},
        {'title': 'The Godfather', 'description': 'Mafia-familia boteretsu baten boterea eta leialtasuna aztertzen duen klasikoa.', 'category_id': crime.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/1/1c/Godfather_ver1.jpg', 'duration': 175},
        {'title': 'Pulp Fiction', 'description': 'Krimen-ezohiko hurbilpena eta hizkera berezia lotzen dituen filma.', 'category_id': crime.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/3/3b/Pulp_Fiction_%281994%29_poster.jpg', 'duration': 154},
        {'title': 'The Silence of the Lambs', 'description': 'Polizia ikerketa ilun bat eta psikopata baten arteko tentsioa.', 'category_id': thriller.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/8/86/The_Silence_of_the_Lambs_poster.jpg', 'duration': 118},
        {'title': 'The Prestige', 'description': 'Bi magia-maisuen arteko lehia ezezagun eta trikimailu betean.', 'category_id': drama.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/d/d2/Prestige_poster.jpg', 'duration': 130},
        {'title': 'Avatar', 'description': 'Mundu alienigenaren eta gizateriaren arteko borroka ikusgarria.', 'category_id': fantasy.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/b/b0/Avatar-Teaser-Poster.jpg', 'duration': 162},
        {'title': 'The Lion King', 'description': 'Animazio epikoa familia, koroa eta nortasuna aztertzen duena.', 'category_id': animation.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/3/3d/The_Lion_King_poster.jpg', 'duration': 88},
        {'title': 'Spirited Away', 'description': 'Japoniako animazio magia eta txikien bidaia liluragarria.', 'category_id': animation.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/3/32/Spirited_Away_poster.JPG', 'duration': 125},
        {'title': 'Back to the Future', 'description': 'Denboran atzera bidaia dibertigarria eta arriskuak dakartzan abentura.', 'category_id': scifi.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/d/d2/Back_to_the_Future.jpg', 'duration': 116},
        {'title': 'Mad Max: Fury Road', 'description': 'Aurrekaririk gabea den post-apokaliptiko akzio-bidaia.', 'category_id': action.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/6/6e/Mad_Max_Fury_Road.jpg', 'duration': 120},
        {'title': 'The Departed', 'description': 'Polizia eta mafiosoen artean zurien eta beltzen joko latza.', 'category_id': crime.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/5/50/Departed234.jpg', 'duration': 151},
        {'title': 'The Grand Budapest Hotel', 'description': 'Komedia dotorea, bidaia eta misterio artean murgiltzen den istorioa.', 'category_id': comedy.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/a/a6/The_Grand_Budapest_Hotel_Poster.jpg', 'duration': 99},
        {'title': 'La La Land', 'description': 'Musika, ametsak eta maitasuna Los Angeleseko eszena batean.', 'category_id': music.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/a/ab/La_La_Land_%28film%29.png', 'duration': 128},
        {'title': 'Get Out', 'description': 'Horror sozial bortitza eta tentsio mentala uztartzen duen filma.', 'category_id': horror.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/e/eb/Get_Out_poster.png', 'duration': 104},
        {'title': 'The Truman Show', 'description': 'Errealitate simulatu eta norberaren identitatea aztertzen duen zientzia-fikzioa.', 'category_id': scifi.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/c/cd/The_Truman_Show.jpg', 'duration': 103},
        {'title': 'Blade Runner 2049', 'description': 'Etorkizun distopikoa eta gizakiaren zentzua arakatzen duen sekuela.', 'category_id': scifi.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/9/9b/Blade_Runner_2049_poster.png', 'duration': 164},
        {'title': 'The Social Network', 'description': 'Sare sozialen sorrera eta boterearen garestia kontatzen duen drama.', 'category_id': drama.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/7/7c/Social_network_film_poster.jpg', 'duration': 120},
        {'title': 'Jurassic Park', 'description': 'Dinosaurioen berpizkundea eta abentura izango dituen parkean.', 'category_id': adventure.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/e/e7/Jurassic_Park_poster.jpg', 'duration': 127},
        {'title': 'The Avengers', 'description': 'Superheroi taldeak unibertsoa salbatzeko elkartzen diren akziozko apustua.', 'category_id': action.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/f/f9/TheAvengers2012Poster.jpg', 'duration': 143},
        {'title': 'Toy Story', 'description': 'Jostailuek beren bizitza duela sinesten duten bihotzezko animazioa.', 'category_id': animation.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/1/13/Toy_Story.jpg', 'duration': 81},
        {'title': 'Guardians of the Galaxy', 'description': 'Espazio akzioa eta umorea elkartzen dituen talde bizia.', 'category_id': action.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/b/b5/Guardians_of_the_Galaxy_poster.jpg', 'duration': 121},
        {'title': 'Black Panther', 'description': 'Erritmoak, kultura eta akzio modernoaren arteko ondoan egindako superheroi filma.', 'category_id': action.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/0/0c/Black_Panther_film_poster.jpg', 'duration': 134},
        {'title': 'Titanic', 'description': 'Urperatzearen eta maitasunik gabeko kontakizun dramatikoa.', 'category_id': romance.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/2/22/Titanic_poster.jpg', 'duration': 194},
        {'title': 'The Wizard of Oz', 'description': 'Fantasia klasikoa non ausardia, bihotza eta burujabetza aurkitzen diren.', 'category_id': fantasy.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/c/c9/The_Wizard_of_Oz_1939_poster.jpg', 'duration': 102},
        {'title': 'Fight Club', 'description': 'Gizonen arteko talde sekretu bat eta nortasunaren krisia aztertzen duen drama.', 'category_id': drama.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/f/fc/Fight_Club_poster.jpg', 'duration': 139},
        {'title': 'Pirates of the Caribbean', 'description': 'Itsasontzi pirata eta altxor magikoen abentura.', 'category_id': adventure.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/8/89/Pirates_of_the_Caribbean_-_The_Curse_of_the_Black_Pearl.png', 'duration': 143},
        {'title': 'Harry Potter and the Sorcerer\'s Stone', 'description': 'Mago gazte baten abentura mundu magikoan.', 'category_id': fantasy.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/7/7a/Harry_Potter_and_the_Philosopher%27s_Stone_banner.jpg', 'duration': 152},
        {'title': 'Finding Nemo', 'description': 'Aita eta seme arrainaren bidaia emozionala.', 'category_id': animation.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/2/29/Finding_Nemo.jpg', 'duration': 100},
        {'title': 'The Hangover', 'description': 'Komedia dibertigarria ezkontza-bidaia arriskutsu baten inguruan.', 'category_id': comedy.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/b/b9/Hangoverposter09.jpg', 'duration': 100},
        {'title': 'Whiplash', 'description': 'Musika eta perfekzioa bilatzen duen bateri-jotzailearen istorioa.', 'category_id': music.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/0/01/Whiplash_poster.jpg', 'duration': 107},
        {'title': 'Hereditary', 'description': 'Horror psikologikoa familia-sekretu ilun baten inguruan.', 'category_id': horror.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/5/5d/Hereditary_poster.png', 'duration': 127},
        {'title': 'Romeo and Juliet', 'description': 'Maitasun klasikoa eta tragedia familia-gatazkaren artean.', 'category_id': romance.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/6/6f/Romeo_and_Juliet_Poster.png', 'duration': 119},
        {'title': 'Scarface', 'description': 'Krimen-epika droga-trafiko eta boterearen inguruan.', 'category_id': crime.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/7/78/Scarface.jpg', 'duration': 170},
        {'title': 'Se7en', 'description': 'Thriller iluna zortzi bekatu hilgarrien inguruan.', 'category_id': thriller.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/6/68/Se7enposter.jpg', 'duration': 127},
        {'title': 'Die Hard', 'description': 'Akzio klasikoa eraikin okupatu baten aurkako borrokan.', 'category_id': action.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/7/7e/Die_hard.jpg', 'duration': 131},
        {'title': 'The Terminator', 'description': 'Zientzia-fikzio thriller robot hiltzaile baten inguruan.', 'category_id': scifi.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/7/70/Terminator1984movieposter.jpg', 'duration': 107},
        {'title': 'The Hobbit', 'description': 'Fantasia abentura dragoi eta altxorraren bila.', 'category_id': fantasy.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/b/b3/The_Hobbit-_An_Unexpected_Journey.jpeg', 'duration': 169},
        {'title': 'Shrek', 'description': 'Animazio komikoa ogro eta printzesaren istorioan.', 'category_id': animation.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/4/4a/Shrek_%28film%29.jpg', 'duration': 90},
        {'title': 'Superbad', 'description': 'Komedia gazte eskola-urte amaierako abenturan.', 'category_id': comedy.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/5/50/Superbad_%28film%29_poster.jpg', 'duration': 113},
        {'title': 'Bohemian Rhapsody', 'description': 'Musika biografia Queen taldearen inguruan.', 'category_id': music.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/2/2e/Bohemian_Rhapsody_poster.png', 'duration': 134},
        {'title': 'The Conjuring', 'description': 'Horror erreala etxe hantutu baten inguruan.', 'category_id': horror.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/1/1f/Conjuring_poster.jpg', 'duration': 112},
        {'title': 'Pride and Prejudice', 'description': 'Romantzia klasikoa maitasun eta gizarte-normen artean.', 'category_id': romance.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/0/03/Prideandprejudiceposter.jpg', 'duration': 127},
        {'title': 'Goodfellas', 'description': 'Krimen-drama mafia-bizitzaren inguruan.', 'category_id': crime.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/7/7b/Goodfellas.jpg', 'duration': 146},
        {'title': 'Psycho', 'description': 'Thriller klasikoa motel eta hiltzaile baten inguruan.', 'category_id': thriller.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/b/b9/Psycho_%281960%29.jpg', 'duration': 109},
        {'title': 'John Wick', 'description': 'Akzio thriller hiltzaile ohia mendekatzen den istorioan.', 'category_id': action.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/9/98/John_Wick_TeaserPoster.jpg', 'duration': 101},
        {'title': 'Arrival', 'description': 'Zientzia-fikzio thriller alienen komunikazioaren inguruan.', 'category_id': scifi.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/d/df/Arrival%2C_Movie_Poster.jpg', 'duration': 116},
        {'title': 'The Chronicles of Narnia', 'description': 'Fantasia abentura mundu magikoan haurren bidaian.', 'category_id': fantasy.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/1/10/The_Chronicles_of_Narnia_-_The_Lion%2C_the_Witch_and_the_Wardrobe.jpg', 'duration': 140},
        {'title': 'Moana', 'description': 'Animazio abentura itsaso eta kultura polinesiarren inguruan.', 'category_id': animation.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/2/26/Moana_Teaser_Poster.jpg', 'duration': 107},
        {'title': 'Groundhog Day', 'description': 'Komedia fantastikoa egun bera errepikatzen den istorioan.', 'category_id': comedy.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/b/b1/Groundhog_Day_%28movie_poster%29.jpg', 'duration': 101},
        {'title': 'Amadeus', 'description': 'Musika drama Mozart eta salbazioaren inguruan.', 'category_id': music.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/5/5c/Amadeus_%281984%29_poster.jpg', 'duration': 160},
        {'title': 'It', 'description': 'Horror thriller umeentzako beldurra eta laguntasuna.', 'category_id': horror.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/5/5a/It_%282017%29_poster.jpg', 'duration': 135},
        {'title': 'Casablanca', 'description': 'Romantzia klasikoa bigarren mundu gerraren garaian.', 'category_id': romance.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/2/21/Casablanca_film_poster.jpg', 'duration': 102},
        {'title': 'The Usual Suspects', 'description': 'Krimen thriller polizia eta krimenaren inguruan.', 'category_id': crime.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/9/9c/Usual_suspects_ver1.jpg', 'duration': 106},
        {'title': 'Gone Girl', 'description': 'Thriller psikologikoa desagertze eta engainuaren inguruan.', 'category_id': thriller.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/0/05/Gone_Girl_Poster.jpg', 'duration': 149},
        {'title': 'Jumanji', 'description': 'Abentura dibertigarria joko magiko eta arriskuaren inguruan.', 'category_id': adventure.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/7/7c/Jumanji_welcome_to_the_jungle.png', 'duration': 119},
        {'title': 'The Mummy', 'description': 'Abentura akziozkoa antzinako madarikazio eta altxorraren bila.', 'category_id': adventure.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/5/5e/The_Mummy_%281999_film%29_poster.jpg', 'duration': 125},
        {'title': 'National Treasure', 'description': 'Abentura altxor historiko eta puzzleen inguruan.', 'category_id': adventure.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/a/a7/National_Treasure_poster.jpg', 'duration': 131},
        {'title': 'Dumb and Dumber', 'description': 'Komedia klasikoa bi lagun tontoen abenturan.', 'category_id': comedy.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/6/64/Dumbanddumber.jpg', 'duration': 107},
        {'title': 'Anchorman', 'description': 'Komedia 70eko hamarkadako telebista-aurkezlearen inguruan.', 'category_id': comedy.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/6/64/Anchorman_poster.jpg', 'duration': 104},
        {'title': 'The Greatest Showman', 'description': 'Musika eta ametsak zirkuaren munduan.', 'category_id': music.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/1/10/The_Greatest_Showman_poster.png', 'duration': 105},
        {'title': 'Moulin Rouge!', 'description': 'Musika eta maitasuna Pariseko kabaretean.', 'category_id': music.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/9/9e/Moulin_rouge_poster.jpg', 'duration': 126},
        {'title': 'The Shining', 'description': 'Horror psikologikoa hotel isolatu eta eromen baten inguruan.', 'category_id': horror.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/2/25/The_Shining_poster.jpg', 'duration': 146},
        {'title': 'Halloween', 'description': 'Horror klasikoa hiltzaile maskaradun baten inguruan.', 'category_id': horror.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/e/e9/Halloween_%282018_film%29_poster.png', 'duration': 106},
        {'title': 'The Notebook', 'description': 'Romantzia emozionala maitasun eta memoria galtzearekin.', 'category_id': romance.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/8/86/Posternotebook.jpg', 'duration': 123},
        {'title': 'Love Actually', 'description': 'Romantzia dibertigarria Londresko maitasun-istorio anitzekin.', 'category_id': romance.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/e/eb/Love_Actually_movie.jpg', 'duration': 135},
        {'title': 'Shutter Island', 'description': 'Thriller psikologikoa irla isolatu eta sekretuen inguruan.', 'category_id': thriller.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/7/7e/Shutter_Island_poster.jpg', 'duration': 138},
        {'title': 'Prisoners', 'description': 'Thriller tentsiozkoa desagertze eta justiziaren inguruan.', 'category_id': thriller.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/6/63/Prisoners_poster.jpg', 'duration': 153}
    ]

    existing_titles = {m.title for m in Movie.query.all()}
    movies_to_add = [Movie(**movie) for movie in default_movies if movie['title'] not in existing_titles]
    if movies_to_add:
        db.session.add_all(movies_to_add)
        db.session.commit()

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_default_movies()
    app.run(debug=True)
