import os
#import logging
from datetime import datetime, timedelta
from threading import Lock
import re
import time
from flask import Flask, jsonify, request, make_response, Response, json, url_for

# Create Flask application
app = Flask(__name__)
#app.config['LOGGING_LEVEL'] = logging.INFO

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
			 'type' : 'credit', 'charge-history': 0.00, 'detail' : credit},
			{'id' : 2, 'default' : False, 'nickname' : 'my-debit',
			 'type' : 'debit', 'charge-history': 0.00,'detail' : debit},
			{'id' : 3, 'default' : False, 'nickname' : 'my-paypal',
			 'type' : 'paypal', 'charge-history': 0.00,'detail' : paypal}]

######################################################################
# GET INDEX
######################################################################
@app.route('/')
def index():
	payments_url = request.base_url + "payments"
	#to do: change this to work with remplates
	#need to reorganize directory
	return app.send_static_file('index.html')

######################################################################
# LIST ALL PAYMENTS
######################################################################
@app.route('/payments', methods=['GET'])
def list_payments():
	if request.query_string != "":
		return query_payments()
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
	data = request.get_json(silent=True)
	if data is None:
		return make_response(CONTENT_ERR_MSG, HTTP_400_BAD_REQUEST)

	if is_valid(data):
		id = index_inc()
    
		newData = {'id' : id, 'default' : False, 'charge-history' : 0.0, 
               'nickname' : data['nickname'], 'type' : data['type'], 'detail' : data['detail']}
  
		payments.append(newData)
		message = {'successfully created' : payments[len(payments)-1]}
		rc = HTTP_201_CREATED
	else:
		message = {'error' : 'Data is not valid.' }
		rc = HTTP_400_BAD_REQUEST
	
	response = make_response(jsonify(message), rc)
	if rc == HTTP_201_CREATED:
		response.headers['Location'] = url_for('get_payments', id = id)
	return response

######################################################################
# SET DEFAULT PAYMENT (ACTION)
######################################################################
@app.route('/payments/<int:id>/set-default', methods=['PUT'])
def set_default(id):
	if id > current_payment_id or id < 1:
		message = { 'error' : 'Payment with id: %s was not found' % str(id) }
		rc = HTTP_404_NOT_FOUND
	else:
		index = [i for i, payment in enumerate(payments) if payment['id'] == id]
		if len(index) <= 0:
			message = { 'error' : 'Payment with id: %s was not found' % str(id) }
			rc = HTTP_404_NOT_FOUND
		else:
			for payment in payments:
				payment['default'] = False
			payments[index[0]]['default'] = True
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
# RETRIEVE A PAYMENT ON QUERY
######################################################################
def query_payments():

	q = request.query_string
	key = re.search('\w*', q)
	key = key.group(0)			
	value = re.search('=\w*', q)
	value = value.group(0)[1::]

	list=[]
	for p in payments:
		if p.has_key(key):
			if p[key] == value:
				list.append(p)
		else:
			message = { 'error' : '%s is not a valid key' % key }
			rc = HTTP_404_NOT_FOUND
			return make_response(jsonify(message), rc)
	
	if len(list) > 0:
   		message = list
   		rc = HTTP_200_OK
	else:
   		message = { 'error' : 'Payment with %s: %s was not found' % (key,value) }
   		rc = HTTP_404_NOT_FOUND
   	return make_response(jsonify(message), rc)

######################################################################
# UPDATE AN EXISTING PAYMENT
######################################################################
@app.route('/payments/<int:id>', methods=['PUT'])
def update_payments(id):
    index = [i for i, payment in enumerate(payments) if payment['id'] == id]
    if len(index) > 0:
        if not request.is_json:
    		return make_response(CONTENT_ERR_MSG, HTTP_400_BAD_REQUEST)
        payload = request.get_json()
        if is_valid(payload):
            payments[index[0]] = {'id' : id, 'nickname' : payload['nickname'], 'type' : payload['type'],
            					  'default' : payments[index[0]]['default'],
            					  'charge-history' : payments[index[0]]['charge-history'],
            					  'detail' : payload['detail']}
            message = payments[index[0]]
            rc = HTTP_200_OK
        else:
            message = { 'error' : 'Payments data was not valid' }
            rc = HTTP_400_BAD_REQUEST
    else:
        message = { 'error' : 'Payments %s was not found' % id }
        rc = HTTP_404_NOT_FOUND

    return make_response(jsonify(message), rc)

