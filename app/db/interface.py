# -*- coding:utf-8 -*-

import re
from datetime import datetime
from sqlalchemy import exc

from app.db.models import Payment, Detail
from app.error_handlers import DataValidationError
from app.db import app_db
from sqlalchemy import exc
from datetime import datetime, timedelta

class PaymentService(object):
    """
    Serves as an interface which takes requests from the front-end
    and runs the corresponding actions in the database.
    """
    UPDATABLE_PAYMENT_FIELDS = [ 'nickname','payment_type','defaults']
    NONUPDATABLE_PAYMENT_RREQUEST_FIELDS = [ 'is_default','is_removed','charge_history']
    def __init__(self):
        """
        Initialize connection to database here.
        """
        self.db = app_db

    def add_payment(self, payment_data):
        """
        Takes a dictionary of payment parameters and creates a new
        payment item in the database using those parameters' data.

        :param payment_data: <dict> a validated JSON payload that describes a new Payment object
        """
        p = Payment()

        try:
            p.deserialize(payment_data)
        except DataValidationError as e:
            raise DataValidationError(e.message)
        self.db.session.add(p)
        self.db.session.commit()
        return p.serialize()
    def remove_payment(self, payment_id=None, payment_attributes=None):
        """
        Accepts an id or a variable number of keyword arguments (in payment_attributes)
        that could be used to identify a payment if the id is
        not known.

        :param payment_id: <int> the unique identifier of a payment to be removed
        :param payment_attributes: <dict> a collection of payment attributes to identify the payment

        Currently only supports finding payment with the id specified

        """

        payment = self.db.session.query(Payment).get(payment_id)
        if payment:
            """
            payment_to_be_deleted = payment.serialize()
            payment_to_be_deleted['is_removed'] = True
            payment.deserialize_put(payment_to_be_deleted)
            """
            #workaround for deserialize_put as it always has is_removed = False
            payment.is_removed = True
            """
            self.db.session.delete(payment)
            """
            self.db.session.commit()

    def update_payment(self, payment_id, payment_replacement=None, payment_attributes=None):
        """
        Uses the payment_id to find a specific payment item to update.
        If the update is via a PUT request, wherein the new object overwrites
        the old one completely, then new_payment should be supplied.
        Else, for updates via PATCH requests, the fields found in payment_attributes
        will be used to overwrite the ones currently associated with the payment.

        :param payment_id: <int> the unique identifier of a payment to be updated
        :param payment_replacement: <dict> a complete payload that describes a new payload which replaces the old one
        :param payment_attributes: <dict> a collection of new payment attribute values that will overwrite old ones
        """
        if not payment_replacement and not payment_attributes:
            raise DataValidationError('Invalid payment: body of request contained bad or no data')
        payment = self.db.session.query(Payment).get(payment_id)
        if payment == None or payment.is_removed == True :
            raise PaymentNotFoundError('Invalid payment: Payment ID not found')
        if payment_replacement:
            # TODO 	: test cases for validity in next sprint
            if not self.is_valid_put(payment.user_id,payment_replacement):
                raise DataValidationError('Invalid payment: body of request contained bad or no data')
            payment.deserialize_put(payment_replacement)
        elif payment_attributes: #patch
            existing_payment = payment.serialize()
            for key in payment_attributes:
                if key in self.UPDATABLE_PAYMENT_FIELDS:
                    existing_payment[key] = payment_attributes[key]
                else:
                    raise DataValidationError('Invalid payment: body of request contains invalid/un-updatable fields')
            payment.deserialize_put(existing_payment)
        self.db.session.commit()
        return_object = payment.serialize()
        return return_object

    def get_payments(self, payment_ids=None, payment_attributes=None):
        """
        Retrieves one or more payment items depending on the parameters
        passed in:
            - payment_ids, if present, will mean that the system should return
              all payment items that correspond to those ids.  Note that a list witj
              a single element is acceptable here.
            - payment_attributes, if present, will mean to query the database
              for all payment items that match the attributes.

        If neither parameter is supplied, then all payment items are returned.

        :param payment_ids: <list[int]> a list of one or more payments to be retrieved
        :param payment_attributes: <dict> a collection of payment attributes to be used in
                                   filtering for specific payments
        """
        if payment_ids != None:
            payments = self.db.session.query(Payment).filter(Payment.id.in_(payment_ids)).all()
            """
            #### will come back to this new implementation ###
            try:
                id_dict = [{'payment_id': id} for id in payment_ids]
                payments = [self._query_payments(payment_attributes=val)[0] for key, val in id_dict.iteritems()]
            except PaymentServiceQueryError as e:
                raise DataValidationError(e.message)
            """
        elif payment_attributes != None:
            try:
                payments = self._query_payments(payment_attributes)
            except PaymentServiceQueryError as e:
                raise DataValidationError(e.message)

        else:
            payments = self.db.session.query(Payment).all()

        payments = self._remove_soft_deletes(payments)

        return [payment.serialize() for payment in payments]

    def _query_payments(self, payment_attributes):
        """
        Returns all payment items that fulfill the attributes used to
        filter from all payment items.


        Note: this method assumes that the attributes are safe and have been validated.
        Also, the attributes passed in *must* be part of the Payment schema, since the
        query below is for the Payment model.  Later on we should have a parameter that
        indicates which model to use.

        :param parameter_attributes: <dict> a collection of Payment attributes to filter by
        :return: <list[Payment]> a list of the Payment items returned by the query
        """
        try:

            payment_query = self.db.session.query(Payment).filter_by(**payment_attributes)
            payments = payment_query.all()
            payments = self._remove_soft_deletes(payments)
            return payments

        except exc.SQLAlchemyError:
            raise PaymentServiceQueryError('Could not retrieve payment items due to query error with given attributes')

