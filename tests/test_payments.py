# Test cases can be run with either of the following:
# python -m unittest discover
# nosetests -v --rednose --nologcapture

import unittest, json, mock
from app import payments
from app.db import app_db
from app.db.models import Payment, Detail
from app.db.interface import PaymentService
from flask_api import status    # HTTP Status Codes
from app.error_handlers import DataValidationError

CC_DETAIL = {'user_name' : 'Jimmy Jones', 'card_number' : '1111222233334444',
             'expires' : '01/2019', 'card_type' : 'Mastercard'}

DC_DETAIL = {'user_name' : 'John Jameson', 'card_number' : '4444333322221111',
             'expires' : '02/2020', 'card_type' : 'Visa'}

PP_DETAIL = {'user_name' : 'John Jameson', 'user_email' : 'jj@aol.com'}

CREDIT = {'nickname' : 'my credit', 'user_id' : 1, 'payment_type' : 'credit', 
          'details' : CC_DETAIL}

DEBIT = {'nickname' : 'my debit', 'user_id' : 2, 'payment_type' : 'debit', 
         'details' : DC_DETAIL}

PAYPAL = {'nickname' : 'my paypal', 'user_id' : 2, 'payment_type' : 'paypal', 
          'details' : PP_DETAIL}

#note 'nickname' is spelled wrong
BAD_DATA = {'nicknam3' : 'my paypal', 'user_id' : 2, 'payment_type' : 'paypal', 
            'details' : PP_DETAIL}

PP_RETURN = dict(PAYPAL)
PP_RETURN ['is_default'] = False
PP_RETURN ['charge_history'] = 0.0
PP_RETURN ['payment_id'] = 1
PP_RETURN ['details']['is_linked'] = True

CC_RETURN = dict(CREDIT)
CC_RETURN['is_default'] = False
CC_RETURN['charge_history'] = 0.0
CC_RETURN['payment_id'] = 1

#this should always be added second
DC_RETURN = dict(DEBIT)
DC_RETURN['is_default'] = False
DC_RETURN['charge_history'] = 0.0
DC_RETURN['payment_id'] = 2

class TestPaymentsCRUD(unittest.TestCase):
    """
    Test cases for CRUD methods contained in payments.py.
    """

    def setUp(self):
        self.app = payments.app.test_client()

    @mock.patch.object(PaymentService, 'add_payment', return_value=CC_RETURN, autospec=True)
    def test_crud_create_card(self, mock_ps_add):
        data = json.dumps(CREDIT)
        resp = self.app.post('/payments', data=data, content_type='application/json')
        mock_ps_add.assert_called_with(mock.ANY, CREDIT)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json.loads(resp.data), {'created' : CC_RETURN})

    @mock.patch.object(PaymentService, 'add_payment', return_value=PP_RETURN, autospec=True)
    def test_crud_create_paypal(self, mock_ps_add):
        data = json.dumps(PAYPAL)
        resp = self.app.post('/payments', data=data, content_type='application/json')
        mock_ps_add.assert_called_with(mock.ANY, PAYPAL)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json.loads(resp.data), {'created' : PP_RETURN})

    @mock.patch.object(PaymentService, 'add_payment', autospec=True)
    def test_crud_create_two_cards(self, mock_ps_add):
        data = json.dumps(CREDIT)
        mock_ps_add.return_value = CC_RETURN
        resp = self.app.post('/payments', data=data, content_type='application/json')
        mock_ps_add.assert_called_with(mock.ANY, CREDIT)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json.loads(resp.data), {'created' : CC_RETURN})
        
        data = json.dumps(DEBIT)
        mock_ps_add.return_value = DC_RETURN
        resp = self.app.post('/payments', data=data, content_type='application/json')
        mock_ps_add.assert_called_with(mock.ANY, DEBIT)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json.loads(resp.data), {'created' : DC_RETURN})

    @mock.patch.object(PaymentService, 'add_payment', side_effect=DataValidationError, autospec=True)
    def test_crud_create_bad_data(self, mock_ps_add):
        data = json.dumps(BAD_DATA)
        try:
            resp = self.app.post('/payments', data=data, content_type='application/json')
        except DataValidationError as e:
            self.assertTrue('missing nickname' in e.message)
            mock_ps_add.assert_called_with(mock.ANY, BAD_DATA)
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertTrue('missing nickname' in json.loads(resp.data))

    @mock.patch.object(PaymentService, 'add_payment', side_effect=DataValidationError, autospec=True)
    def test_crud_create_garbage(self, mock_ps_add):
        garbage = 'a@$*&@#sdassdc3r 3284723X43&^@!#@*#'
        data = json.dumps(garbage)
        try:
            resp = self.app.post('/payments', data=data, content_type='application/json')
        except DataValidationError as e:
            self.assertTrue('bad or no data' in e.message)
            mock_ps_add.assert_called_with(mock.ANY, None)
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
