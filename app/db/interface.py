# -*- coding:utf-8 -*-

from sqlalchemy import exc

from app.db.models import Payment, Detail
from app.error_handlers import DataValidationError
from app.db import app_db
from app.db.models import Payment

class PaymentService(object):
    """
    Serves as an interface which takes requests from the front-end
    and runs the corresponding actions in the database.
    """

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
        p.deserialize(payment_data)
        self.db.session.add(p)
        self.db.session.commit()
        result = p.serialize()
        return result

    def remove_payment(self, payment_id=None, payment_attributes=None):
        """
        Accepts an id or a variable number of keyword arguments (in payment_attributes)
        that could be used to identify a payment if the id is
        not known.

        :param payment_id: <int> the unique identifier of a payment to be removed
        :param payment_attributes: <dict> a collection of new payment attribute values that will overwrite old ones
        """

        raise NotImplementedError()

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
        payment = Payment.query.get_or_404(payment_id)
        if payment_replacement:
            #need to handle is valid and throw 400 bad request for payment_replacement
            payment.deserialize(payment_replacement)
            self.db.session.commit()
            return_object = payment.serialize()
            return return_object
        elif payment_attributes: #patch
            # implement isvalid on payment_attributes and throw 400 bad request otherwise
            existing_payment = payment.serialize()
            payload_nickname = existing_payment['nickname'] if 'nickname' not in payment_attributes else payment_attributes['nickname']
            payload_type = existing_payment['type'] if 'type' not in payment_attributes else payment_attributes['type']
            payload_detail = existing_payment['detail'] if 'detail' not in payment_attributes else payment_attributes['detail']
            payload_default = existing_payment['default'] if 'default' not in payment_attributes else payment_attributes['default'] # set only one default
            payload_charge = existing_payment['charge-history'] if 'charge-history' not in payment_attributes else payment_attributes['charge-history']
            target_payment = {'id' : payment_id, 'nickname' : payload_nickname, 'default' : payload_default,
                'charge-history' :  payload_charge, 'type' : payload_type, 'detail' : payload_detail}
            payment.deserialize(target_payment)
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

        raise NotImplementedError()

    def _query_payments(self, payment_attributes):
        """
        Returns all payment items that fulfill the attributes used to
        filter from all payment items.

        Note: this method assumes that the attributes are safe and have been validated.

        :param parameter_attributes: <dict> a collection of Payment attributes to filter by
        :return: <list[Payment]> a list of the Payment items returned by the query
        """
        try:
            payments = self.db.session.query(Payment).filter_by(**payment_attributes)
            return payments

        except exc.SQLAlchemyError:
            raise PaymentServiceQueryError('Could not retrieve payment items due to query error with given attributes')


class PaymentServiceException(Exception):
    """ Generic exception class for PaymentService. """

class PaymentServiceQueryError(Exception):
    """ Raised when an internal query fails. """
