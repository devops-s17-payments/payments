import os
from app import app

# Pull options from environment
debug = (os.getenv('DEBUG', 'False') == 'True')
port = os.getenv('PORT', '5000')

######################################################################
#   M A I N
######################################################################
if __name__ == "__main__":
    print "Starting Payments service..."
    app.run(host='0.0.0.0', port=int(port), debug=debug)

