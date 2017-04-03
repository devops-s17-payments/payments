# Test cases can be run with either of the following:
# python -m unittest discover
# nosetests -v --rednose --nologcapture

import unittest

from app import payments
from app.db import app_db
from app.db.models import Payment, Detail
from app.db.interface import PaymentService
from app.error_handlers import DataValidationError

CREDIT = {'nickname' : 'my credit', 'user_id' : 1, 'payment_type' : 'credit', 
             'details' : {'user_name' : 'Jimmy Jones', 'card_number' : '1111222233334444',
             'expires' : '01/2019', 'card_type' : 'Mastercard'}}

DEBIT = {'nickname' : 'my debit', 'user_id' : 2, 'payment_type' : 'debit', 
         'details' : {'user_name' : 'John Jameson', 'card_number' : '4444333322221111',
         'expires' : '02/2020', 'card_type' : 'Visa'}}

PAYPAL = {'nickname' : 'my paypal', 'user_id' : 2, 'payment_type' : 'paypal', 
          'details' : {'user_name' : 'John Jameson', 'user_email' : 'jj@aol.com'}}

#note 'nickname' is spelled wrong
BAD_DATA = {'nicknam3' : 'my paypal', 'user_id' : 2, 'payment_type' : 'paypal', 
            'details' : {'user_name' : 'John Jameson', 'user_email' : 'jj@aol.com'}}

ps = PaymentService()

class TestInterface(unittest.TestCase):

    def setUp(self):
        payments.app.debug = True
        payments.app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://payments:payments@localhost:5432/test'
        app_db.create_all()  # make our sqlalchemy tables
        
        data = CREDIT

        payment = Payment()
        payment.deserialize(data)
        app_db.session.add(payment)
        app_db.session.commit()
        self.app = payments.app.test_client()

    def tearDown(self):
        app_db.session.remove()
        app_db.drop_all()

    def test_interface_add_card(self):
        data = DEBIT
        p2 = app_db.session.query(Payment).get(2)
        self.assertEqual(p2, None)
        ps.add_payment(data)
        p2 = app_db.session.query(Payment).get(2)
        d2 = p2.details
        self.assertNotEqual(p2, None)
        self.assertEqual(p2.nickname, 'my debit')
        self.assertEqual(d2.user_name, 'John Jameson')

    def test_interface_add_paypal(self):
        data = PAYPAL
        p2 = app_db.session.query(Payment).get(2)
        self.assertEqual(p2, None)
        ps.add_payment(data)
        p2 = app_db.session.query(Payment).get(2)
        d2 = p2.details
        self.assertNotEqual(p2, None)
        self.assertEqual(p2.nickname, 'my paypal')
        self.assertEqual(d2.user_name, 'John Jameson')
        self.assertEqual(d2.is_linked, True)

    def test_interface_add_missing_details(self):
        data = {'nickname' : 'my debit', 'user_id' : 2, 'payment_type' : 'debit'}
        self.assertRaises(DataValidationError, ps.add_payment, data)

    def test_interface_add_bad_data(self):
        data = BAD_DATA
        self.assertRaises(DataValidationError, ps.add_payment, data)

    def test_interface_add_garbage(self):
        garbage = 'afv@#(&@(#Z@#>X@C8rq rq34tr0q934r 9qr@(#*(@!$))'
        self.assertRaises(DataValidationError, ps.add_payment, garbage)