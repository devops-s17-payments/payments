
from flask import url_for
from app.db import app_db
from app.error_handlers import DataValidationError


######################################################################
# Models
######################################################################

class Payment(app_db.Model):
    __tablename__ = 'payment'
    id = app_db.Column(app_db.Integer, primary_key=True)
    nickname = app_db.Column(app_db.String(20))
    user_id = app_db.Column(app_db.Integer)
    payment_type = app_db.Column(app_db.String(10))
    is_default = app_db.Column(app_db.Boolean)
    is_removed = app_db.Column(app_db.Boolean)
    charge_history = app_db.Column(app_db.Float)

    detail_id = app_db.Column(app_db.Integer, app_db.ForeignKey('detail.id'))
    details = app_db.relationship('Detail',
        backref=app_db.backref('payment', lazy='joined'))

    def self_url(self):
        return url_for('get_payments', id=self.id, _external=True)

    def serialize(self):
        return {
                    'payment_id' : self.id,
                    'user_id' : self.user_id,
                    'nickname' : self.nickname,
                    'payment_type' : self.payment_type,
                    'is_default' : self.is_default,
                    'charge_history' : self.charge_history,
                    'details' : self.details.serialize()
                }

    def deserialize(self, data):
        try:
            self.user_id = data['user_id']
            self.nickname = data['nickname']
            self.payment_type = data['payment_type']
            self.is_default = False if 'is_default' not in data else data['is_default']
            self.is_removed = False
            self.charge_history = 0.0 if 'charge_history' not in data else data['charge_history']
            details = data['details']
            
            d = Detail()
            if (self.payment_type == 'credit' or self.payment_type == 'debit'):
                d.deserialize_card(details)
            else:
                d.deserialize_paypal(details)
            self.details = d
        except KeyError as e:
            raise DataValidationError('Invalid payment: missing ' + e.args[0])
        except TypeError as e:
            raise DataValidationError('Invalid payment: body of request contained bad or no data')

class Detail(app_db.Model):
    __tablename__ = 'detail'
    id = app_db.Column(app_db.Integer, primary_key=True)
    user_name = app_db.Column(app_db.String(50))
    expires = app_db.Column(app_db.String(7))
    card_type = app_db.Column(app_db.String(10))
    card_number = app_db.Column(app_db.String(16))
    user_email = app_db.Column(app_db.String(50))
    is_linked = app_db.Column(app_db.Boolean)

    def serialize(self):
        if self.is_linked is None:  #is_linked is paypal attribute
            result = {
                        'user_name' : self.user_name,
                        'card_type' : self.card_type,
                        'card_number' : self.card_number,
                        'expires' : self.expires
                     }
        else:
            result = {
                        'user_name' : self.user_name,
                        'user_email' : self.user_email,
                        'is_linked' : self.is_linked
                     }
        return result


    def deserialize_card(self, details):
        try:
            self.user_name = details['user_name']
            self.card_type = details['card_type']
            self.card_number = details['card_number']
            self.expires = details['expires']
        except KeyError as e:
            raise DataValidationError('Invalid payment: missing ' + e.args[0])
        except TypeError as e:
            raise DataValidationError('Invalid payment: body of request contained bad or no data')

    def deserialize_paypal(self, details):
        try:
            self.user_name = details['user_name']
            self.user_email = details['user_email']
            self.is_linked = True
        except KeyError as e:
            raise DataValidationError('Invalid payment: missing ' + e.args[0])
        except TypeError as e:
            raise DataValidationError('Invalid payment: body of request contained bad or no data')
