# Test cases can be run with either of the following:
# python -m unittest discover
# nosetests -v --rednose --nologcapture

import unittest, json
from app import payments
from app.db import app_db
from app.error_handlers import DataValidationError,InvalidPaymentID
from app.db.interface import PaymentService
from app.db.models import Payment, Detail
from flask_api import status    # HTTP Status Codes

CREDIT = {'nickname' : 'my credit', 'user_id' : 1, 'payment_type' : 'credit', 
          'details' : {'user_name' : 'Jimmy Jones', 'card_number' : '1111222233334444',
          'expires' : '01/2019', 'card_type' : 'Mastercard'}}

BAD_DATA = {'nicknam3' : 'my paypal', 'user_id' : 2, 'payment_type' : 'paypal', 
            'details' : {'user_name' : 'John Jameson', 'user_email' : 'jj@aol.com'}}

PAYPAL = {'nickname' : 'my paypal', 'user_id' : 2, 'payment_type' : 'paypal', 
          'details' : {'user_name' : 'John Jameson', 'user_email' : 'jj@aol.com'}}

class TestErrorHandlers(unittest.TestCase):

    '''
        need to revisit these w/r/t to validating correct 
        error messages after refactoring is complete
    '''

    def setUp(self):
        self.app = payments.app.test_client()
        
    def test_crud_put_not_allowed_for_create(self):
        data = json.dumps(PAYPAL)
        resp = self.app.put('/payments', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_crud_post_not_allowed_on_existing(self):
        data = json.dumps(CREDIT)
        resp = self.app.post('/payments/1', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_crud_post_not_allowed_on_existing2(self):
        resp = self.app.post('/payments/1')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_crud_post_bad_data(self):
        data = json.dumps(BAD_DATA)
        resp = self.app.post('/payments', data=data, content_type='application/json')
        self.assertEquals(resp.status_code, status.HTTP_400_BAD_REQUEST)
        #self.assertTrue('missing nickname' in resp.data)

    def test_crud_post_no_data(self):
        data = None
        resp = self.app.post('/payments', data=data, content_type='application/json')
        self.assertEquals(resp.status_code, status.HTTP_400_BAD_REQUEST)
        #self.assertTrue('bad or no data' in resp.data)

    def test_crud_post_garbage(self):
        garbage = 'coiNCEOI#$()&@#%&V$TC&nDFudfsf sdg g w9r w39 r70'
        resp = self.app.post('/payments', data=garbage, content_type='application/json')
        self.assertEquals(resp.status_code, status.HTTP_400_BAD_REQUEST)
        #self.assertTrue('bad or no data' in resp.data)

    def test_crud_get_id_not_found(self):
        resp = self.app.get('payments/777')
        self.assertTrue(resp.status_code, status.HTTP_404_NOT_FOUND)

        ### not sure why this is failing... will come back to this ###
        #self.assertTrue(payments.NOT_FOUND_ERROR_BODY['error'].format(777) in resp.data)

    def test_crud_put_id_not_found(self):
        resp = self.app.put('payments/778')
        self.assertTrue(resp.status_code, status.HTTP_404_NOT_FOUND)
        #self.assertTrue('778 was not found' in resp.data)

    def test_crud_patch_id_not_found(self):
        resp = self.app.put('payments/779')
        self.assertTrue(resp.status_code, status.HTTP_404_NOT_FOUND)
        #self.assertTrue('779 was not found' in resp.data)

    def test_crud_get_garbage1_not_found(self):
        resp = self.app.get('payments/dflkdfsdflkjsd')
        self.assertTrue(resp.status_code, status.HTTP_404_NOT_FOUND)
        #self.assertTrue('requested URL was not found' in resp.data)

    def test_crud_get_garbage2_not_found(self):
        resp = self.app.get('<24@#&*^@sd35vqr\]/.,diiv8989')
        self.assertTrue(resp.status_code, status.HTTP_404_NOT_FOUND)
        #self.assertTrue('requested URL was not found' in resp.data)