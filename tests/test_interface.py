# Test cases can be run with either of the following:
# python -m unittest discover
# nosetests -v --rednose --nologcapture


import unittest
import mock

from app import payments
from app.db import app_db
from app.db.models import Payment, Detail
from app.db.interface import PaymentService, PaymentServiceQueryError

from app.error_handlers import DataValidationError


CC_DETAIL = {'user_name' : 'Jimmy Jones', 'card_number' : '1111222233334444',
             'expires' : '01/2019', 'card_type' : 'Mastercard'}

DC_DETAIL = {'user_name' : 'Jeremy Jenkins', 'card_number' : '4444333322221111',
             'expires' : '02/2020', 'card_type' : 'Visa'}

PP_DETAIL = {'user_name' : 'John Jameson', 'user_email' : 'jj@aol.com'}

CREDIT = {'nickname' : 'my credit', 'user_id' : 1, 'payment_type' : 'credit', 
          'details' : CC_DETAIL}

DEBIT = {'nickname' : 'my debit', 'user_id' : 2, 'payment_type' : 'debit', 
         'details' : DC_DETAIL}

PAYPAL = {'nickname' : 'my paypal', 'user_id' : 1, 'payment_type' : 'paypal', 
          'details' : PP_DETAIL}

BAD_DATA = {'bad key' : 'my paypal', 'user_id' : 2, 'payment_type' : 'paypal', 
            'details' : PP_DETAIL}

BAD_DATA2 = {"nicknam3" : "my paypal", "user_id" : 1, "payment_type" : "paypal",
             "details" : {"user_name" : "John Jameson", "user_email" : "jj@aol.com"}}

PP_RETURN = dict(PAYPAL, is_default=False, charge_history=0.0, payment_id=3)
PP_RETURN['details']['is_linked'] = True

CC_RETURN = dict(CREDIT, is_default=False, charge_history=0.0, payment_id=1)

DC_RETURN = dict(DEBIT, is_default=False, charge_history=0.0, payment_id=2)

QUERY_ATTRIBUTES = {
    'user_id': 1,
    'nickname': 'my paypal'
}

BAD_QUERY_ATTRIBUTES = {
    'payment_type': 'Amateurcard'
}

