from flask_sqlalchemy import SQLAlchemy

from app import app

'''
db connection string current in config, but will implement a way to get from environ
'''

app_db = SQLAlchemy(app)