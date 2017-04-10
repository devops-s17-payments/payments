# Test cases can be run with either of the following:
# python -m unittest discover
# nosetests -v --rednose --nologcapture

import unittest
import mock


from app import payments
from app.db import app_db
from app.db.models import Payment, Detail
from app.db.interface import PaymentService, PaymentServiceQueryError, PaymentNotFoundError
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
# for put updates
PUT_CREDIT = {'nickname' : 'favcredit', 'user_id' : 1, 'payment_type' : 'credit',
    'details' : CC_DETAIL}
PUT_CREDIT_RETURN = {'nickname' : 'favcredit', 'user_id' : 1, 'payment_type' : 'credit',
    'details' : CC_DETAIL, 'is_default' : False, 'charge_history' : 0.0, 'payment_id' : 1}
# for patch updates
PATCH_CREDIT = { 'nickname' : 'boringcredit'}
PATCH_RETURN = {'nickname' : 'boringcredit', 'user_id' : 1, 'payment_type' : 'credit',
    'details' : CC_DETAIL, 'is_default' : False, 'charge_history' : 0.0, 'payment_id' : 1}

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
        with self.assertRaises(DataValidationError) as e:
            result = self.ps.get_payments(payment_ids=id)
            self.assertTrue('id 99 could not be found' in e)
        mock_db.query(Payment).filter.assert_called_once()
        mock_P.serialize.assert_not_called()

    @mock.patch.object(PaymentService, '_remove_soft_deletes')
    @mock.patch('app.db.models.Payment')
    @mock.patch.object(app_db, 'session')
    def test_interface_get_one_mock(self, mock_db, mock_P, mock_remove):
        id = [1]

        mock_P.serialize.return_value = CC_RETURN
        mock_db.query(Payment).filter.return_value.all.return_value = [mock_P]
        mock_remove.return_value = [mock_P]
        result = self.ps.get_payments(payment_ids=id)
        mock_db.query(Payment).filter.assert_called_once()
        #mock_db.query(Payment).filter.all.assert_called_once()
        mock_P.serialize.assert_called_once()
        mock_remove.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result, [CC_RETURN])

    @mock.patch.object(PaymentService, '_remove_soft_deletes')
    @mock.patch('app.db.models.Payment')
    @mock.patch.object(app_db, 'session')
    def test_interface_get_multiple_mock(self, mock_db, mock_P, mock_remove):
        ids = [1,2,3]

        mock_P.serialize.side_effect = [CC_RETURN, DC_RETURN, PP_RETURN]
        mock_db.query(Payment).filter.return_value.all.return_value = [mock_P, mock_P, mock_P]
        mock_remove.return_value = [mock_P, mock_P, mock_P]
        result = self.ps.get_payments(payment_ids=[ids])
        mock_db.query(Payment).filter.assert_called_once()
        mock_remove.assert_called_once()
        mock_P.serialize.assert_called()
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], CC_RETURN)

    @mock.patch.object(PaymentService, '_remove_soft_deletes')
    @mock.patch('app.db.models.Payment')
    @mock.patch.object(app_db, 'session')
    def test_interface_get_bad_multiple_mock(self, mock_db, mock_P, mock_remove):
        ids = [1,99, 2]

        mock_P.serialize.side_effect = [CC_RETURN, DC_RETURN]
        mock_db.query(Payment).filter.return_value.all.return_value = [mock_P, mock_P]
        mock_remove.return_value = [mock_P, mock_P]
        result = self.ps.get_payments(payment_ids=[ids])
        mock_db.query(Payment).filter.assert_called_once()
        mock_P.serialize.assert_called()
        mock_remove.assert_called_once()
        self.assertEqual(len(result), 2)


    @mock.patch.object(PaymentService, '_remove_soft_deletes')
    @mock.patch('app.db.models.Payment')
    @mock.patch.object(app_db, 'session')
    def test_interface_get_all_mock(self, mock_db, mock_P, mock_remove):
        mock_P.serialize.side_effect = [CC_RETURN, DC_RETURN]
        mock_db.query(Payment).all.return_value = [mock_P, mock_P]
        mock_remove.return_value = [mock_P, mock_P]
        result = self.ps.get_payments()
        mock_db.query(Payment).all.assert_called_once()
        mock_remove.assert_called_once()
        mock_P.serialize.assert_called()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], CC_RETURN)

    @mock.patch.object(PaymentService, '_remove_soft_deletes')
    @mock.patch.object(PaymentService, '_query_payments', return_value=CC_RETURN)
    @mock.patch('app.db.models.Payment')
    def test_interface_get_query_nick_mock(self, mock_P, mock_q, mock_remove):
        q = {'nickname' : 'my credit'}

        mock_P.serialize.return_value = CC_RETURN
        mock_q.return_value = [mock_P]
        mock_remove.return_value = [mock_P]
        result = self.ps.get_payments(payment_attributes=q)
        mock_q.assert_called_once()
        mock_remove.assert_called_once()
        mock_P.serialize.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], CC_RETURN)

    @mock.patch.object(PaymentService, '_remove_soft_deletes')
    @mock.patch.object(PaymentService, '_query_payments', side_effect=PaymentServiceQueryError)
    @mock.patch('app.db.models.Payment')
    def test_interface_bad_query_mock(self, mock_P, mock_q, mock_remove):
        q = {'whatever' : 'man'}

        with self.assertRaises(DataValidationError) as e:
            result = self.ps.get_payments(payment_attributes=q)
        mock_q.assert_called_once()
        mock_P.serialize.assert_not_called()
        mock_remove.assert_not_called()

    def test_interface_get_single_payment(self):
        id = [1]

        result = self.ps.get_payments(payment_ids=id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], CC_RETURN)

    def test_interface_get_missing_payment(self):
        id = [99]

        with self.assertRaises(DataValidationError) as e:
            result = self.ps.get_payments(payment_ids=id)
            self.assertTrue('id 99 could not be found' in e)

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

    def test_interface_get_is_removed(self):
        p = Payment()
        p.deserialize(PAYPAL)
        p.is_removed = True
        app_db.session.add(p)
        app_db.session.commit()

        result = self.ps.get_payments()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], CC_RETURN)

    def test_interface_remove_soft_delete(self):
        data = (CREDIT, DEBIT, PAYPAL)
        payments = []
        for d in data:
            p = Payment()
            p.deserialize(d)
            p.is_removed = True
            payments.append(p)

        self.assertEqual(len(payments), 3)
        payments = self.ps._remove_soft_deletes(payments)
        self.assertEqual(len(payments), 0)
        self.assertEqual(payments, [])

    def test_interface_query_nickname(self):
        q = {'nickname' : 'my credit'}
        result = self.ps.get_payments(payment_attributes=q)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0], CC_RETURN)

    def test_interface_add_card_returns_json(self):
        data = CREDIT
        payment = self.ps.add_payment(data)
        self.assertTrue(type(payment), type({}))
        self.assertTrue(payment['nickname'] == 'my credit')
        self.assertTrue(payment['details']['user_name'] == 'Jimmy Jones')

    def test_interface_add_card_to_db(self):
        data = CREDIT
        p1 = app_db.session.query(Payment).get(2)
        self.assertEqual(p1, None)
        self.ps.add_payment(data)
        p1 = app_db.session.query(Payment).get(2)
        d1 = p1.details
        self.assertEqual(p1.nickname, 'my credit')
        self.assertEqual(d1.user_name, 'Jimmy Jones')

    def test_interface_add_paypal_to_db(self):
        data = PAYPAL
        p1 = app_db.session.query(Payment).get(2)
        self.assertEqual(p1, None)
        self.ps.add_payment(data)
        p1 = app_db.session.query(Payment).get(2)
        d1 = p1.details
        self.assertEqual(p1.nickname, 'my paypal')
        self.assertEqual(p1.user_id, 1)
        self.assertEqual(d1.user_name, 'John Jameson')
        self.assertEqual(d1.is_linked, True)

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

    @mock.patch.object(PaymentService, '_remove_soft_deletes')
    @mock.patch.object(app_db, 'session')
    def test_interface_query_payments(self, mock_db, mock_remove):
        # this is a long mock - note that the method call chaining matches that of the method call
        # on self.db in _query_payments


        # set the return value of ...filter_by() to a new mock whose all property is a function that
        # returns [DC_RETURN]; this is done so that when payment_query.all() is called, [DC_RETURN] is returned
        mock_db.query(Payment).filter_by.return_value = mock.MagicMock(all=lambda: [DC_RETURN])
        mock_remove.return_value = [DC_RETURN]
        result = self.ps._query_payments(QUERY_ATTRIBUTES)

        mock_db.query(Payment).filter_by.assert_called_once_with(**QUERY_ATTRIBUTES)
        mock_remove.assert_called_once()
        self.assertEqual(result, [DC_RETURN])


    @mock.patch.object(app_db, 'session')
    def test_interface_query_payments_error(self, mock_db):
        mock_db.query(Payment).filter_by.side_effect = PaymentServiceQueryError

        with self.assertRaises(PaymentServiceQueryError):
            result = self.ps._query_payments(QUERY_ATTRIBUTES)
        # also check that the mocked app_db was called appropriately
        mock_db.query(Payment).filter_by.assert_called_once_with(**QUERY_ATTRIBUTES)

    #Testing delete/remove payments
    @mock.patch.object(app_db, 'session')
    def test_interface_delete_payment_with_valid_id(self, mock_db):
        #payment_to_be_deleted = mock_db.query(Payment).get(1)
        result = self.ps.remove_payment(payment_id=1)
        payment_after_deletion = mock_db.query(Payment).get(1)
        self.assertTrue(payment_after_deletion.is_removed)
        #TODO - next sprint : do get, check count, should be one less
    
    @mock.patch.object(app_db, 'session')
    def test_interface_delete_payment_with_invalid_id(self, mock_db):
        invalid_id = 28462
        payment_to_be_deleted = mock_db.query(Payment).get(invalid_id)
        self.assertNotEqual(payment_to_be_deleted.id,invalid_id)
        result = self.ps.remove_payment(payment_id=invalid_id)
        self.assertIsNone(result)
        #This doesn't raise an error because Deletes are idempotent
        payment_after_deletion = mock_db.query(Payment).get(invalid_id)
        self.assertNotEqual(payment_after_deletion.id,invalid_id)
        #TODO - next sprint : do get, check count, should be same

