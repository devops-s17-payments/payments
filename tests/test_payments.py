# Test cases can be run with either of the following:
# python -m unittest discover
# nosetests -v --rednose --nologcapture

import unittest

from app import payments
from app.db import app_db
from app.db import models
#from app.error_handlers import DataValidationError


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

class TestPaymentsCRUD(unittest.TestCase):
    """
    Test cases for CRUD methods contained in payments.py.
    """

    def setUp(self):
        self.app = payments.app.test_client()

    def test_crud_create_card(self):
        with patch.object(PaymentService, 'add_payment', return_value=CREDIT) as mocked_service:
            data = json.dumps(CREDIT)
            resp = self.app.post('/payments', data=data, content_type='application/json')
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
            self.assertEqual(json.loads(resp.data), {'created' : CREDIT})

    def test_crud_create_paypal(self):
        with patch.object(PaymentService, 'add_payment', return_value=DEBIT) as mocked_service:
            data = json.dumps(DEBIT)
            resp = self.app.post('/payments', data=data, content_type='application/json')
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
            self.assertEqual(json.loads(resp.data), {'created' : DEBIT})

