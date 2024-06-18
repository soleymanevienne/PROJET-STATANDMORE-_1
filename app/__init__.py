from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os
from datetime import timedelta

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration de l'application Flask
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///instance/yourdatabase.db')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'yoursecretkey')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    with app.app_context():
        from . import routes, models
        db.create_all()
    
    return app