class TestInterface(unittest.TestCase):

    def setUp(self):
        payments.app.debug = True
        payments.app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://payments:payments@localhost:5432/test'
        app_db.create_all()  # make our sqlalchemy tables
        self.ps = PaymentService()
        self.app = payments.app.test_client()

    def tearDown(self):
        app_db.session.remove()
        app_db.drop_all()

    def test_interface_add_card_returns_json(self):
        data = CREDIT
        payment = self.ps.add_payment(data)
        self.assertTrue(type(payment), type({}))
        self.assertTrue(payment['nickname'] == 'my credit')
        self.assertTrue(payment['details']['user_name'] == 'Jimmy Jones')

    def test_interface_add_card_to_db(self):
        data = CREDIT
        p1 = app_db.session.query(Payment).get(1)
        self.assertEqual(p1, None)
        self.ps.add_payment(data)
        p1 = app_db.session.query(Payment).get(1)
        d1 = p1.details
        self.assertEqual(p1.nickname, 'my credit')
        self.assertEqual(d1.user_name, 'Jimmy Jones')
        p2 = app_db.session.query(Payment).get(2)
        self.assertEqual(p2, None)

    def test_interface_add_paypal_to_db(self):
        data = PAYPAL
        p1 = app_db.session.query(Payment).get(1)
        self.assertEqual(p1, None)
        self.ps.add_payment(data)
        p1 = app_db.session.query(Payment).get(1)
        d1 = p1.details
        self.assertEqual(p1.nickname, 'my paypal')
        self.assertEqual(p1.user_id, 1)
        self.assertEqual(d1.user_name, 'John Jameson')
        self.assertEqual(d1.is_linked, True)
        p2 = app_db.session.query(Payment).get(2)
        self.assertEqual(p2, None)

    def test_interface_add_missing_details(self):
        data = {'nickname' : 'my debit', 'user_id' : 2, 'payment_type' : 'debit'}
        self.assertRaises(DataValidationError, self.ps.add_payment, data)

    def test_interface_add_bad_data_single_quote(self):
        data = BAD_DATA
        with self.assertRaises(DataValidationError) as e:
            self.ps.add_payment(data)
        self.assertTrue('missing nickname' in e.exception.message)

    def test_interface_add_bad_data_double_quote(self):
        data = BAD_DATA2
        with self.assertRaises(DataValidationError) as e:
            self.ps.add_payment(data)
        self.assertTrue('missing nickname' in e.exception.message)

    def test_interface_add_garbage(self):
        garbage = 'afv@#(&@(#Z@#>X@C8rq rq34tr0q934r 9qr@(#*(@!$))'
        with self.assertRaises(DataValidationError) as e:
            self.ps.add_payment(garbage)
        self.assertTrue('bad or no data' in e.exception.message)
    
    @mock.patch.object(Payment, 'deserialize')
    @mock.patch.object(Payment, 'serialize', return_value=CC_RETURN)
    @mock.patch.object(app_db, 'session', autospec=True)
    def test_interface_add_card_mock(self, mock_db, mock_serial, mock_deserial):
        payment = self.ps.add_payment(CREDIT)
        mock_serial.assert_called_once_with()
        mock_deserial.assert_called_once_with(CREDIT)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        self.assertTrue(type(payment), type({}))
        self.assertEqual(CC_RETURN, payment)
        self.assertEqual(CC_DETAIL, payment['details'])

    @mock.patch.object(Payment, 'deserialize')
    @mock.patch.object(Payment, 'serialize', return_value=PP_RETURN)
    @mock.patch.object(app_db, 'session')
    def test_interface_add_paypal_mock(self, mock_db, mock_serial, mock_deserial):
        temp = dict(PP_DETAIL, is_linked=True)
        payment = self.ps.add_payment(PAYPAL)
        mock_serial.assert_called_with()
        mock_deserial.assert_called_once_with(PAYPAL)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        self.assertTrue(type(payment), type({}))
        self.assertEqual(PP_RETURN, payment)
        self.assertEqual(temp, payment['details'])

    @mock.patch.object(app_db, 'session')
    def test_interface_query_payments(self, mock_db):
        # this is a long mock - note that the method call chaining matches that of the method call
        # on self.db in _query_payments

        # set the return value of ...filter_by() to a new mock whose all property is a function that
        # returns [DC_RETURN]; this is done so that when payment_query.all() is called, [DC_RETURN] is returned
        mock_db.query(Payment).filter_by.return_value = mock.MagicMock(all=lambda: [DC_RETURN])
        result = self.ps._query_payments(QUERY_ATTRIBUTES)

        mock_db.query(Payment).filter_by.assert_called_once_with(**QUERY_ATTRIBUTES)
        self.assertEqual(result, [DC_RETURN])

    @mock.patch.object(app_db, 'session')
    def test_interface_query_payments_error(self, mock_db):
        mock_db.query(Payment).filter_by.side_effect = PaymentServiceQueryError

        with self.assertRaises(PaymentServiceQueryError):
            result = self.ps._query_payments(QUERY_ATTRIBUTES)
        # also check that the mocked app_db was called appropriately
        mock_db.query(Payment).filter_by.assert_called_once_with(**QUERY_ATTRIBUTES)


class TestInterfaceFunctional(unittest.TestCase):
    """
    A class for doing more functional tests involving the interface.py classes.
    Actual db connections are used, so db resources are created and destroyed.
    """

    def setUp(self):
        payments.app.debug = True
        payments.app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://payments:payments@localhost:5432/test'
        app_db.create_all()  # make our sqlalchemy tables

        payments_to_add = (CREDIT, DEBIT, PAYPAL)
        for p in payments_to_add:
            payment = Payment()
            payment.deserialize(p)
            app_db.session.add(payment)
            app_db.session.commit()

        self.ps = PaymentService()

    def tearDown(self):
        app_db.session.remove()
        app_db.drop_all()

    def test_successful_query(self):
        # No mocking for this test since we want to test the method's ability to *actually* retrieve resources
        # the query attributes should match the CREDIT payment item

        result = self.ps._query_payments(QUERY_ATTRIBUTES)
        # in this case, PP_RETURN was the third item added, so its id should be 3, not 2
        PP_RETURN['payment_id'] = 3
        # should only be one result, so get the only element of the list
        assert result[0].serialize() == PP_RETURN

    def test_unsuccessful_query(self):
        # try querying for something that doesn't exist
        result = self.ps._query_payments(BAD_QUERY_ATTRIBUTES)
        assert result == []
