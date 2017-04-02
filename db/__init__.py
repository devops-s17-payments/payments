from flask_sqlalchemy import SQLAlchemy
from payments import app

'''
db connection string current in config, but will implement a way to get from environ
'''


db = SQLAlchemy(app)