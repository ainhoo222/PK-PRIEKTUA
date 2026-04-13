import sys
import os
sys.path.insert(0, os.getcwd())
from app import app, db, Comment

# Clear any existing models
db.metadata.clear()

# Reimport the models
from app import User, Category, Movie, Favorite

# Create all tables
with app.app_context():
    db.create_all()
    
    # Verify the User table has the avatar column
    inspector = db.inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('user')]
    print(f'Columnas en tabla user: {columns}')
    if 'avatar' in columns:
        print('? Columna avatar creada correctamente')
    else:
        print('? Error: avatar column not found')
