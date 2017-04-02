# -*- coding:utf-8 -*-

from db import app_db
from db.models import Payment, Detail


class PaymentService(object):
    """
    Serves as an interface which takes requests from the front-end
    and runs the corresponding actions in the database.
    """

    def __init__(self):
        """
        Initialize connection to database here.
        """

    def add_payment(self, payment_data):
        """
        Takes a dictionary of payment parameters and creates a new
        payment item in the database using those parameters' data.

        :param payment_data: <dict> a validated JSON payload that describes a new Payment object
        """

        raise NotImplementedError()

    def remove_payment(self, payment_id=None, payment_attributes=None):
        """
        Accepts an id or a variable number of keyword arguments
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
        Else, for updates via PATCH requests, the fields found in **kwargs
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

        raise NotImplementedError()
