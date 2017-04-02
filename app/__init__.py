from flask import Flask

# Create Flask application
app = Flask(__name__)
app.config.from_object('config')

import payments