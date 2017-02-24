import os
import logging
from threading import Lock
from flask import Flask, jsonify, request, make_response, Response, json, url_for

# Create Flask application
app = Flask(__name__)
app.config['LOGGING_LEVEL'] = logging.INFO

# Lock for thread-safe counter increment
lock = Lock()

# Status Codes
# will be replaced eventually
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409

# Error Messages
CONTENT_ERR_MSG = "Content type of the request is not json. Doesn't support other formats now."

#starter payment models for mvp
#dummy data
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

payments = [{'id' : 1, 'default' : True, 'nickname' : 'my-credit',
			 'type' : 'credit', 'detail' : credit},
			{'id' : 2, 'default' : False, 'nickname' : 'my-debit',
			 'type' : 'debit', 'detail' : debit},
			{'id' : 3, 'default' : False, 'nickname' : 'my-paypal',
			 'type' : 'paypal', 'detail' : paypal}]

######################################################################
# GET INDEX
######################################################################
@app.route('/')
def index():
	payments_url = request.base_url + "payments"
	return jsonify(name='Welcome to the Payments API',
				   version='1.0',
				   url=payments_url), HTTP_200_OK

######################################################################
# LIST ALL PAYMENTS
######################################################################
@app.route('/payments', methods=['GET'])
def list_payments():
    results = []
    type = request.args.get('type')
    if type:
        results = [payment for payment in payments if payment['type'] == type]
    else:
        results = payments

    return make_response(jsonify(results), HTTP_200_OK)

######################################################################
# ADD A NEW PAYMENT
######################################################################
@app.route('/payments', methods=['POST'])
def add_payment():
	if not request.is_json:
		make_response(CONTENT_ERR_MSG, HTTP_400_BAD_REQUEST)
	data = request.get_json()
	#haven't figure out why this doesn't work yet
	#data = {'nickname' : 'new-payment', 'type' : 'credit',
	#		'detail' : {'name' : 'Jimmy Jones', 'number' : '1111222233334444',
	#					'expires' : '01/2019', 'type' : 'Mastercard'}}
	
	#to-do: will refactor to put this logic in is_valid utility function
	try:
		id = index_inc()
		newData = {'id' : id, 'name' : data['nickname'], 'type' : data['type'], 'detail' : data['detail']}
		payments.append(newData)
		message = {'successfully created' : payments[id-1]}
		rc = HTTP_201_CREATED
	except KeyError as err:
		message = {'error' : ('Missing parameter error: %s', err) }
		rc = HTTP_400_BAD_REQUEST
	
	return make_response(jsonify(message), rc)

######################################################################
# SET DEFAULT PAYMENT
######################################################################
@app.route('/payments/<int:id>/set-default', methods=['PUT'])
def set_default(id):
	if id > current_payment_id or id < 1:
		message = { 'error' : 'Payment with id: %s was not found' % str(id) }
		rc = HTTP_404_NOT_FOUND
	else:
		for payment in payments:
			if payment['id'] == id:
				payment['default'] = True
			else:
				payment['default'] = False
		message = { 'success' : 'Payment with id: %s set as default.' % str(id) }
		rc = HTTP_200_OK

	return make_response(jsonify(message), rc)

######################################################################
# RETRIEVE A PAYMENT
######################################################################
@app.route('/payments/<int:id>', methods=['GET'])
def get_payments(id):
    index = [i for i, payment in enumerate(payments) if payment['id'] == id]
    if len(index) > 0:
        message = payments[index[0]]
        rc = HTTP_200_OK
    else:
        message = { 'error' : 'Payment with id: %s was not found' % str(id) }
        rc = HTTP_404_NOT_FOUND

    return make_response(jsonify(message), rc)

######################################################################
# DELETE A PAYMENT
######################################################################
@app.route('/payments/<int:id>', methods=['DELETE'])
def delete_payments(id):
    index = [i for i, payment in enumerate(payments) if payment['id'] == id]
    if len(index) > 0:
        del payments[index[0]]
    return '', HTTP_204_NO_CONTENT

######################################################################
#   U T I L I T I E S
######################################################################
def index_inc():
    global current_payment_id
    with lock:
        current_payment_id += 1
    return current_payment_id

def is_valid(data):
	pass

######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
	debug = (os.getenv('DEBUG', 'False') == 'True')
	port = os.getenv('PORT', '5000')
	app.run(host='0.0.0.0', port=int(port), debug=debug)
