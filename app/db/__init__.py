from flask_sqlalchemy import SQLAlchemy
from app import app

db = SQLAlchemy(app)
db.create_all()

import models, interface