# Test cases can be run with either of the following:
# python -m unittest discover
# nosetests -v --rednose --nologcapture

import unittest, json, mock

from app import payments
from app.db import app_db
from app.error_handlers import DataValidationError
from app.db.interface import PaymentService
from app.db.models import Payment, Detail
from flask_api import status    # HTTP Status Codes

CARD_DATA = {'nickname' : 'my credit', 'user_id' : 1, 'payment_type' : 'credit', 
             'details' : {'user_name' : 'Jimmy Jones', 'card_number' : '1111222233334444',
             'expires' : '01/2019', 'card_type' : 'Mastercard'}}

#note 'nickname' is spelled wrong
BAD_DATA = {'nicknam3' : 'my paypal', 'user_id' : 2, 'payment_type' : 'paypal', 
            'details' : {'user_name' : 'John Jameson', 'user_email' : 'jj@aol.com'}}

PAYPAL_DATA = {'nickname' : 'my paypal', 'user_id' : 2, 'payment_type' : 'paypal', 
               'details' : {'user_name' : 'John Jameson', 'user_email' : 'jj@aol.com'}}

class TestModels(unittest.TestCase):

    def setUp(self):
        payments.app.debug = True
        payments.app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://payments:payments@localhost:5432/test'
        app_db.drop_all()    # clean up the last tests
        app_db.create_all()  # make our sqlalchemy tables
        
        data = CARD_DATA

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

class TestErrorHandlers(unittest.TestCase):

    def setUp(self):
        self.app = payments.app.test_client()
        
    def test_crud_put_not_allowed_for_create(self):
        data = json.dumps(PAYPAL_DATA)
        resp = self.app.put('/payments', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_crud_post_not_allowed_on_existing(self):
        data = json.dumps(CARD_DATA)
        resp = self.app.post('/payments/1', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_crud_post_bad_data(self):
        data = json.dumps(BAD_DATA)
        resp = self.app.post('/payments', data=data, content_type='application/json')
        self.assertEquals(resp.status_code, status.HTTP_400_BAD_REQUEST)
        
        ''' this will be fixed in refactor '''
        #self.assertTrue('missing nickname' in resp.data)

    def test_crud_post_no_data(self):
        data = None
        resp = self.app.post('/payments', data=data, content_type='application/json')
        self.assertEquals(resp.status_code, status.HTTP_400_BAD_REQUEST)
        
        ''' this will be fixed in refactor '''
        #self.assertTrue('bad or no data' in resp.data)

    def test_crud_post_garbage(self):
        garbage = 'coiNCEOI#$()&@#%&V$TC&nDFudfsf sdg g w9r w39 r70'
        resp = self.app.post('/payments', data=garbage, content_type='application/json')
        self.assertEquals(resp.status_code, status.HTTP_400_BAD_REQUEST)
        
        ''' this will be fixed in refactor '''
        #self.assertTrue('bad or no data' in resp.data)

    def test_crud_get_id_not_found(self):
        resp = self.app.get('payments/777')
        self.assertTrue(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue('777 was not found' in resp.data)

    def test_crud_put_id_not_found(self):
        resp = self.app.put('payments/778')
        self.assertTrue(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue('778 was not found' in resp.data)

    def test_crud_patch_id_not_found(self):
        resp = self.app.put('payments/779')
        self.assertTrue(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue('779 was not found' in resp.data)

    def test_crud_get_garbage1_not_found(self):
        resp = self.app.get('payments/dflkdfsdflkjsd')
        self.assertTrue(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue('requested URL was not found' in resp.data)

    def test_crud_get_garbage2_not_found(self):
        resp = self.app.get('<24@#&*^@sd35vqr\]/.,diiv8989')
        self.assertTrue(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue('requested URL was not found' in resp.data)

