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

DC_DETAIL = {'user_name' : 'Jeremy Jenkins', 'card_number' : '4444333322221111',
             'expires' : '02/2020', 'card_type' : 'Visa'}

PP_DETAIL = {'user_name' : 'John Jameson', 'user_email' : 'jj@aol.com'}

CREDIT = {'nickname' : 'my credit', 'user_id' : 1, 'payment_type' : 'credit', 
          'details' : CC_DETAIL}

DEBIT = {'nickname' : 'my debit', 'user_id' : 1, 'payment_type' : 'debit', 
         'details' : DC_DETAIL}

PAYPAL = {'nickname' : 'my paypal', 'user_id' : 1, 'payment_type' : 'paypal', 
          'details' : PP_DETAIL}

BAD_DATA = {'bad key' : 'my paypal', 'user_id' : 2, 'payment_type' : 'paypal', 
            'details' : PP_DETAIL}

PP_RETURN = dict(PAYPAL, is_default=False, charge_history=0.0, payment_id=3)
PP_RETURN['details']['is_linked'] = True

CC_RETURN = dict(CREDIT, is_default=False, charge_history=0.0, payment_id=1)

DC_RETURN = dict(DEBIT, is_default=False, charge_history=0.0, payment_id=2)


class TestInterface(unittest.TestCase):

    def setUp(self):
        payments.app.debug = True
        payments.app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://payments:payments@localhost:5432/test'
        app_db.create_all()  # make our sqlalchemy tables

        ''' seed data '''
        p = Payment()
        p.deserialize(CREDIT)
        app_db.session.add(p)
        app_db.session.commit()
        self.ps = PaymentService()
        self.app = payments.app.test_client()

    def tearDown(self):
        app_db.session.remove()
        app_db.drop_all()


    @mock.patch('app.db.models.Payment')
    @mock.patch.object(app_db, 'session')
    def test_interface_get_missing_mock(self, mock_db, mock_P):
        id = [99]
        
        mock_db.query(Payment).filter.return_value.all.return_value = []
        result = self.ps.get_payments(payment_ids=id)
        mock_db.query(Payment).filter.assert_called_once()
        #mock_db.query(Payment).filter.all.assert_called_once()
        mock_P.serialize.assert_not_called()
        self.assertEqual(result, [])
    
    @mock.patch('app.db.models.Payment')
    @mock.patch.object(app_db, 'session')
    def test_interface_get_one_mock(self, mock_db, mock_P):
        id = [1]
        
        mock_P.serialize.return_value = CC_RETURN
        mock_db.query(Payment).filter.return_value.all.return_value = [mock_P]
        result = self.ps.get_payments(payment_ids=id)
        mock_db.query(Payment).filter.assert_called_once()
        #mock_db.query(Payment).filter.all.assert_called_once()
        mock_P.serialize.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result, [CC_RETURN])

    @mock.patch('app.db.models.Payment')
    @mock.patch.object(app_db, 'session')
    def test_interface_get_multiple_mock(self, mock_db, mock_P):
        ids = [1,2,3]
        
        mock_P.serialize.side_effect = [CC_RETURN, DC_RETURN, PP_RETURN]
        mock_db.query(Payment).filter.return_value.all.return_value = [mock_P, mock_P, mock_P]
        result = self.ps.get_payments(payment_ids=[ids])
        mock_db.query(Payment).filter.assert_called_once()
        #mock_db.query(Payment).filter.all.assert_called_once()
        mock_P.serialize.assert_called()
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], CC_RETURN)

    @mock.patch('app.db.models.Payment')
    @mock.patch.object(app_db, 'session')
    def test_interface_get_bad_multiple_mock(self, mock_db, mock_P):
        ids = [1,99, 2]
        
        mock_P.serialize.side_effect = [CC_RETURN, DC_RETURN]
        mock_db.query(Payment).filter.return_value.all.return_value = [mock_P, mock_P]
        result = self.ps.get_payments(payment_ids=[ids])
        mock_db.query(Payment).filter.assert_called_once()
        #mock_db.query(Payment).filter.all.assert_called_once()
        mock_P.serialize.assert_called()
        self.assertEqual(len(result), 2)
    
    @mock.patch('app.db.models.Payment')
    @mock.patch.object(app_db, 'session')
    def test_interface_get_all_mock(self, mock_db, mock_P):
        
        mock_P.serialize.side_effect = [CC_RETURN, DC_RETURN]
        mock_db.query(Payment).all.return_value = [mock_P, mock_P]
        result = self.ps.get_payments()
        mock_db.query(Payment).all.assert_called_once()
        mock_P.serialize.assert_called()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], CC_RETURN)

    @mock.patch.object(PaymentService, '_query_payments', return_value=CC_RETURN)
    @mock.patch('app.db.models.Payment')
    def test_interface_get_query_nick_mock(self, mock_P, mock_q):
        q = {'nickname' : 'my credit'}

        mock_P.serialize.return_value = [CC_RETURN]
        mock_q.return_value = [mock_P]
        result = self.ps.get_payments(payment_attributes=q)
        
        result = self.ps.get_payments()
        mock_q.assert_called_once()
        mock_P.serialize.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], CC_RETURN)

    @mock.patch.object(PaymentService, '_query_payments', side_effect=PaymentServiceQueryError)
    @mock.patch('app.db.models.Payment')
    def test_interface_bad_query_mock(self, mock_P, mock_q):
        q = {'whatever' : 'man'}

        with self.assertRaises(DataValidationError) as e:
            result = self.ps.get_payments(payment_attributes=q)
        mock_q.assert_called_once()
        mock_P.serialize.assert_not_called()

    def test_interface_get_single_payment(self):
        id = [1]
        
        result = self.ps.get_payments(payment_ids=id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], CC_RETURN)

    def test_interface_get_missing_payment(self):
        id = [99]
        
        result = self.ps.get_payments(payment_ids=id)
        self.assertEqual(len(result), 0)
        self.assertEqual(result, [])

    def test_interface_get_three_consec_payment(self):
        ids = [1,2,3]

        p = Payment()
        p.deserialize(DEBIT)
        app_db.session.add(p)
        p = Payment()
        p.deserialize(PAYPAL)
        app_db.session.add(p)
        app_db.session.commit()
        
        result = self.ps.get_payments(payment_ids=ids)
        self.assertEqual(len(result), 3)
        self.assertEqual(result, [CC_RETURN, DC_RETURN, PP_RETURN])

    def test_interface_get_two_non_consec_payment(self):
        ids = [1, 3]

        p = Payment()
        p.deserialize(DEBIT)
        app_db.session.add(p)
        p = Payment()
        p.deserialize(PAYPAL)
        app_db.session.add(p)
        app_db.session.commit()
        
        result = self.ps.get_payments(payment_ids=ids)
        self.assertEqual(len(result), 2)
        self.assertEqual(result, [CC_RETURN, PP_RETURN])

    def test_interface_get_bad_list(self):
        ids = [1, 99, 2]

        p = Payment()
        p.deserialize(DEBIT)
        app_db.session.add(p)
        app_db.session.commit()
        
        result = self.ps.get_payments(payment_ids=ids)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1], DC_RETURN)

    def test_interface_get_all(self):
        p = Payment()
        p.deserialize(PAYPAL)
        app_db.session.add(p)
        app_db.session.commit()

        result = self.ps.get_payments()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], CC_RETURN)

    ''' 
        ### not implemented yet ###

    def test_interface_query_nickname(self):
        q = {'nickname' : 'my credit'}

        result = self.ps.get_payments(payment_attributes=q)
        self.assertEqual(len(result), 0)
        self.assertTrue(result[0], CC_RETURN)
    '''

