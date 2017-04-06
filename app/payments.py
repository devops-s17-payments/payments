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
@app.route('/payments/<int:user_id>/set-default', methods=['PATCH'])
def set_default(user_id):
    try:
        if not request.data:
            raise DataValidationError('Invalid request: body of request contained no data')
        if not request.is_json:
            raise DataValidationError('Invalid request: body of request contained bad data')
        data = request.get_json()
        if not data['payment_id']:
            raise DataValidationError('Invalid request: body of request does not have the payment_id')
        else:
            resp = payment_service.perform_payment_action(user_id=user_id,payment_attributes=data)
            if resp == True:
                message = { 'success' : 'Payment with id: %s set as default for user with user_id: %s.' % (data['payment_id'], str(user_id)) }
                rc = HTTP_200_OK
            else:
                message = { 'error' : 'No Payment with id: %s was found for user with user_id: %s.' % (data['payment_id'], str(user_id)) }
                rc = HTTP_404_NOT_FOUND
    except Exception:
        message = {"error" : e.message}
        rc = status.HTTP_400_BAD_REQUEST
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
    index = [i for i, payment in enumerate(payments) if payment['id'] == id]
    if len(index) > 0:
        del payments[index[0]]
    return '', HTTP_204_NO_CONTENT

######################################################################
# CHARGE PAYMENT (ACTION)
######################################################################

@app.route('/payments/<int:user_id>/charge', methods=['PATCH'])
def charge_payment(user_id):
    try:
        if not request.data:
            raise DataValidationError('Invalid payment: body of request contained bad or no data')
        if not request.is_json:
            raise DataValidationError('Invalid payment: body of request contained bad or no data')
        data = request.get_json()
        if not data['amount']:
            raise DataValidationError('Invalid request: body of request does not have the amount')
        elif (data['amount'] < 0):
            raise DataValidationError('Invalid order amount. Transaction cancelled. Please check your order and try again.')
        else:
            resp = payment_service.perform_payment_action(user_id=user_id, payment_attributes=data)
            if resp == True:
                message = {'success' : 'Default payment method for user_id: %s has been charged $%.2f' % (str(user_id), data['amount'])}
                rc = HTTP_200_OK
    except Exception:

'''
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
'''
    return make_response(jsonify(message), rc)


######################################################################
#   U T I L I T I E S
######################################################################
"""
Commenting this out as it is not being used currently
def index_inc():
    global current_payment_id
    with lock:
        current_payment_id += 1
    return current_payment_id
"""

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
