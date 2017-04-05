# -*- coding:utf-8 -*-
from app.db.models import Payment, Detail
from app.error_handlers import DataValidationError
from app.db import app_db
from sqlalchemy import exc

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

        raise NotImplementedError()

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

    def _remove_soft_deletes(self, payments):
        """
        Takes a list of payments and removes those payments that have been 'soft deleted,'
        meaning the 'is_removed' field has been set to True
        
        Maybe there's a probably a better way to do this by including requirement in db query,
        but this will do for now 
        """
        return [payment for payment in payments if not payment.is_removed]
        

class PaymentServiceException(Exception):
    """ Generic exception class for PaymentService. """

class PaymentServiceQueryError(Exception):
    """ Raised when an internal query fails. """
