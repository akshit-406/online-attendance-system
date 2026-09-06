from flask import Flask
from flask_login import LoginManager
import os
from models import db, User


app = Flask(__name__)


# --------------------------------
# Configuration
# --------------------------------

app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'dev-secret-key'
)

database_url = os.environ.get('DATABASE_URL')

if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# --------------------------------
# Database
# --------------------------------

db.init_app(app)


# --------------------------------
# Flask Login
# --------------------------------

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = 'main.login'


@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))


# --------------------------------
# Create Database
# --------------------------------

with app.app_context():
    db.create_all()


# --------------------------------
# Register Routes
# --------------------------------

from routes import main

app.register_blueprint(main)


# --------------------------------
# Run Application
# --------------------------------

if __name__ == '__main__':

    app.run()