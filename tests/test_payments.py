# Test cases can be run with either of the following:
# python -m unittest discover
# nosetests -v --rednose --nologcapture

import unittest
from mock import patch
import json

from app import payments
from app.db import app_db
from app.db import models
from app.db.interface import PaymentService

SAMPLE_PAYMENT = {'nickname' : 'my credit', 'user_id' : 1, 'payment_type' : 'credit',
        'details' : {'user_name' : 'Jimmy Jones', 'card_number' : '1111222233334444',
        'expires' : '01/2019', 'card_type' : 'Mastercard'}}


class TestPaymentsCRUD(unittest.TestCase):
    """
    Test cases for CRUD methods contained in payments.py.
    """
    def setUp(self):
        # Important!  Need to use the test_client method in order to test the flask-made routes
        self.app = payments.app.test_client()

    def test_get_payments_ok(self):
        # return 200 OK and a simple payload for a successful request
        id = 0
        with patch.object(PaymentService, 'get_payments', return_value=SAMPLE_PAYMENT) as mocked_service:
            response = self.app.get('/payments/{}'.format(id))

            self.assertEqual(response.status_code, payments.HTTP_200_OK)
            self.assertEqual(json.loads(response.data), SAMPLE_PAYMENT)

    def test_get_payments_not_found(self):
        # something goes wrong with the GET request and the resource cannot be found
        id = 0
        with patch.object(PaymentService, 'get_payments', side_effect=Exception) as mocked_service:
            error_response = payments.NOT_FOUND_ERROR_BODY
            error_response['error'].format(id)
            response = self.app.get('/payments/{}'.format(id))

            self.assertEqual(response.status_code, payments.HTTP_404_NOT_FOUND)
            self.assertEqual(json.loads(response.data), error_response)
