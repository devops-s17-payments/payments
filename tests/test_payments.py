# Test cases can be run with either of the following:
# python -m unittest discover
# nosetests -v --rednose --nologcapture

import unittest, json
from app import payments
from app.db import app_db
from app.error_handlers import DataValidationError
from app.db.interface import PaymentService
from app.db.models import Payment, Detail
from flask_api import status    # HTTP Status Codes

CREDIT = {'nickname' : 'my credit', 'user_id' : 1, 'payment_type' : 'credit', 
          'details' : {'user_name' : 'Jimmy Jones', 'card_number' : '1111222233334444',
          'expires' : '01/2019', 'card_type' : 'Mastercard'}}

#note 'nickname' is spelled wrong
BAD_DATA = {'nicknam3' : 'my paypal', 'user_id' : 2, 'payment_type' : 'paypal', 
            'details' : {'user_name' : 'John Jameson', 'user_email' : 'jj@aol.com'}}

PAYPAL = {'nickname' : 'my paypal', 'user_id' : 2, 'payment_type' : 'paypal', 
          'details' : {'user_name' : 'John Jameson', 'user_email' : 'jj@aol.com'}}

class TestModels(unittest.TestCase):

    def setUp(self):
        payments.app.debug = True
        payments.app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://payments:payments@localhost:5432/test'
        app_db.drop_all()    # clean up the last tests
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

    def test_db_has_one_item(self):
        p1 = app_db.session.query(Payment).get(1)
        self.assertNotEqual(p1, None)
        p2 = app_db.session.query(Payment).get(2)
        self.assertEqual(p2, None)

    def test_credit_has_no_paypal_fields(self):
        payment = app_db.session.query(Payment).get(1)
        self.assertEqual(payment.nickname, 'my credit')
        detail = payment.details
        self.assertEqual(detail.is_linked, None)
        self.assertEqual(detail.user_email, None)

