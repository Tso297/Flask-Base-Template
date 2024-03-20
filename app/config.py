import os

basedir = os.path.abspath(os.path.dirname(__name__))

class Config():
    FLASK_APP=os.environ.get('FLASK_APP')
    FLASK_DEBUG=os.environ.get('FLASK_DEBUG')
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    SECRET_KEY=os.environ.get('SECRET_KEY')