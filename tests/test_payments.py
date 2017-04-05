# Test cases can be run with either of the following:
# python -m unittest discover
# nosetests -v --rednose --nologcapture

import unittest, json, mock
from app import payments
from app.db import app_db
from app.db.models import Payment, Detail
from app.db.interface import PaymentService
from flask_api import status   # HTTP Status Codes
from flask import make_response,jsonify
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

# for put updates
PUT_CREDIT = {'nickname' : 'favcredit', 'user_id' : 1, 'payment_type' : 'credit',
    'details' : CC_DETAIL}
PUT_CREDIT_RETURN = {'nickname' : 'favcredit', 'user_id' : 1, 'payment_type' : 'credit',
    'details' : CC_DETAIL, 'is_default' : False, 'charge_history' : 0.0, 'payment_id' : 1}
# for patch updates
PATCH_CREDIT = { 'nickname' : 'boringcredit'}
PATCH_RETURN = {'nickname' : 'boringcredit', 'user_id' : 1, 'payment_type' : 'credit',
    'details' : CC_DETAIL, 'is_default' : False, 'charge_history' : 0.0, 'payment_id' : 1}
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

#test cases for update payments - put and patch
# passing correct data to put
    @mock.patch.object(PaymentService, 'update_payment', return_value=PUT_CREDIT_RETURN, autospec=True)
    def test_crud_update_put(self,mock_ps_update):
        data = json.dumps(PUT_CREDIT_RETURN)
        resp = self.app.put('/payments/1', data=data, content_type='application/json')
        mock_ps_update.assert_called_with(mock.ANY,1,payment_replacement=PUT_CREDIT_RETURN)
        self.assertEqual( resp.status_code, status.HTTP_200_OK )
        new_json = json.loads(resp.data)
        self.assertEqual (new_json['nickname'], 'favcredit')

# passing correct data to patch
    @mock.patch.object(PaymentService, 'update_payment', return_value=PATCH_RETURN, autospec=True)
    def test_crud_update_patch(self,mock_ps_update):
        print 'here'
        data = json.dumps(PATCH_CREDIT)
        resp = self.app.patch('/payments/1', data=data, content_type='application/json')
        mock_ps_update.assert_called_with(mock.ANY,1,payment_attributes=PATCH_CREDIT)
        self.assertEqual( resp.status_code, status.HTTP_200_OK )
        new_json = json.loads(resp.data)
        self.assertEqual (new_json['nickname'], 'boringcredit')

# passing text data to put
    def test_crud_update_put_with_text_data(self):
        resp = self.app.put('/payments/1', data="hello", content_type='text/plain')
        self.assertEqual( resp.status_code, status.HTTP_400_BAD_REQUEST )
        self.assertTrue('bad or no data' in resp.data)

# passing text data to patch
    def test_crud_update_patch_with_text_data(self):
        resp = self.app.patch('/payments/1', data="hello", content_type='text/plain')
        self.assertEqual( resp.status_code, status.HTTP_400_BAD_REQUEST )
        self.assertTrue('bad or no data' in resp.data)

# passing no data to put
    def test_crud_update_put_with_no_data(self):
        resp = self.app.put('/payments/1', data=None, content_type='application/json')
        self.assertEqual( resp.status_code, status.HTTP_400_BAD_REQUEST )
        self.assertTrue('no data' in resp.data)

# passing no data to patch
    def test_crud_update_patch_with_no_data(self):
        resp = self.app.patch('/payments/1', data=None, content_type='application/json')
        self.assertEqual( resp.status_code, status.HTTP_400_BAD_REQUEST )
        self.assertTrue('no data' in resp.data)

# passing garbage data to put
    @mock.patch.object(PaymentService, 'update_payment', side_effect=DataValidationError, autospec=True)
    def test_crud_update_put_garbage(self, mock_ps_update):
        garbage = 'a@$*&@#sdassdc3r 3284723X43&^@!#@*#'
        data = json.dumps(garbage)
        try:
            resp = self.app.put('/payments/1', data=data, content_type='application/json')
        except DataValidationError as e:
            self.assertTrue('bad or no data' in e.message)
            mock_ps_update.assert_called_with(mock.ANY, payment_replacement=None)
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

# passing garbage data to put
    @mock.patch.object(PaymentService, 'update_payment', side_effect=DataValidationError, autospec=True)
    def test_crud_update_patch_garbage(self, mock_ps_update):
        garbage = 'a@$*&@#sdassdc3r 3284723X43&^@!#@*#'
        data = json.dumps(garbage)
        try:
            resp = self.app.patch('/payments/1', data=data, content_type='application/json')
        except DataValidationError as e:
            self.assertTrue('bad or no data' in e.message)
            mock_ps_update.assert_called_with(mock.ANY, payment_attributes=None)
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
'''
# passing wrong payment id to put
    @mock.patch.object(PaymentService, 'update_payment', return_value = err_response, autospec=True)
    def test_crud_update_put_wrong_id(self,mock_ps_update):
        data = json.dumps(PUT_CREDIT_RETURN)
        print 'hwofhldfh;osfho;ehf'
        resp = self.app.put('/payments/1111', data=data, content_type='application/json')
        mock_ps_update.assert_called_with(mock.ANY,1111,payment_replacement=PUT_CREDIT_RETURN)
        print resp
        self.assertEqual( resp.status_code, status.HTTP_404_NOT_FOUND )
        self.assertTrue('Not Found' in resp.error)
# passing wrong payment id to
'''
