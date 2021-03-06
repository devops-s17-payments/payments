# Test cases can be run with either of the following:
# python -m unittest discover
# nosetests -v --rednose --nologcapture

import unittest, json, mock
from mock import patch
from app import payments
from app.db.interface import PaymentService, PaymentNotFoundError
from flask_api import status   # HTTP Status Codes
from flask import make_response,jsonify
from app.error_handlers import DataValidationError
from mock import patch

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
BAD_DATA = {'bad key' : 'my paypal', 'user_id' : 2, 'payment_type' : 'paypal',
            'details' : PP_DETAIL}

BAD_DATA2 = {"nicknam3" : "my paypal", "user_id" : 1, "payment_type" : "paypal",
             "details" : {"user_name" : "John Jameson", "user_email" : "jj@aol.com"}}

PP_RETURN = dict(PAYPAL, is_default=False, charge_history=0.0, payment_id=3)
PP_RETURN['details']['is_linked'] = True

CC_RETURN = dict(CREDIT, is_default=False, charge_history=0.0, payment_id=1)

DC_RETURN = dict(DEBIT, is_default=False, charge_history=0.0, payment_id=2)

SAMPLE_PAYMENT = {
    'id': 0,
    'nickname': 'my credit',
    'user_id': 1,
    'payment_type': 'credit',
    'details':
        {
            'user_name': 'Jimmy Jones',
            'card_number': '1111222233334444',
            'expires': '01/2019',
            'card_type': 'Mastercard'
        }
}

SAMPLE_PAYMENTS = [
    {
        'id': 0,
        'nickname': 'credit_one',
        'user_id': 1,
        'payment_type': 'credit',
        'details':
            {
                'user_name': 'Tommy Stones',
                'card_number': '123456789000',
                'expires': '02/2020',
                'card_type': 'Mastercard'
            }
    },
    {
        'id': 1,
        'nickname': 'credit_two',
        'user_id': 1,
        'payment_type': 'paypal',
        'details':
            {
                'user_name': 'Tommy Stones',
                'user_email': 'tommy@stones.abc',
                'is_linked': True
            }
    },
    {
        'id': 2,
        'nickname': 'amex',
        'user_id': 2,
        'payment_type': 'credit',
        'details':
            {
                'user_name': 'Jillian Jasper',
                'card_number': '0101010101010101',
                'expires': '12/2020',
                'card_type': 'American Express'
            }
    }
]

