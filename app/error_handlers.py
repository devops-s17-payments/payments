from flask import jsonify, make_response
from flask_api import status    # HTTP Status Codes
from app import app

######################################################################
# Custom Exceptions
######################################################################
class DataValidationError(ValueError):
    pass

######################################################################
# ERROR Handling
######################################################################

@app.errorhandler(DataValidationError)
def request_validation_error(e):
    return make_response(jsonify(status=400, error='Bad Request', message=e.message), status.HTTP_400_BAD_REQUEST)

@app.errorhandler(404)
def not_found(e):
    return make_response(jsonify(status=404, error='Not Found', message=e.description), status.HTTP_404_NOT_FOUND)

@app.errorhandler(400)
def bad_request(e):
    return make_response(jsonify(status=400, error='Bad Request', message=e.message), status.HTTP_400_BAD_REQUEST)

@app.errorhandler(405)
def method_not_allowed(e):
    return make_response(jsonify(status=405, error='Method not Allowed', message='Your request method is not supported. Check your HTTP method and try again.'), status.HTTP_405_METHOD_NOT_ALLOWED)

@app.errorhandler(500)
def internal_error(e):
	return make_response(jsonify(status=500, error='Internal Server Error', message='Well, this is embarrassing...'), status.HTTP_500_INTERNAL_SERVER_ERROR)

class InvalidPaymentID(Exception):
    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
