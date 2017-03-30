# Test cases can be run with either of the following:
# python -m unittest discover
# nosetests -v --rednose --nologcapture

import unittest, json
import payments, db
from db import db, models
from flask_api import status    # HTTP Status Codes

class TestModels(unittest.TestCase):

    def setUp(self):
        payments.app.debug = True
        payments.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/test.db'
        db.drop_all()    # clean up the last tests
        db.create_all()  # make our sqlalchemy tables
        
        data = {'nickname' : 'my credit', 'user_id' : 1, 'payment_type' : 'credit', 
        'details' : {'user_name' : 'Jimmy Jones', 'card_number' : '1111222233334444',
        'expires' : '01/2019', 'card_type' : 'Mastercard'}}

        payment = models.Payment()
        payment.deserialize(data)
        db.session.add(payment)
        db.session.commit()
        self.app = payments.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_db_has_one_item(self):
        p1 = db.session.query(models.Payment).get(1)
        self.assertNotEqual(p1, None)
        p2 = db.session.query(models.Payment).get(2)
        self.assertEqual(p2, None)

    def test_credit_has_no_paypal_fields(self):
        payment = db.session.query(models.Payment).get(1)
        self.assertEqual(payment.nickname, 'my credit')
        detail = payment.details
        self.assertEqual(detail.is_linked, None)
        self.assertEqual(detail.user_email, None)

