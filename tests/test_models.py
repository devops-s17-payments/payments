# Test cases can be run with either of the following:
# python -m unittest discover
# nosetests -v --rednose --nologcapture

import unittest
#from mock import patch
from app import payments
from app.db import app_db
from app.db.models import Payment, Detail

CREDIT_DETAIL = {'user_name' : 'John Jameson', 'card_number' : '4444333322221111',
                 'expires' : '02/2020', 'card_type' : 'Visa'}

PAYPAL_DETAIL = {'user_name' : 'John Jameson', 'user_email' : 'jj@aol.com'}

CREDIT = {'nickname' : 'my credit', 'user_id' : 1,
          'payment_type' : 'credit', 'details' : CREDIT_DETAIL}

PAYPAL = {'nickname' : 'my paypal', 'user_id' : 2,
          'payment_type' : 'paypal', 'details' : PAYPAL_DETAIL}

#note 'nickname' is spelled wrong
BAD_DATA = {'nicknam3' : 'bad', 'user_id' : 2,
            'payment_type' : 'paypal', 'details' : PAYPAL_DETAIL}

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

    def test_payment_serialize_credit(self):
        payment = Payment.query.get(1)
        p = payment.serialize()
        self.assertEqual(type(p), type({}))
        self.assertEqual(p['nickname'], 'my credit')
        self.assertEqual(p['user_id'], 1)
        self.assertEqual(p['payment_type'], 'credit')
        self.assertEqual(type(p['details']), type({}))
    
    def test_detail_serialize_credit(self):
        detail = Detail.query.get(1)
        d = detail.serialize()
        self.assertEqual(d['user_name'], 'John Jameson')
        self.assertEqual(d['card_number'], '4444333322221111')
        self.assertEqual(d['card_type'], 'Visa')
        self.assertEqual(d['expires'], '02/2020')
        self.assertTrue('is_linked' not in d)
        self.assertTrue('user_email' not in d)

    def test_detail_serialize_paypal(self):
        d = Detail()
        d.deserialize_paypal(PAYPAL_DETAIL)
        app_db.session.add(d)
        app_db.session.commit()
        detail = Detail.query.get(2)
        d = detail.serialize()
        self.assertEqual(d['user_name'], 'John Jameson')
        self.assertEqual(d['user_email'], 'jj@aol.com')
        self.assertEqual(d['is_linked'], True)
        self.assertTrue('card_number' not in d)
        self.assertTrue('card_type' not in d)
        
    def test_payment_deserialize(self):
        pass

    def test_detail_deserialize_credit(self):
        pass

    def test_detail_deserialize_paypal(self):
        pass

    def test_payment_self_url(self):
        payment = Payment.query.get(1)
        with payments.app.test_request_context():
            addr = payment.self_url()
            self.assertTrue('/payments/1' in addr)
        