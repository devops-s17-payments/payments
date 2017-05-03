from flask_sqlalchemy import SQLAlchemy

from app import app


app_db = SQLAlchemy(app)

'''
most import models AFTER db init
but BEFORE table creation
'''
from app.db import models

app_db.create_all()
app_db.session.commit()