#Test cases for update interface method
#valid PUT data
    @mock.patch.object(PaymentService,'is_valid_put',return_value = True)
    @mock.patch.object(app_db, 'session')
    @mock.patch('app.db.models.Payment')
    def test_interface_update_with_valid_put_data(self,mock_P,mock_db,mock_isvalid):
        mock_db.query(Payment).get.return_value = mock_P
        mock_P.serialize.return_value = PUT_CREDIT_RETURN
        resp = self.ps.update_payment(1,payment_replacement = PUT_CREDIT)
        mock_P.serialize.assert_called()
        mock_isvalid.assert_called_once()
        mock_P.deserialize_put.assert_called_once()
        mock_db.commit.assert_called_once()
    
#none put and patch inputs
    @mock.patch.object(app_db, 'session')
    def test_interface_update_with_vaild_id_invalidargs(self, mock_db):
        with self.assertRaises(DataValidationError):
            result = self.ps.update_payment(111,None,None)
        mock_db.commit.assert_not_called()
    
#update a non existing (payment id not found or is removed = true) payment
    @mock.patch.object(app_db, 'session')
    def test_interface_update_with_invalid_id(self, mock_db):
        mock_db.query(Payment).get.return_value = None
        with self.assertRaises(PaymentNotFoundError):
            result = self.ps.update_payment(111,payment_replacement = PUT_CREDIT)
        mock_db.query(Payment).get.assert_called_with(111)
        mock_db.commit.assert_not_called()