# UTILITY FUNCTIONS
    def is_valid_put(self,existing_user_id,data):
        valid = False
        valid_detail = False
        try:
            for key in self.NONUPDATABLE_PAYMENT_RREQUEST_FIELDS :
                if key in data:
                   raise DataValidationError('Invalid payment: body of request contained bad or no data')
            if existing_user_id != data['user_id']:
                raise DataValidationError('Invalid payment: Changes to user_id field not allowed')
            type = data['payment_type']
            detail = data['details']
            if bool(re.search(r'\d', detail['user_name'])) == False:
                valid = True
            if type == 'credit' or type == 'debit':
                card_number = detail['card_number']
                expires_date = detail['expires']
                if bool(re.match('^[0-9]+$', card_number)) and (len(card_number) == 16):
                    datetime.strptime(expires_date, '%m/%Y')
                    valid_detail = True
            elif data['is_linked'] != None and type == 'paypal':
                valid_detail = True
        except KeyError as e:
            raise DataValidationError('Invalid payment: missing ' + e.args[0])
        except TypeError as e:
            raise DataValidationError('Invalid payment: body of request contained bad or no data')
        return valid & valid_detail

    def _remove_soft_deletes(self, payments):
        """
        Takes a list of payments and removes those payments that have been 'soft deleted,'
        meaning the 'is_removed' field has been set to True

        Maybe there's a probably a better way to do this by including requirement in db query,
        but this will do for now
        """
        return [payment for payment in payments if not payment.is_removed]

    def perform_payment_action(self, user_id, payment_attributes=None):
        """
        Accepts a payment with user_id and performs an action on it

        :param user_id: <int> the unique identifier of a user_id whose payment/s is/are to be actioned upon
        :param payment_attributes: <dict> a collection of new payment attribute values that will update old ones

        if payment_attributes has payment_id, then it is "set-default" action.
        This also sets any other default payment of the same user to False

        if payment_attributes has amount, then it is performing "charge" action.
        This would update the charge history
        """
        try:
            payments = self._query_payments(payment_attributes={"user_id":user_id})
            if 'payment_id' in payment_attributes: #for set-default action
                payment_id_to_be_updated = payment_attributes['payment_id']
                payment_to_be_updated = None
                for payment in payments:
                    if payment.id == payment_id_to_be_updated: #no need to check if is_removed = False because the query filters it
                        payment_to_be_updated = payment
                if payment_to_be_updated != None:
                    payment_to_be_updated.is_default = True
                    #making sure other payments have default as false
                    other_payments = [payment for payment in payments if payment != payment_to_be_updated]
                    for other_payment in other_payments:
                        other_payment.is_default = False
                    #Committing all changes
                    self.db.session.commit()
                    return True
                else:
                    return False
            elif 'amount' in payment_attributes: #for charge action
                default_payment = None
                for payment in payments:
                    if payment.is_default == True:
                        default_payment = payment
                if default_payment != None:
                    update_payment_flag = True

                    if default_payment.payment_type == 'paypal' and not default_payment.details.is_linked:
                        error_msg = 'Invalid request: Default Payment for this user_id: '+ str(user_id)+' (Paypal) is not linked.'
                        raise DataValidationError(error_msg)
                    elif default_payment.payment_type != 'paypal' and self.is_expired(default_payment.details.expires):
                        error_msg = 'Invalid request: Default Payment for this user_id: '+ str(user_id)+' ('+default_payment.payment_type+') is expired'
                        raise DataValidationError(error_msg)

                    default_payment.charge_history = default_payment.charge_history + payment_attributes['amount']
                    self.db.session.commit()
                    return True
                else:
                    error_msg = 'Invalid request: Default Payment for this user_id: '+ str(user_id)+' not found. Please update the default_payment first.'
                    raise DataValidationError(error_msg) #PaymentNotFoundError
            else:
                raise DataValidationError('Invalid request: The request body contains bad or missing data.')
        except PaymentServiceQueryError as e:
            error_msg = 'Payments not found for the user_id: '+ str(user_id)
            raise DataValidationError(error_msg) #PaymentNotFoundError

    def is_expired(self, exp_date):
        month = int(exp_date[:2]) + 1
        exp_date = '%s%s' % (month, exp_date[2:])
        exp_date = datetime.strptime(exp_date, '%m/%Y')
        exp_date = exp_date - timedelta(1)
        exp_date = datetime.date(exp_date)

        now = datetime.now()
        now = datetime.date(now)

        if(now > exp_date):
            return True
        else:
            return False

    def load_sample(self, public, private):
        p = Payment()
        p.deserialize(public)
        p.is_default = private['is_default']
        p.is_removed = private['is_removed']
        p.charge_history = private['charge_history'] 
        app_db.session.add(p)
        app_db.session.commit()


class PaymentNotFoundError(Exception):
    """ Exception when payment is not found """

class PaymentServiceException(Exception):
    """ Generic exception class for PaymentService. """

class PaymentServiceQueryError(Exception):
    """ Raised when an internal query fails. """