######################################################################
# UPDATE AN EXISTING PAYMENT PARTIALLY
######################################################################
@app.route('/payments/<int:id>', methods=['PATCH'])
def update_partial_payments(id):
    index = [i for i, payment in enumerate(payments) if payment['id'] == id]
    if len(index) > 0:
        if not request.is_json:
    		    return make_response(CONTENT_ERR_MSG, HTTP_400_BAD_REQUEST)
        payload = request.get_json()
        if is_valid_patch(payload):
            target_payment = payments[index[0]]
            # for now, can only update partially with nickname, type and detail
            payload_nickname = target_payment['nickname'] if 'nickname' not in payload else payload['nickname']
            payload_type = target_payment['type'] if 'type' not in payload else payload['type']
            payload_detail = target_payment['detail'] if 'detail' not in payload else payload['detail']
            payments[index[0]] = {'id' : id, 'nickname' : payload_nickname, 'default' : target_payment['default'], 
                'charge-history' : target_payment['charge-history'], 'type' : payload_type, 'detail' : payload_detail}
            message = payments[index[0]]
            rc = HTTP_200_OK
        else:
            message = { 'error' : 'Payments data was not valid' }
            rc = HTTP_400_BAD_REQUEST
    else:
        message = { 'error' : 'Payments %s was not found' % id }
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
# CHARGE PAYMENT (ACTION)
######################################################################

@app.route('/payments/charge', methods=['PUT'])
def charge_payment():
	rc = HTTP_400_BAD_REQUEST
	charge = request.get_json(silent=True)
	if charge is None:
		return make_response(CONTENT_ERR_MSG, rc)
	if not is_positive(charge['amount']):
		message = {'error' : ('Invalid order amount. Transaction cancelled. ', 
							  'Please check your order and try again.')}
	else:
		index = [i for i, payment in enumerate(payments) if payment['default']]
		if len(index) < 1:
			message = {'error' : 'No default payment method selected. Transaction cancelled'}
			return make_response(jsonify(message), rc)
		p = payments[index[0]]
		
		if p['type'] == 'paypal' and not p['detail']['linked']:
			message = {'error' : ('Your paypal account has not been linked. Transaction cancelled. ', 
								  'Please update your account and try your order again.')}
		elif p['type'] != 'paypal' and is_expired(p):
			message = {'error' : ('Your credit/debit card has expired. Transaction cancelled. ', 
								  'Please update your account and try your order again.')}
		else:
			p['charge-history'] = p['charge-history'] + charge['amount']
			message = {'success' : 'Your payment method %s has been charged $%.2f' % (p['nickname'], charge['amount'])}
			rc = HTTP_200_OK
	
	return make_response(jsonify(message), rc)


######################################################################
#   U T I L I T I E S
######################################################################
def index_inc():
	global current_payment_id
	with lock:
		current_payment_id += 1
	return current_payment_id

def is_valid(data):
	valid = False
	valid_detail = False
	try:
		nickname = data['nickname']
		type = data['type']
		detail = data['detail']

		if bool(re.search(r'\d', detail['name'])) == False:
			valid = True

		if type == 'credit' or type == 'debit':
			name = detail['name']
			card_number = detail['number']
			expires_date = detail['expires']
			subtype = detail['type']
			if bool(re.match('^[0-9]+$', card_number)) and (len(card_number) == 16):
				datetime.strptime(expires_date, '%m/%Y')
				valid_detail = True
		else:
			name = detail['name']
			email = detail['e-mail']
			linked = detail['linked']
			valid_detail = True;
    #except KeyError as err:
    #app.logger.warn('Missing parameter error: %s', err)
    #    pass
    #except TypeError:
    #app.logger.warn('Invalid Content Type error')
    #    pass
    #except ValueError:
    #app.logger.warn('Invalid Content Type error')
    #   pass
	except:
		pass
	return valid & valid_detail

def is_expired(payment):
	#get datetime object for last day of expiring month
	exp_date = payment['detail']['expires']
	month = int(exp_date[:2]) + 1
	exp_date = '%s%s' % (month, exp_date[2:])
	exp_date = datetime.strptime(exp_date, '%m/%Y')
	exp_date = exp_date - timedelta(1)
	exp_date = datetime.date(exp_date)

	now = datetime.now()
	now = datetime.date(now)

	if(now < exp_date):
		return False
	else:
		return True

def is_positive(amount):
	if(amount > 0):
		return True
	else:
		return False

def is_valid_patch(data):
	#update later for validating data for PATCH method
	return True

######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
	debug = (os.getenv('DEBUG', 'False') == 'True')
	port = os.getenv('PORT', '5000')
	app.run(host='0.0.0.0', port=int(port), debug=debug)
