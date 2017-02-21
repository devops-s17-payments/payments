from flask import Flask, jsonify, request
import os

# Create Flask application
app = Flask(__name__)

# Status Codes
# will be replaced eventually
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409

@app.route('/')
def index():
	payments_url = request.base_url + "payments"
	return jsonify(name='Welcome to the Payments API',
				   version='1.0',
				   url=payments_url), HTTP_200_OK

####################
# RETRIEVE PAYMENT #
####################
@app.route('/payments/<int:id>', methods=['GET'])
def get_payments(id):
	if payments.has_key(id):
		message = payments[id]
		code = HTTP_200_OK
	else:
		message = 'Error: Payment id %s does not exist' % str(id)
		code = HTTP_404_NOT_FOUND
	
	#DOB: this should be refactored eventually... need some utility functions
	return jsonify(data=message), code

##########################
########## MAIN ##########
##########################
if __name__ == '__main__':
	#starter payment models for mvp
	current_payment_id = 3;
	
	credit = {'name' : 'John Johnson',
			  'number' : '1234567898765432',
			  'expires' : '01/2020',
			  'type' : 'American Express'}
	
	debit = {'name' : 'Jane Jenkins',
			 'number' : '9876543212345678',
			 'expires' : '08/2018',
			 'type' : "Visa"}
	
	paypal = {'name' : 'Joe Jetson',
			  'e-mail' : 'joe@aol.com',
			  'linked' : True}

	payments = {1: {'nickname' : 'my-credit', 'type' : 'credit', 'detail' : credit},
				2: {'nickname' : 'my-debit', 'type' : 'debit', 'detail' : debit},
				3: {'nickname' : 'my-paypal', 'type' : 'paypal', 'detail' : paypal}}

	debug = (os.getenv('DEBUG', 'False') == 'True')
	port = os.getenv('PORT', '5000')
	app.run(host='0.0.0.0', port=int(port), debug=debug)
