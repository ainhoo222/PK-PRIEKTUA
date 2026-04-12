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
    avatar = db.Column(db.String(10), default='👤')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    poster = db.Column(db.String(500))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref='movies')

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)

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
        data = request.get_json()
        if Movie.query.filter_by(title=data['title']).first():
            return jsonify({'message': 'Pelikula hau jada existitzen da'}), 400
        new_movie = Movie(
            title=data['title'],
            description=data.get('description', ''),
            poster=data.get('poster', ''),
            category_id=data.get('category_id')
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
            'category': {'id': m.category.id, 'name': m.category.name} if m.category else None
        })
    return jsonify(result)

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
        {'title': 'Gladiator', 'description': 'Gladiatzaile bati buruzko film epikoa antzinako Erroman.', 'category_id': action.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/8/8d/Gladiator_ver1.jpg'},
        {'title': 'Interstellar', 'description': 'Espazio-bidaia eta denborazko sakontasunak deskubritzen dituen zientzia-fikzio filma.', 'category_id': scifi.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/b/bc/Interstellar_film_poster.jpg'},
        {'title': 'Inception', 'description': 'Ametsak manipulatu eta errealitatea zalantzan jartzen duen thriller psikologikoa.', 'category_id': scifi.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/7/7f/Inception_ver3.jpg'},
        {'title': 'The Matrix', 'description': 'Erlaitzaren aurrealdeari eta sistema faltsu bati buruzko zientzia-fikzio klasikoa.', 'category_id': scifi.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/c/c1/The_Matrix_Poster.jpg'},
        {'title': 'The Dark Knight', 'description': 'Batman eta Jokerren arteko ospea eta drama.' , 'category_id': action.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/8/8a/Dark_Knight.jpg'},
        {'title': 'The Lord of the Rings', 'description': 'Fantasia-epika mundu magiko batean, abentura handia.', 'category_id': fantasy.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/8/87/Ringstrilogy.jpg'},
        {'title': 'Parasite', 'description': 'Klase sozialen arteko tentsioa eta umorea beltza uztartzen dituen drama.', 'category_id': drama.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/5/53/Parasite_%282019_film%29.png'},
        {'title': 'Indiana Jones', 'description': 'Abentura klasikoa altxorra aurkitzeari eta arriskuari buruz.', 'category_id': adventure.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/a/a0/Raiders_of_the_Lost_Ark_poster.jpg'},
        {'title': 'The Shawshank Redemption', 'description': 'Esperantza eta askatasuna bilatzen duen kartzela-drama harrigarria.', 'category_id': drama.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/8/81/ShawshankRedemptionMoviePoster.jpg'},
        {'title': 'Forrest Gump', 'description': 'Mundu modernoaren historia ikuspegi xume eta bihotzez inguruan.', 'category_id': drama.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/6/67/Forrest_Gump_poster.jpg'},
        {'title': 'The Godfather', 'description': 'Mafia-familia boteretsu baten boterea eta leialtasuna aztertzen duen klasikoa.', 'category_id': crime.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/1/1c/Godfather_ver1.jpg'},
        {'title': 'Pulp Fiction', 'description': 'Krimen-ezohiko hurbilpena eta hizkera berezia lotzen dituen filma.', 'category_id': crime.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/3/3b/Pulp_Fiction_%281994%29_poster.jpg'},
        {'title': 'The Silence of the Lambs', 'description': 'Polizia ikerketa ilun bat eta psikopata baten arteko tentsioa.', 'category_id': thriller.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/8/86/The_Silence_of_the_Lambs_poster.jpg'},
        {'title': 'The Prestige', 'description': 'Bi magia-maisuen arteko lehia ezezagun eta trikimailu betean.', 'category_id': drama.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/d/d2/Prestige_poster.jpg'},
        {'title': 'Avatar', 'description': 'Mundu alienigenaren eta gizateriaren arteko borroka ikusgarria.', 'category_id': fantasy.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/b/b0/Avatar-Teaser-Poster.jpg'},
        {'title': 'The Lion King', 'description': 'Animazio epikoa familia, koroa eta nortasuna aztertzen duena.', 'category_id': animation.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/3/3d/The_Lion_King_poster.jpg'},
        {'title': 'Spirited Away', 'description': 'Japoniako animazio magia eta txikien bidaia liluragarria.', 'category_id': animation.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/3/32/Spirited_Away_poster.JPG'},
        {'title': 'Back to the Future', 'description': 'Denboran atzera bidaia dibertigarria eta arriskuak dakartzan abentura.', 'category_id': scifi.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/d/d2/Back_to_the_Future.jpg'},
        {'title': 'Mad Max: Fury Road', 'description': 'Aurrekaririk gabea den post-apokaliptiko akzio-bidaia.', 'category_id': action.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/6/6e/Mad_Max_Fury_Road.jpg'},
        {'title': 'The Departed', 'description': 'Polizia eta mafiosoen artean zurien eta beltzen joko latza.', 'category_id': crime.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/5/50/Departed234.jpg'},
        {'title': 'The Grand Budapest Hotel', 'description': 'Komedia dotorea, bidaia eta misterio artean murgiltzen den istorioa.', 'category_id': comedy.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/a/a6/The_Grand_Budapest_Hotel_Poster.jpg'},
        {'title': 'La La Land', 'description': 'Musika, ametsak eta maitasuna Los Angeleseko eszena batean.', 'category_id': music.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/a/ab/La_La_Land_%28film%29.png'},
        {'title': 'Get Out', 'description': 'Horror sozial bortitza eta tentsio mentala uztartzen duen filma.', 'category_id': horror.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/e/eb/Get_Out_poster.png'},
        {'title': 'The Truman Show', 'description': 'Errealitate simulatu eta norberaren identitatea aztertzen duen zientzia-fikzioa.', 'category_id': scifi.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/c/cd/The_Truman_Show.jpg'},
        {'title': 'Blade Runner 2049', 'description': 'Etorkizun distopikoa eta gizakiaren zentzua arakatzen duen sekuela.', 'category_id': scifi.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/9/9b/Blade_Runner_2049_poster.png'},
        {'title': 'The Social Network', 'description': 'Sare sozialen sorrera eta boterearen garestia kontatzen duen drama.', 'category_id': drama.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/7/7c/Social_network_film_poster.jpg'},
        {'title': 'Jurassic Park', 'description': 'Dinosaurioen berpizkundea eta abentura izango dituen parkean.', 'category_id': adventure.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/e/e7/Jurassic_Park_poster.jpg'},
        {'title': 'The Avengers', 'description': 'Superheroi taldeak unibertsoa salbatzeko elkartzen diren akziozko apustua.', 'category_id': action.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/f/f9/TheAvengers2012Poster.jpg'},
        {'title': 'Toy Story', 'description': 'Jostailuek beren bizitza duela sinesten duten bihotzezko animazioa.', 'category_id': animation.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/1/13/Toy_Story.jpg'},
        {'title': 'Guardians of the Galaxy', 'description': 'Espazio akzioa eta umorea elkartzen dituen talde bizia.', 'category_id': action.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/b/b5/Guardians_of_the_Galaxy_poster.jpg'},
        {'title': 'Black Panther', 'description': 'Erritmoak, kultura eta akzio modernoaren arteko ondoan egindako superheroi filma.', 'category_id': action.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/0/0c/Black_Panther_film_poster.jpg'},
        {'title': 'Titanic', 'description': 'Urperatzearen eta maitasunik gabeko kontakizun dramatikoa.', 'category_id': romance.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/2/22/Titanic_poster.jpg'},
        {'title': 'The Wizard of Oz', 'description': 'Fantasia klasikoa non ausardia, bihotza eta burujabetza aurkitzen diren.', 'category_id': fantasy.id, 'poster': 'https://upload.wikimedia.org/wikipedia/en/c/c9/The_Wizard_of_Oz_1939_poster.jpg'}
    ]

    existing_titles = {m.title for m in Movie.query.all()}
    movies_to_add = [Movie(**movie) for movie in default_movies if movie['title'] not in existing_titles]
    if movies_to_add:
        db.session.add_all(movies_to_add)
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_default_movies()
    app.run(debug=True)
