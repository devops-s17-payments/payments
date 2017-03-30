from flask_sqlalchemy import SQLAlchemy
from payments import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/dev.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)