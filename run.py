import os
from app import app

if __name__ == '__main__':
    print 'Starting payments app'
    debug = (os.getenv('DEBUG', 'False') == 'True')
    port = os.getenv('PORT', '5000')
    app.run(host='0.0.0.0', port=int(port), debug=debug)
