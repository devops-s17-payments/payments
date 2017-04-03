# Test cases can be run with either of the following:
# python -m unittest discover
# nosetests -v --rednose --nologcapture

import unittest
#from mock import patch
from app import payments
from app.db import app_db
from app.db.models import Payment, Detail, DataValidationError #remove DVE before merging
#from app.error_handlers import DataValidationError

CREDIT_DETAIL = {'user_name' : 'John Jameson', 'card_number' : '4444333322221111',
                 'expires' : '02/2020', 'card_type' : 'Visa'}

PAYPAL_DETAIL = {'user_name' : 'John Jameson', 'user_email' : 'jj@aol.com'}

BAD_DETAIL = {'whatever' : 'John Jameson', 'card_number' : '4444333322221111',
              'expires' : '02/2020', 'card_type' : 'Visa'}

CREDIT = {'nickname' : 'my credit', 'user_id' : 1,
          'payment_type' : 'credit', 'details' : CREDIT_DETAIL}

PAYPAL = {'nickname' : 'my paypal', 'user_id' : 2,
          'payment_type' : 'paypal', 'details' : PAYPAL_DETAIL}

BAD_CARD = {'whatever' : 'bad', 'user_id' : 2,
            'payment_type' : 'debit', 'details' : BAD_DETAIL}

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
        self.assertEqual(type(p['details']), type({}))

        temp = CREDIT
        temp['is_default'] = False
        temp['charge_history'] = 0.0
        temp['payment_id'] = 1
        self.assertEqual(temp, payment.serialize())
    
    def test_detail_serialize_credit(self):
        detail = Detail.query.get(1)
        d = detail.serialize()
        self.assertEqual(type(d), type({}))
        self.assertEqual(CREDIT_DETAIL, detail.serialize())

    def test_detail_serialize_paypal(self):
        d = Detail()
        d.deserialize_paypal(PAYPAL_DETAIL)
        app_db.session.add(d)
        app_db.session.commit()
        detail = Detail.query.get(2)
        d = detail.serialize()
        self.assertEqual(type(d), type({}))

        temp = PAYPAL_DETAIL
        temp['is_linked'] = True
        self.assertEqual(temp, detail.serialize())
        
    def test_payment_deserialize(self):
        p = Payment()
        self.assertEqual(p.nickname, None)
        self.assertEqual(p.user_id, None)
        self.assertEqual(p.payment_type, None)
        self.assertEqual(p.details, None)
        self.assertEqual(p.is_default, None)
        self.assertEqual(p.is_removed, None)
        self.assertEqual(p.charge_history, None)
        p.deserialize(CREDIT)
        self.assertEqual(p.nickname, 'my credit')
        self.assertEqual(p.user_id, 1)
        self.assertEqual(p.payment_type, 'credit')
        self.assertNotEqual(p.details, None)
        self.assertEqual(p.is_default, False)
        self.assertEqual(p.is_removed, False)
        self.assertEqual(p.charge_history, 0.0)

    def test_detail_deserialize_credit(self):
        d = Detail()
        self.assertEqual(d.user_name, None)
        self.assertEqual(d.card_type, None)
        self.assertEqual(d.card_number, None)
        self.assertEqual(d.expires, None)
        self.assertEqual(d.is_linked, None)
        self.assertEqual(d.user_email, None)
        d.deserialize_card(CREDIT_DETAIL)
        self.assertEqual(d.user_name, 'John Jameson')
        self.assertEqual(d.card_type, 'Visa')
        self.assertEqual(d.card_number, '4444333322221111')
        self.assertEqual(d.expires, '02/2020')
        self.assertEqual(d.is_linked, None)
        self.assertEqual(d.user_email, None)

    def test_detail_deserialize_paypal(self):
        d = Detail()
        self.assertEqual(d.user_name, None)
        self.assertEqual(d.card_type, None)
        self.assertEqual(d.card_number, None)
        self.assertEqual(d.expires, None)
        self.assertEqual(d.is_linked, None)
        self.assertEqual(d.user_email, None)
        d.deserialize_paypal(PAYPAL_DETAIL)
        self.assertEqual(d.user_name, 'John Jameson')
        self.assertEqual(d.card_type, None)
        self.assertEqual(d.card_number, None)
        self.assertEqual(d.expires, None)
        self.assertEqual(d.is_linked, True)
        self.assertEqual(d.user_email, 'jj@aol.com')

    def test_payment_self_url(self):
        payment = Payment.query.get(1)
        with payments.app.test_request_context():
            addr = payment.self_url()
            self.assertTrue('/payments/1' in addr)

    def test_payment_deserialize_bad_data(self):
        p = Payment();
        self.assertRaises(DataValidationError, p.deserialize, BAD_CARD)
        self.assertRaises(DataValidationError, p.deserialize, 'as@Q#$*)&2r923rz3ru3892')

    def test_detail_deserialize_bad_card(self):
        d = Detail()
        self.assertRaises(DataValidationError, d.deserialize_card, BAD_DETAIL)
        self.assertRaises(DataValidationError, d.deserialize_card, 'dfkjh@#(*#@R(*HFG$E')

    def test_payment_deserialize_bad_paypal(self):
        d = Detail()
        self.assertRaises(DataValidationError, d.deserialize_paypal, BAD_DETAIL)
        self.assertRaises(DataValidationError, d.deserialize_paypal, 'dfkh(!*@$*f394f4')