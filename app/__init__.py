from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app) #only if using a DB
migrate = Migrate(app,db)# only if using a DB
cors = CORS(app)# only if you plan to connect this elsewhere unless this is 100% flask oriented within itself.

from . import models

from .api import api

app.register_blueprint(api)