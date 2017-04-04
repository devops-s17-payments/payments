# Test cases can be run with either of the following:
# python -m unittest discover
# nosetests -v --rednose --nologcapture

import unittest, mock

from app import payments
from app.db import app_db
from app.db.models import Payment, Detail
from app.db.interface import PaymentService, PaymentServiceQueryError
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

ps = PaymentService()

QUERY_ATTRIBUTES = {
    'user_name': 'John Jameson',
    'card_type': 'Mastercard'
}

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
        self.ps = ps

    def tearDown(self):
        app_db.session.remove()
        app_db.drop_all()

    def test_interface_add_card_returns_json(self):
        data = DEBIT
        payment = ps.add_payment(data)
        self.assertTrue(type(payment), type({}))
        self.assertTrue(payment['nickname'] == 'my debit')
        self.assertTrue(payment['details']['user_name'] == 'John Jameson')

    def test_interface_add_card_to_db(self):
        data = DEBIT
        p2 = app_db.session.query(Payment).get(2)
        self.assertEqual(p2, None)
        ps.add_payment(data)
        p2 = app_db.session.query(Payment).get(2)
        d2 = p2.details
        self.assertNotEqual(p2, None)
        self.assertEqual(p2.nickname, 'my debit')
        self.assertEqual(d2.user_name, 'John Jameson')

    def test_interface_add_paypal_to_db(self):
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

    """ 
    adding some mock tests in addition to the above since add_payment
    relies on functions in Payment / Detail

    these also rely on Deserialize methods, but since those reuturn model objects,
    I'm not sure how to mock those quite yet... will revisit
    """
    @mock.patch.object(Detail, 'serialize', return_valie=CC_DETAIL, autospec=True)
    @mock.patch.object(Payment, 'serialize', return_value=CC_RETURN, autospec=True)
    def test_interface_add_card_mock(self, mock_serial, mock_det_serial):
        payment = ps.add_payment(CREDIT)
        self.assertTrue(type(payment), type({}))
        self.assertEqual(CC_RETURN, payment)
        self.assertEqual(CC_DETAIL, payment['details'])

    @mock.patch.object(Detail, 'serialize', autospec=True)
    @mock.patch.object(Payment, 'serialize', return_value=PP_RETURN, autospec=True)
    def test_interface_add_paypal_mock(self, mock_pay_serial, mock_det_serial):
        temp = dict(PP_DETAIL)
        temp['is_linked'] = True
        mock_det_serial.return_value = temp
        payment = ps.add_payment(PAYPAL)
        self.assertTrue(type(payment), type({}))
        self.assertEqual(PP_RETURN, payment)
        self.assertEqual(temp, payment['details'])

    @mock.patch.object(app_db, 'session')
    def test_interface_query_payments(self, mock_db):
        # this is a long mock - note that the method call chaining matches that of the method call
        # on self.db in _query_payments
        mock_db.query(Payment).filter_by.return_value = [DEBIT]
        result = self.ps._query_payments(QUERY_ATTRIBUTES)

        mock_db.query(Payment).filter_by.assert_called_once_with(**QUERY_ATTRIBUTES)
        self.assertEqual(result, [DEBIT])

    @mock.patch.object(app_db, 'session')
    def test_interface_query_payments_error(self, mock_db):
        mock_db.query(Payment).filter_by.side_effect = PaymentServiceQueryError

        with self.assertRaises(PaymentServiceQueryError):
            result = self.ps._query_payments(QUERY_ATTRIBUTES)
        # also check that the mocked app_db was called appropriately
        mock_db.query(Payment).filter_by.assert_called_once_with(**QUERY_ATTRIBUTES)