class TestPaymentsCRUD(unittest.TestCase):
    """
    Test cases for CRUD methods contained in payments.py.
    """
    def setUp(self):
        # Important!  Need to use the test_client method in order to test the flask-made routes
        self.app = payments.app.test_client()

    def test_get_payments_ok(self):
        # return 200 OK and a simple payload for a successful request
        id = 0
        with patch.object(PaymentService, 'get_payments', return_value=SAMPLE_PAYMENT) as mocked_service:
            response = self.app.get('/payments/{}'.format(id))

            # when doing the assertion methods on a mocked object, make *very* sure that the method
            # is one of the actual methods; otherwise the assertion will be meaningless
            mocked_service.assert_called_once_with(payment_ids=[id])
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(json.loads(response.data), SAMPLE_PAYMENT)

    def test_get_payments_not_found(self):
        # something goes wrong with the GET request and the resource cannot be found
        id = 0
        with patch.object(PaymentService, 'get_payments', side_effect=Exception) as mocked_service:
            error_response = payments.NOT_FOUND_ERROR_BODY
            error_response['error'] = error_response['error'].format(id)
            response = self.app.get('/payments/{}'.format(id))

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(json.loads(response.data), error_response)

    def test_list_payments_all(self):
        # ensure that all payments are returned
        with patch.object(PaymentService, 'get_payments', return_value=SAMPLE_PAYMENTS) as mocked_service:
            response = self.app.get('/payments')

            mocked_service.assert_called_once_with()
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(json.loads(response.data), SAMPLE_PAYMENTS)

    def test_list_payments_by_ids(self):
        # return payments that have specific ids
        ids = [1,2]
        # the final query string will look like: ?ids=1&ids=2
        # flask will know how to deal with a query param appearing multiple times
        ids_query_string = 'ids={}&ids={}'.format(ids[0], ids[1])
        payments_to_return = SAMPLE_PAYMENTS[1:3]

        with patch.object(PaymentService, 'get_payments', return_value=payments_to_return) as mocked_service:
            response = self.app.get('/payments?{}'.format(ids_query_string))

            mocked_service.assert_called_once_with(payment_ids=ids)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(json.loads(response.data), payments_to_return)

    def test_list_payments_by_attribute(self):
        # return payments that have a specific attribute
        specific_attribute = 'payment_type'
        specific_attribute_value = 'paypal'
        attribute_params = {'payment_type': 'paypal'}
        paypal_payment = SAMPLE_PAYMENTS[1]

        with patch.object(PaymentService, 'get_payments', return_value=paypal_payment) as mocked_service:
            response = self.app.get('/payments?{}={}'.format(specific_attribute, specific_attribute_value))

            mocked_service.assert_called_once_with(payment_attributes=attribute_params)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(json.loads(response.data), paypal_payment)

    def test_list_payments_not_found(self):
        # attempt to retrieve payments and catch the exception raised; return 404
        with patch.object(PaymentService, 'get_payments', side_effect=Exception) as mocked_service:
            response = self.app.get('/payments')

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(json.loads(response.data), payments.GENERAL_NOT_FOUND_ERROR)

    def test_list_payments_with_ids_and_other_params(self):
        # test to make sure that the ids parameter takes priority over other parameters
        ids = [1,2]
        ids_query_string = 'ids={}&ids={}'.format(ids[0], ids[1])
        payments_to_return = SAMPLE_PAYMENTS[1:3]
        other_param = 'nickname'
        other_param_value = 'amex'

        with patch.object(PaymentService, 'get_payments', return_value=payments_to_return) as mocked_service:
            query_string = '{}&{}={}'.format(ids_query_string, other_param, other_param_value)
            response = self.app.get('/payments?{}'.format(query_string))

            # important - we should call the get_payments method with payment_ids, *not* payment_attributes
            mocked_service.assert_called_once_with(payment_ids=ids)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(json.loads(response.data), payments_to_return)

    @mock.patch.object(PaymentService, 'add_payment', return_value=CC_RETURN)
    def test_crud_create_card(self, mock_ps_add):
        data = json.dumps(CREDIT)
        resp = self.app.post('/payments', data=data, content_type='application/json')
        mock_ps_add.assert_called_with(CREDIT)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json.loads(resp.data), {'created' : CC_RETURN})

    @mock.patch.object(PaymentService, 'add_payment', return_value=PP_RETURN)
    def test_crud_create_paypal(self, mock_ps_add):
        data = json.dumps(PAYPAL)
        resp = self.app.post('/payments', data=data, content_type='application/json')
        mock_ps_add.assert_called_with(PAYPAL)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json.loads(resp.data), {'created' : PP_RETURN})

    @mock.patch.object(PaymentService, 'add_payment')
    def test_crud_create_two_cards(self, mock_ps_add):
        data = json.dumps(CREDIT)
        mock_ps_add.return_value = CC_RETURN
        resp = self.app.post('/payments', data=data, content_type='application/json')
        mock_ps_add.assert_called_with(CREDIT)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json.loads(resp.data), {'created' : CC_RETURN})

        data = json.dumps(DEBIT)
        mock_ps_add.return_value = DC_RETURN
        resp = self.app.post('/payments', data=data, content_type='application/json')
        mock_ps_add.assert_called_with(DEBIT)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json.loads(resp.data), {'created' : DC_RETURN})

    @mock.patch.object(PaymentService, 'add_payment', side_effect=DataValidationError)
    def test_crud_create_bad_data_single_quotes(self, mock_ps_add):
        data = json.dumps(BAD_DATA)

        resp = self.app.post('/payments', data=data, content_type='application/json')
        mock_ps_add.assert_called_with(BAD_DATA)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("error" in resp.data)

    @mock.patch.object(PaymentService, 'add_payment', side_effect=DataValidationError)
    def test_crud_create_bad_data_double_quotes(self, mock_ps_add):
        data = json.dumps(BAD_DATA2)

        resp = self.app.post('/payments', data=data, content_type='application/json')
        mock_ps_add.assert_called_with(BAD_DATA2)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("error" in resp.data)

    @mock.patch.object(PaymentService, 'add_payment', side_effect=DataValidationError)
    def test_crud_create_garbage(self, mock_ps_add):
        garbage = 'a@$*&@#sdassdc3r 3284723X43&^@!#@*#'
        resp = self.app.post('/payments', data=garbage, content_type='application/json')
        mock_ps_add.assert_called_with(None)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("error" in resp.data)

    #Tests for Deleting
    @mock.patch.object(PaymentService, 'remove_payment')
    def test_delete_payment_with_valid_id(self, mock_ps_delete):
        resp = self.app.delete('/payments/1')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue('' in resp.data)

    @mock.patch.object(PaymentService, 'remove_payment')
    def test_delete_payment_with_invalid_id(self, mock_ps_delete):
        resp = self.app.delete('/payments/1345345')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue('' in resp.data)

    def test_delete_payment_with_gibberish_id(self):
        resp = self.app.delete('/payments/jghjeshg')
        #will not go to the payment service so no need to mock
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue('Not Found' in resp.data)

    #Tests for action - set-default
    @mock.patch.object(PaymentService, 'perform_payment_action')
    def test_set_default_action_with_no_payments_for_user_id(self, mock_db_action):
        user_id = payment_id = 1
        payment_data = {'payment_id': payment_id}
        data = json.dumps(payment_data)
        mock_db_action.side_effect = DataValidationError('Payments not found for the user_id: {}'.format(user_id))
        resp = self.app.patch('payments/{}/set-default'.format(user_id),data=data, content_type='application/json')
        mock_db_action.assert_called_once_with(user_id, payment_attributes=payment_data)
        self.assertRaises(DataValidationError)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('error' in resp.data)
        self.assertTrue('Payments not found' in resp.data)

    @mock.patch.object(PaymentService, 'perform_payment_action', return_value=True)
    def test_set_default_action_success(self, mock_db_action):
        user_id = payment_id = 1
        payment_data = {'payment_id': payment_id}
        data = json.dumps(payment_data)
        resp = self.app.patch('payments/{}/set-default'.format(user_id),data=data, content_type='application/json')
        mock_db_action.assert_called_once_with(user_id, payment_attributes=payment_data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue('success' in resp.data)

    @mock.patch.object(PaymentService, 'perform_payment_action', return_value=False)
    def test_set_default_action_with_no_default_payment(self, mock_db_action):
        user_id = payment_id = 1
        payment_data = {'payment_id': payment_id}
        data = json.dumps(payment_data)
        resp = self.app.patch('payments/{}/set-default'.format(user_id),data=data, content_type='application/json')
        mock_db_action.assert_called_once_with(user_id, payment_attributes=payment_data)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue('No Payment' in resp.data)

    @mock.patch.object(PaymentService, 'perform_payment_action')
    def test_set_default_action_with_no_request_data(self, mock_db_action):
        user_id = 1
        resp = self.app.patch('payments/{}/set-default'.format(user_id),data=None, content_type='application/json')
        mock_db_action.assert_not_called()
        self.assertRaises(DataValidationError)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('no data' in resp.data)

    @mock.patch.object(PaymentService, 'perform_payment_action')
    def test_set_default_action_with_text_request_data(self, mock_db_action):
        user_id = payment_id = 1
        payment_data = "payment_id"
        resp = self.app.patch('payments/{}/set-default'.format(user_id),data=payment_data, content_type='text/plain')
        mock_db_action.assert_not_called()
        self.assertRaises(DataValidationError)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('not json' in resp.data)

    @mock.patch.object(PaymentService, 'perform_payment_action')
    def test_set_default_action_with_wrong_request_data(self, mock_db_action):
        user_id = payment_id = 1
        payment_data = {'random_id': payment_id}
        data = json.dumps(payment_data)
        resp = self.app.patch('payments/{}/set-default'.format(user_id),data=data, content_type='application/json')
        mock_db_action.assert_not_called()
        self.assertRaises(KeyError)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('does not have the payment_id' in resp.data)

    #Tests for action - charge
    @mock.patch.object(PaymentService, 'perform_payment_action')
    def test_charge_action_with_no_payments_for_user_id(self, mock_db_action):
        user_id = 1
        amount_data = {'amount' : 25.0 }
        data = json.dumps(amount_data)
        mock_db_action.side_effect = DataValidationError('Payments not found for the user_id: {}'.format(user_id))
        resp = self.app.patch('payments/{}/charge'.format(user_id),data=data, content_type='application/json')
        mock_db_action.assert_called_once_with(user_id, payment_attributes=amount_data)
        self.assertRaises(DataValidationError)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('error' in resp.data)
        self.assertTrue('Payments not found' in resp.data)

    @mock.patch.object(PaymentService, 'perform_payment_action')
    def test_charge_action_with_no_request_data(self, mock_db_action):
        user_id = 1
        resp = self.app.patch('payments/{}/charge'.format(user_id),data=None, content_type='application/json')
        mock_db_action.assert_not_called()
        self.assertRaises(DataValidationError)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('no data' in resp.data)

    @mock.patch.object(PaymentService, 'perform_payment_action')
    def test_charge_action_with_text_request_data(self, mock_db_action):
        user_id = 1
        amount_data = "payment_id"
        resp = self.app.patch('payments/{}/charge'.format(user_id),data=amount_data, content_type='text/plain')
        mock_db_action.assert_not_called()
        self.assertRaises(DataValidationError)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('not json' in resp.data)

    @mock.patch.object(PaymentService, 'perform_payment_action')
    def test_charge_action_with_wrong_request_data(self, mock_db_action):
        user_id = 1
        amount_data = {'charge-amount' : 25.0 }
        data = json.dumps(amount_data)
        resp = self.app.patch('payments/{}/charge'.format(user_id),data=data, content_type='application/json')
        mock_db_action.assert_not_called()
        self.assertRaises(KeyError)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('does not have the amount' in resp.data)

    @mock.patch.object(PaymentService, 'perform_payment_action')
    def test_charge_action_with_negative_amount(self, mock_db_action):
        user_id = 1
        amount_data = {'amount' : -25.0 }
        data = json.dumps(amount_data)
        resp = self.app.patch('payments/{}/charge'.format(user_id),data=data, content_type='application/json')
        mock_db_action.assert_not_called()
        self.assertRaises(DataValidationError)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('Order amount is negative.' in resp.data)

    @mock.patch.object(PaymentService, 'perform_payment_action', return_value=True)
    def test_charge_action_success(self, mock_db_action):
        user_id = 1
        amount_data = {'amount' : 25.0 }
        data = json.dumps(amount_data)
        resp = self.app.patch('payments/{}/charge'.format(user_id),data=data, content_type='application/json')
        mock_db_action.assert_called_once_with(user_id, payment_attributes=amount_data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue('success' in resp.data)

    @mock.patch.object(PaymentService, 'perform_payment_action')
    def test_charge_action_with_no_default_payment_for_user(self, mock_db_action):
        user_id = 1
        amount_data = {'amount' : 25.0 }
        data = json.dumps(amount_data)
        mock_db_action.side_effect = DataValidationError('Invalid request: Default Payment for this user_id: {} not found. Please update the default_payment first.'.format(user_id))
        resp = self.app.patch('payments/{}/charge'.format(user_id),data=data, content_type='application/json')
        mock_db_action.assert_called_once_with(user_id, payment_attributes=amount_data)
        self.assertRaises(DataValidationError)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('error' in resp.data)
        self.assertTrue('Invalid request: Default Payment' in resp.data)

    @mock.patch.object(PaymentService, 'perform_payment_action')
    def test_charge_action_with_default_payment_card_expired(self, mock_db_action):
        user_id = 1
        amount_data = {'amount' : 25.0 }
        data = json.dumps(amount_data)
        mock_db_action.side_effect = DataValidationError('Invalid request: Default Payment for this user_id: {} (credit) is expired'.format(user_id))
        resp = self.app.patch('payments/{}/charge'.format(user_id),data=data, content_type='application/json')
        mock_db_action.assert_called_once_with(user_id, payment_attributes=amount_data)
        self.assertRaises(DataValidationError)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('error' in resp.data)
        self.assertTrue('expired' in resp.data)

    @mock.patch.object(PaymentService, 'perform_payment_action')
    def test_charge_action_with_no_default_payment_paypal_not_linked(self, mock_db_action):
        user_id = 1
        amount_data = {'amount' : 25.0 }
        data = json.dumps(amount_data)
        mock_db_action.side_effect = DataValidationError('Invalid request: Default Payment for this user_id: {} (Paypal) is not linked'.format(user_id))
        resp = self.app.patch('payments/{}/charge'.format(user_id),data=data, content_type='application/json')
        mock_db_action.assert_called_once_with(user_id, payment_attributes=amount_data)
        self.assertRaises(DataValidationError)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('error' in resp.data)
        self.assertTrue('not linked' in resp.data)

    def test_index(self):
        resp = self.app.get('/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue('Payments REST API Service' in resp.data)
#test cases for update payments - put and patch
# passing correct data to put
    @mock.patch.object(PaymentService, 'update_payment', return_value=PUT_CREDIT_RETURN)
    def test_crud_update_put(self,mock_ps_update):
        data = json.dumps(PUT_CREDIT)
        resp = self.app.put('/payments/1', data=data, content_type='application/json')
        mock_ps_update.assert_called_with(1,payment_replacement=PUT_CREDIT)
        self.assertEqual( resp.status_code, status.HTTP_200_OK )
        new_json = json.loads(resp.data)
        self.assertEqual (new_json['nickname'], 'favcredit')

# passing correct data to patch
    @mock.patch.object(PaymentService, 'update_payment', return_value=PATCH_RETURN)
    def test_crud_update_patch(self,mock_ps_update):
        data = json.dumps(PATCH_CREDIT)
        resp = self.app.patch('/payments/1', data=data, content_type='application/json')
        mock_ps_update.assert_called_with(1,payment_attributes=PATCH_CREDIT)
        self.assertEqual( resp.status_code, status.HTTP_200_OK )
        new_json = json.loads(resp.data)
        self.assertEqual (new_json['nickname'], 'boringcredit')

# passing text data to put
    def test_crud_update_put_with_text_data(self):
        resp = self.app.put('/payments/1', data="hello", content_type='text/plain')
        self.assertEqual( resp.status_code, status.HTTP_400_BAD_REQUEST )
        self.assertTrue('not json' in resp.data)

# passing text data to patch
    def test_crud_update_patch_with_text_data(self):
        resp = self.app.patch('/payments/1', data="hello", content_type='text/plain')
        self.assertEqual( resp.status_code, status.HTTP_400_BAD_REQUEST )
        self.assertTrue('not json' in resp.data)

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
#@mock.patch.object(PaymentService, 'update_payment',side_effect=DataValidationError)
    def test_crud_update_put_garbage(self):
        garbage = "a@$*&@#sdassdc3r 3284723X43&^@!#@*#"
        resp = self.app.put('/payments/1',data = garbage, content_type='application/json')
        self.assertTrue('bad or no data' in resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

# passing garbage data to patch
    def test_crud_update_patch_garbage(self):
        garbage = "a@$*&@#sdassdc3r 3284723X43&^@!#@*#"
        resp = self.app.patch('/payments/1',data = garbage, content_type='application/json')
        self.assertTrue('bad or no data' in resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

# passing a non existing payment id to PATCH
    @mock.patch.object(PaymentService, 'update_payment', side_effect=PaymentNotFoundError('Invalid payment: Payment ID not found'))
    def test_crud_update_id_not_found_patch(self,mock_ps_update):
        credit = json.dumps({'nickname' : 'mycredit'})
        resp = self.app.patch('payments/778',data = credit,content_type='application/json')
        mock_ps_update.assert_called_with(778,payment_attributes={'nickname' : 'mycredit'})
        self.assertTrue('Invalid payment: Payment ID not found' in resp.data)
        self.assertTrue(resp.status_code, status.HTTP_404_NOT_FOUND)
# passing a non existing payment id to PUT
    @mock.patch.object(PaymentService, 'update_payment', side_effect=PaymentNotFoundError('Invalid payment: Payment ID not found'))
    def test_crud_update_id_not_found_put(self,mock_ps_update):
        credit = json.dumps(CC_RETURN)
        resp = self.app.put('payments/778',data = credit,content_type='application/json')
        mock_ps_update.assert_called_with(778,payment_replacement=CC_RETURN)
        self.assertTrue('Invalid payment: Payment ID not found' in resp.data)
        self.assertTrue(resp.status_code, status.HTTP_404_NOT_FOUND)
