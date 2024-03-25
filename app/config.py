import os

basedir = os.path.abspath(os.path.dirname(__name__))

class Config():
    FLASK_APP=os.environ.get('FLASK_APP')
    FLASK_DEBUG=os.environ.get('FLASK_DEBUG')
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL') #only if you have a database
    SQLALCHEMY_TRACK_MODIFICATIONS=False #only if you have a database
    SECRET_KEY=os.environ.get('SECRET_KEY') #only if you have forms