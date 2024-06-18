from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialisation de l'application Flask et configuration de la base de données
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yourdatabase.db'
app.config['SECRET_KEY'] = 'yoursecretkey'
db = SQLAlchemy(app)

# Définition du modèle User pour représenter les utilisateurs dans la base de données
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    avatar = db.Column(db.String(150), nullable=True)

# Contexte de l'application Flask pour exécuter les commandes liées à la base de données
with app.app_context():
    # Réinitialise la base de données en supprimant toutes les tables existantes et en créant de nouvelles tables
    db.drop_all()
    db.create_all()
    print("La base de données a été réinitialisée.")
