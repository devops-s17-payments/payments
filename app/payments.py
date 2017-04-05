#import logging
import re
from datetime import datetime, timedelta
from threading import Lock
from flask import jsonify, request, make_response, url_for
from flask_api import status    # HTTP Status Codes

from app import app
from app.db.interface import PaymentService
from app.error_handlers import DataValidationError

# Instantiate persistence service to be used in CRUD methods
payment_service = PaymentService()

# placeholder to be removed during refactoring of CRUD methods
payments = []
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
# this will move to error_handlers during refactor
CONTENT_ERR_MSG = "If you see this, something needs to be refactored in payments.py"

# Error bodies
NOT_FOUND_ERROR_BODY = {'error': 'Payment with id {} could not be found'}
GENERAL_NOT_FOUND_ERROR = {'error': 'Requested resource(s) could not be found'}

######################################################################
# GET INDEX
######################################################################
@app.route('/')
def index():
    payments_url = request.base_url + "payments"
    return app.send_static_file('index.html')

######################################################################
# LIST ALL PAYMENTS
######################################################################
@app.route('/payments', methods=['GET'])
def list_payments():
    request_args = request.args

    try:
        if 'ids' in request_args:
            # just retrieve a list of payments where each payment corresponds to one of the ids
            ids = request_args.getlist('ids', type=int)
            results = payment_service.get_payments(payment_ids=ids)

        elif request_args:
            # if there is anything else in the request args, query by those parameters;
            # flask puts the request_args into a proprietary data structure called ImmutableMultiDict
            # this cast allows us to make a simple dictionary where each query param is a key and the
            # value is a list that contains the value(s) of that query parameter
            request_args = dict(request_args)
            results = payment_service.get_payments(payment_attributes=request_args)

        else:
            # if no request args are present, simply return all payments
            results = payment_service.get_payments()

        return make_response(jsonify(results), HTTP_200_OK)

    except Exception:
        # we will want to make more specific exception handling later in order to differentiate
        # the case in which it's a 404 and the case where it's a 400 - we'll assume for now that
        # the client makes good requests for resources that may or may not exist
        return make_response(jsonify(GENERAL_NOT_FOUND_ERROR), HTTP_404_NOT_FOUND)

######################################################################
# CREATE PAYMENT
######################################################################
@app.route('/payments', methods=['POST'])
def create_payment():
    """ if get_json fails, no exception raised. returns None """
    data = request.get_json(silent=True)
    try:
        payment = payment_service.add_payment(data)
        rc = status.HTTP_201_CREATED
        message = {"created" : payment}
    except DataValidationError as e:
        message = {"error" : e.message}
        rc = status.HTTP_400_BAD_REQUEST
    return make_response(jsonify(message), rc)

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
    try:
        result = payment_service.get_payments(payment_ids=[id])
        rc = HTTP_200_OK
    except Exception:
        result = NOT_FOUND_ERROR_BODY
        # place the id into the {} in the error message string
        result['error'] = result['error'].format(id)
        rc = HTTP_404_NOT_FOUND

    return make_response(jsonify(result), rc)

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
    payment_service.remove_payment(payment_id=id)
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
            #TO DO: perform validation of e-mail
            email = detail['e-mail']
            valid_detail = True
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
