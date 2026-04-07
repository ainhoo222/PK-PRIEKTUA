from app import app, db, Category

with app.app_context():
    kategoria_izenak = ['Akzioa', 'Komedia', 'Drama', 'Zientzia fikzioa', 'Beldurrezkoa']
    for izena in kategoria_izenak:
        if not Category.query.filter_by(name=izena).first():
            db.session.add(Category(name=izena))
    db.session.commit()
    print("Kategoriak gehituta")
