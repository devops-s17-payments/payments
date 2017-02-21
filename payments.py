from flask import Flask
import os

# Create Flask application
app = Flask(__name__)

@app.route('/')
def index():
	return 'this works'

if __name__ == '__main__':
    debug = (os.getenv('DEBUG', 'False') == 'True')
    port = os.getenv('PORT', '5000')
    app.run(host='0.0.0.0', port=int(port), debug=debug)
