# Test cases can be run with either of the following:
# python -m unittest discover
# nosetests -v --rednose --nologcapture

import unittest
from mock import patch
import json

from app import payments
from app.db.interface import PaymentService

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
            self.assertEqual(response.status_code, payments.HTTP_200_OK)
            self.assertEqual(json.loads(response.data), SAMPLE_PAYMENT)

    def test_get_payments_not_found(self):
        # something goes wrong with the GET request and the resource cannot be found
        id = 0
        with patch.object(PaymentService, 'get_payments', side_effect=Exception) as mocked_service:
            error_response = payments.NOT_FOUND_ERROR_BODY
            error_response['error'].format(id)
            response = self.app.get('/payments/{}'.format(id))

            self.assertEqual(response.status_code, payments.HTTP_404_NOT_FOUND)
            self.assertEqual(json.loads(response.data), error_response)

    def test_list_payments_all(self):
        # ensure that all payments are returned
        with patch.object(PaymentService, 'get_payments', return_value=SAMPLE_PAYMENTS) as mocked_service:
            response = self.app.get('/payments')

            mocked_service.assert_called_once_with()
            self.assertEqual(response.status_code, payments.HTTP_200_OK)
            self.assertEqual(json.loads(response.data), SAMPLE_PAYMENTS)

    def test_list_payments_by_ids(self):
        # return payments that have specific ids
        ids = '1,2'
        ids_as_list = ids.split(',')
        payments_to_return = SAMPLE_PAYMENTS[1:3]

        with patch.object(PaymentService, 'get_payments', return_value=payments_to_return) as mocked_service:
            response = self.app.get('/payments?ids={}'.format(ids))

            mocked_service.assert_called_once_with(payment_ids=ids_as_list)
            self.assertEqual(response.status_code, payments.HTTP_200_OK)
            self.assertEqual(json.loads(response.data), payments_to_return)

    def test_list_payments_by_attribute(self):
        # return payments that have a specific attribute
        specific_attribute = 'payment_type'
        specific_attribute_value = 'paypal'
        attribute_params = {'payment_type': ['paypal']}
        paypal_payment = SAMPLE_PAYMENTS[1]

        with patch.object(PaymentService, 'get_payments', return_value=paypal_payment) as mocked_service:
            response = self.app.get('/payments?{}={}'.format(specific_attribute, specific_attribute_value))

            mocked_service.assert_called_once_with(payment_attributes=attribute_params)
            self.assertEqual(response.status_code, payments.HTTP_200_OK)
            self.assertEqual(json.loads(response.data), paypal_payment)

    def test_list_payments_not_found(self):
        # attempt to retrieve payments and catch the exception raised; return 404
        with patch.object(PaymentService, 'get_payments', side_effect=Exception) as mocked_service:
            response = self.app.get('/payments')

            self.assertEqual(response.status_code, payments.HTTP_404_NOT_FOUND)
            self.assertEqual(json.loads(response.data), payments.GENERAL_NOT_FOUND_ERROR)

    def test_list_payments_with_ids_and_other_params(self):
        # test to make sure that the ids parameter takes priority over other parameters
        ids = '1,2'
        ids_as_list = ids.split(',')
        payments_to_return = SAMPLE_PAYMENTS[1:3]
        other_param = 'nickname'
        other_param_value = 'amex'

        with patch.object(PaymentService, 'get_payments', return_value=payments_to_return) as mocked_service:
            query_string = 'ids={}&{}={}'.format(ids, other_param, other_param_value)
            response = self.app.get('/payments?{}'.format(query_string))

            # important - we should call the get_payments method with payment_ids, *not*
            mocked_service.assert_called_once_with(payment_ids=ids_as_list)
            self.assertEqual(response.status_code, payments.HTTP_200_OK)
            self.assertEqual(json.loads(response.data), payments_to_return)
