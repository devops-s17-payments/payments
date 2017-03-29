import unittest, json
import payments, models
from flask_api import status    # HTTP Status Codes

class TestModels(unittest.TestCase):

    def setUp(self):
        payments.app.debug = True
        payments.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/test.db'
        payments.db.drop_all()    # clean up the last tests
        payments.db.create_all()  # make our sqlalchemy tables
        
        data = {'nickname' : 'my credit', 'user_id' : 1, 'payment_type' : 'credit', 
        'details' : {'user_name' : 'Jimmy Jones', 'card_number' : '1111222233334444',
        'expires' : '01/2019', 'card_type' : 'Mastercard'}}

        payment = models.Payment()
        payment.deserialize(data)
        payments.db.session.add(payment)
        payments.db.session.commit()
        self.app = payments.app.test_client()

    def tearDown(self):
        payments.db.session.remove()
        payments.db.drop_all()

    def test_credit_has_no_paypal_fields(self):
        payment = payments.db.session.query(models.Payment).get(1)
        detail = payment.details
        print payment
        print detail
        self.assertEqual(payment.nickname, 'my credit')