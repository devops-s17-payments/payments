from flask import Flask
from flasgger import Swagger

# Create Flask application
app = Flask(__name__)
app.config.from_object('config')
swag = Swagger(app)

import payments
