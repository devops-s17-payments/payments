from flask_sqlalchemy import SQLAlchemy

from app import app

'''
db connection string current in config, but will implement a way to get from environ
'''

app_db = SQLAlchemy(app)

'''
most import models AFTER db init
but before table creation
'''
from app.db import models

app_db.create_all()
app_db.session.commit()