#updating with a false is_valid update input
    @mock.patch.object(PaymentService,'is_valid_put',return_value = False)
    @mock.patch.object(app_db, 'session')
    @mock.patch('app.db.models.Payment')
    def test_interface_update_with_invalid_input(self,mock_P, mock_db,mock_isvalid):
        mock_db.query(Payment).get.return_value = mock_P
        with self.assertRaises(DataValidationError):
            result = self.ps.update_payment(111,payment_replacement=PUT_CREDIT_RETURN)
        mock_isvalid.assert_called_once()
        mock_P.deserialize_put.assert_not_called()
        mock_db.commit.assert_not_called()

#patch with valid data
    @mock.patch.object(app_db, 'session')
    @mock.patch('app.db.models.Payment')
    def test_interface_update_with_valid_patch_data(self,mock_P, mock_db):
        mock_db.query(Payment).get.return_value = mock_P
        resp = self.ps.update_payment(1,payment_attributes = {'nickname' : 'favourite'})
        mock_db.query(Payment).get.assert_called_with(1)
        mock_P.serialize.assert_called()
        mock_P.deserialize_put.assert_called_once()
        mock_db.commit.assert_called_once()

# patch with unupdatable fields
    @mock.patch.object(app_db, 'session')
    @mock.patch('app.db.models.Payment')
    def test_interface_update_with_invalid_patch_data(self,mock_P, mock_db):
        mock_db.query(Payment).get.return_value = mock_P
        with self.assertRaises(DataValidationError):
            resp = self.ps.update_payment(1,payment_attributes = {'is_default' : 'True'})
        mock_db.query(Payment).get.assert_called_with(1)
        mock_P.serialize.assert_called_once()
        mock_P.deserialize_put.assert_not_called()
        mock_db.commit.assert_not_called()

    # set-default action test cases
    @mock.patch.object(app_db, 'session')
    @mock.patch.object(PaymentService, '_query_payments')
    def test_interface_payment_set_default_action_success(self, mock_query, mock_db):
        user_id = payment_id = 1
        payment_default_data = {'payment_id' : payment_id}
        user_data = {'user_id': user_id}

        cc_payment = Payment()
        cc_payment.deserialize(CC_RETURN)
        cc_payment.id = 1

        pp_payment = Payment()
        pp_payment.deserialize(PP_RETURN)
        pp_payment.id = 3

        self.assertFalse(cc_payment.is_default)
        self.assertFalse(pp_payment.is_default)

        mock_query.return_value = [cc_payment, pp_payment]

        result = self.ps.perform_payment_action(user_id,payment_attributes=payment_default_data)
        self.assertTrue(result)

        self.assertTrue(cc_payment.is_default)
        self.assertFalse(pp_payment.is_default)

        mock_query.assert_called_once_with(payment_attributes=user_data)
        mock_db.commit.assert_called_once()

    @mock.patch.object(app_db, 'session')
    @mock.patch.object(PaymentService, '_query_payments')
    def test_interface_payment_set_default_action_with_no_payment_found_for_the_user(self, mock_query, mock_db):
        user_id = 1
        payment_default_data = {'payment_id' : 2}
        user_data = {'user_id': user_id}

        cc_payment = Payment()
        cc_payment.deserialize(CC_RETURN)
        cc_payment.id = 1

        pp_payment = Payment()
        pp_payment.deserialize(PP_RETURN)
        pp_payment.id = 3

        self.assertFalse(cc_payment.is_default)
        self.assertFalse(pp_payment.is_default)

        mock_query.return_value = [cc_payment, pp_payment]

        result = self.ps.perform_payment_action(user_id,payment_attributes=payment_default_data)
        self.assertFalse(result)

        self.assertFalse(cc_payment.is_default)
        self.assertFalse(pp_payment.is_default)

        mock_query.assert_called_once_with(payment_attributes=user_data)
        mock_db.commit.assert_not_called()

    @mock.patch.object(app_db, 'session')
    @mock.patch.object(PaymentService, '_query_payments', side_effect = PaymentServiceQueryError)
    def test_interface_payment_set_default_action_with_no_payments_for_user(self, mock_query, mock_db):
        user_id = 1
        payment_default_data = {'payment_id' : 2}
        user_data = {'user_id': user_id}

        with self.assertRaises(DataValidationError) as e:
            result = self.ps.perform_payment_action(user_id,payment_attributes=payment_default_data)

        self.assertTrue('Payments not found' in e.exception.message)

        mock_query.assert_called_once_with(payment_attributes=user_data)
        mock_db.commit.assert_not_called()

    #charge action test cases
    @mock.patch.object(app_db, 'session')
    @mock.patch.object(PaymentService, '_query_payments')
    def test_interface_payment_charge_action_for_card_success(self, mock_query, mock_db):
        #This test case also tests is_expired (as the default payment here is a card) interface utility method which returns false
        user_id = 1
        amount_data = {'amount' : 25.0}
        user_data = {'user_id': user_id}

        cc_payment = Payment()
        cc_payment.deserialize(CC_RETURN)
        cc_payment.id = 1
        cc_payment.is_default = True

        pp_payment = Payment()
        pp_payment.deserialize(PP_RETURN)
        pp_payment.id = 3

        self.assertEqual(cc_payment.charge_history,0.0)
        self.assertEqual(pp_payment.charge_history,0.0)

        mock_query.return_value = [cc_payment, pp_payment]

        result = self.ps.perform_payment_action(user_id,payment_attributes=amount_data)
        self.assertTrue(result)

        self.assertEqual(cc_payment.charge_history,25.0)
        self.assertEqual(pp_payment.charge_history,0.0)

        mock_query.assert_called_once_with(payment_attributes=user_data)
        mock_db.commit.assert_called_once()

    @mock.patch.object(app_db, 'session')
    @mock.patch.object(PaymentService, '_query_payments')
    def test_interface_payment_charge_action_for_paypal_success(self, mock_query, mock_db):
        user_id = 1
        amount_data = {'amount' : 25.0}
        user_data = {'user_id': user_id}

        cc_payment = Payment()
        cc_payment.deserialize(CC_RETURN)
        cc_payment.id = 1

        pp_payment = Payment()
        pp_payment.deserialize(PP_RETURN)
        pp_payment.id = 3
        pp_payment.details.is_linked = True
        pp_payment.is_default = True

        self.assertEqual(cc_payment.charge_history,0.0)
        self.assertEqual(pp_payment.charge_history,0.0)

        mock_query.return_value = [cc_payment, pp_payment]

        result = self.ps.perform_payment_action(user_id,payment_attributes=amount_data)
        self.assertTrue(result)

        self.assertEqual(cc_payment.charge_history,0.0)
        self.assertEqual(pp_payment.charge_history,25.0)

        mock_query.assert_called_once_with(payment_attributes=user_data)
        mock_db.commit.assert_called_once()

    @mock.patch.object(app_db, 'session')
    @mock.patch.object(PaymentService, '_query_payments')
    def test_interface_payment_charge_action_with_no_default_payment(self, mock_query, mock_db):
        user_id = 1
        amount_data = {'amount' : 25.0}
        user_data = {'user_id': user_id}

        cc_payment = Payment()
        cc_payment.deserialize(CC_RETURN)
        cc_payment.id = 1

        pp_payment = Payment()
        pp_payment.deserialize(PP_RETURN)
        pp_payment.id = 3

        self.assertEqual(cc_payment.charge_history,0.0)
        self.assertEqual(pp_payment.charge_history,0.0)

        mock_query.return_value = [cc_payment, pp_payment]

        with self.assertRaises(DataValidationError) as e:
            result = self.ps.perform_payment_action(user_id,payment_attributes=amount_data)

        self.assertTrue('update the default_payment' in e.exception.message)

        self.assertEqual(cc_payment.charge_history,0.0)
        self.assertEqual(pp_payment.charge_history,0.0)

        mock_query.assert_called_once_with(payment_attributes=user_data)
        mock_db.commit.assert_not_called()

    @mock.patch.object(app_db, 'session')
    @mock.patch.object(PaymentService, '_query_payments')
    def test_interface_payment_charge_action_with_default_payment_card_expired(self, mock_query, mock_db):
        #This test case also tests is_expired interface utility method which returns true
        user_id = 1
        amount_data = {'amount' : 25.0}
        user_data = {'user_id': user_id}

        cc_payment = Payment()
        cc_payment.deserialize(CC_RETURN)
        cc_payment.id = 1
        cc_payment.is_default = True
        cc_payment.details.expires = '01/2017'

        pp_payment = Payment()
        pp_payment.deserialize(PP_RETURN)
        pp_payment.id = 3

        self.assertEqual(cc_payment.charge_history,0.0)
        self.assertEqual(pp_payment.charge_history,0.0)

        mock_query.return_value = [cc_payment, pp_payment]

        with self.assertRaises(DataValidationError) as e:
            result = self.ps.perform_payment_action(user_id,payment_attributes=amount_data)

        self.assertTrue('is expired' in e.exception.message)

        self.assertEqual(cc_payment.charge_history,0.0)
        self.assertEqual(pp_payment.charge_history,0.0)

        mock_query.assert_called_once_with(payment_attributes=user_data)
        mock_db.commit.assert_not_called()

    @mock.patch.object(app_db, 'session')
    @mock.patch.object(PaymentService, '_query_payments')
    def test_interface_payment_charge_action_with_default_payment_paypal_not_linked(self, mock_query, mock_db):
        user_id = 1
        amount_data = {'amount' : 25.0}
        user_data = {'user_id': user_id}

        cc_payment = Payment()
        cc_payment.deserialize(CC_RETURN)
        cc_payment.id = 1

        pp_payment = Payment()
        pp_payment.deserialize(PP_RETURN)
        pp_payment.id = 3
        pp_payment.is_default = True
        pp_payment.details.is_linked = False

        self.assertEqual(cc_payment.charge_history,0.0)
        self.assertEqual(pp_payment.charge_history,0.0)

        mock_query.return_value = [cc_payment, pp_payment]

        with self.assertRaises(DataValidationError) as e:
            result = self.ps.perform_payment_action(user_id,payment_attributes=amount_data)

        self.assertTrue(' not linked' in e.exception.message)

        self.assertEqual(cc_payment.charge_history,0.0)
        self.assertEqual(pp_payment.charge_history,0.0)

        mock_query.assert_called_once_with(payment_attributes=user_data)
        mock_db.commit.assert_not_called()

    @mock.patch.object(app_db, 'session')
    @mock.patch.object(PaymentService, '_query_payments', side_effect = PaymentServiceQueryError)
    def test_interface_payment_charge_action_with_no_payments_for_user(self, mock_query, mock_db):
        user_id = 1
        amount_data = {'amount' : 25.0}
        user_data = {'user_id': user_id}

        with self.assertRaises(DataValidationError) as e:
            result = self.ps.perform_payment_action(user_id,payment_attributes=amount_data)

        self.assertTrue('Payments not found' in e.exception.message)

        mock_query.assert_called_once_with(payment_attributes=user_data)
        mock_db.commit.assert_not_called()

    #test case for perform_payment_action in case payment_attributes (or request data) has any other key other than payment_id or amount
    @mock.patch.object(app_db, 'session')
    @mock.patch.object(PaymentService, '_query_payments')
    def test_interface_payment_action_with_wrong_actionable_data(self, mock_query, mock_db):
        user_id = 1
        wrong_data = {'history' : 12312}
        user_data = {'user_id': user_id}

        cc_payment = Payment()
        cc_payment.deserialize(CC_RETURN)
        cc_payment.id = 1

        pp_payment = Payment()
        pp_payment.deserialize(PP_RETURN)
        pp_payment.id = 3

        mock_query.return_value = [cc_payment, pp_payment]

        with self.assertRaises(DataValidationError) as e:
            result = self.ps.perform_payment_action(user_id,payment_attributes=wrong_data)

        self.assertTrue('bad or missing data' in e.exception.message)

        mock_query.assert_called_once_with(payment_attributes=user_data)
        mock_db.commit.assert_not_called()

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

    def test_load_sample(self):
        self.assertTrue(len(self.ps.get_payments()), 3)
        details = {
            'user_name' : 'test',
            'user_email' : 'test@gmail.com',
            'is_linked' : True
        }
        public_data = {
            'nickname' : 'nickname',
            'user_id' : 1,
            'payment_type' : 'paypal',
            'details' : details
        }
        private_data = {
            'is_default' : True,
            'is_removed' : False,
            'charge_history' : 9.99
        }
        PaymentService.load_sample(public_data, private_data)
        self.assertTrue(len(self.ps.get_payments()), 4)
        self.assertTrue(self.ps._query_payments({'id' : 1})[0].nickname, 'nickname')
