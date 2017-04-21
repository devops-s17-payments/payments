#import logging
import re
from threading import Lock
from flask import jsonify, request, make_response, url_for
from flask_api import status    # HTTP Status Codes
from app import app
from app.db.interface import PaymentService,PaymentNotFoundError

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
            for key in request_args:
                request_args[key] = request_args[key][0]
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
    """
    Creates a Payment
    This endpoint will create a Payment based the data in the body that is posted
    ---
    tags:
      - Pets
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          id: data
          required:
            - nickname
            - payment_type
            - user_id
            - details
          properties:
            name:
              type: string
              description: your nickname of this Payment
            payment_type:
              type: string
              description: type of Payment (credit, debit, paypal)
            user_id:
                type: integer
                description: User foreign key
            details:
                type: dictionary
                description: details about your Payment (card_type, card_number, etc)
    responses:
      201:
        description: Payment created
        schema:
          id: Payment
          properties:
            id:
              type: integer
              description: unique id assigned internally by service
            nickname:
              type: string
              description: your Payment's nickname
            payment_type:
              type: string
              description: type of Payment (credit, debit, paypal)
            user_id:
                type: integer
                description: User foreign key
            details:
                type: dictionary
                description: details about your Payment (card_type, card_number, etc)
      400:
        description: Bad Request (the posted data was not valid)
    """
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
            raise DataValidationError('Invalid request: request not json')
        data = request.get_json()
        if data['payment_id']:
            resp = payment_service.perform_payment_action(user_id,payment_attributes=data)
            if resp == True:
                message = { 'success' : 'Payment with id: %s set as default for user with user_id: %s.' % (data['payment_id'], str(user_id)) }
                rc = HTTP_200_OK
            else:
                message = { 'error' : 'No Payment with id: %s was found for user with user_id: %s.' % (data['payment_id'], str(user_id)) }
                rc = HTTP_404_NOT_FOUND
    except DataValidationError as e:
        message = {'error' : e.message}
        rc = status.HTTP_400_BAD_REQUEST
    except KeyError as e:
        message = {'error' : 'Invalid request: body of request does not have the payment_id'}
        rc = status.HTTP_400_BAD_REQUEST
    #except PaymentNotFoundError as e:
    #    message = {'error' : e.message}
    #    rc = status.HTTP_404_NOT_FOUND

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
        message = 'Payment with id {} could not be found'.format(id)
        result = {'error': message }
        # place the id into the {} in the error message string
        #result['error'] = result['error'].format(id)
        rc = HTTP_404_NOT_FOUND


    return make_response(jsonify(result), rc)

######################################################################
# UPDATE AN EXISTING PAYMENT
######################################################################
@app.route('/payments/<int:id>', methods=['PUT'])
def update_payments(id):
    try:
        if not request.is_json:
            raise DataValidationError('Invalid payment: Content Type is not json')
        data = request.get_json(silent=True)
        message = payment_service.update_payment(id,payment_replacement=data)
        rc = HTTP_200_OK
    except PaymentNotFoundError as e:
        message = e.message
        rc = HTTP_404_NOT_FOUND
    except DataValidationError as e:
        message = e.message
        rc = HTTP_400_BAD_REQUEST
    return make_response(jsonify(message), rc)

######################################################################
# UPDATE AN EXISTING PAYMENT PARTIALLY
######################################################################
@app.route('/payments/<int:id>', methods=['PATCH'])
def update_partial_payments(id):
    try:
        if not request.is_json:
            raise DataValidationError('Invalid payment: Content Type is not json')
        data = request.get_json(silent=True)
        message = payment_service.update_payment(id,payment_attributes=data)
        rc = HTTP_200_OK
    except PaymentNotFoundError as e:
        message = e.message
        rc = HTTP_404_NOT_FOUND
    except DataValidationError as e:
        message = e.message
        rc = HTTP_400_BAD_REQUEST
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
@app.route('/payments/<int:user_id>/charge', methods=['PATCH'])
def charge_payment(user_id):
    try:
        if not request.data:
            raise DataValidationError('Invalid request: body of request contained no data')
        if not request.is_json:
            raise DataValidationError('Invalid request: request not json')
        data = request.get_json()
        if data['amount']:
            if(data['amount'] < 0):
                raise DataValidationError('Invalid request: Order amount is negative.')
            else:
                resp = payment_service.perform_payment_action(user_id,payment_attributes=data)
                if resp == True:
                    message = {'success' : 'Default payment method for user_id: %s has been charged $%.2f' % (str(user_id), data['amount'])}
                    rc = HTTP_200_OK
    except DataValidationError as e:
        message = {'error' : e.message}
        rc = HTTP_400_BAD_REQUEST
    except KeyError as e:
        message = {'error' : 'Invalid request: body of request does not have the amount to be charged'}
        rc = status.HTTP_400_BAD_REQUEST
    #except PaymentNotFoundError as e:
    #    message = {'error' : e.message}
    #    rc = status.HTTP_404_NOT_FOUND
    return make_response(jsonify(message), rc)
