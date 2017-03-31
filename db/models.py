from db import db
# db will be our connect to SQLAlchemy ORM

######################################################################
# Custom Exceptions
######################################################################
class DataValidationError(ValueError):
    pass

######################################################################
# Models
######################################################################

class Payment(db.Model):
    __tablename__ = 'payment'
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(20))
    user_id = db.Column(db.Integer)
    payment_type = db.Column(db.String(10))
    is_default = db.Column(db.Boolean)
    is_removed = db.Column(db.Boolean)
    charge_history = db.Column(db.Float)

    detail_id = db.Column(db.Integer, db.ForeignKey('detail.id'))
    details = db.relationship('Detail',
        backref=db.backref('payment', lazy='joined'))

    def self_url(self):
        return url_for('get_payments', id=self.id, _external=True)

    def serialize(self):
        return {
                    'payment_id' : self.payment_id,
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
            self.is_default = False
            self.is_removed = False
            self.charge_history = 0.0
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
        #return self

class Detail(db.Model):
    __tablename__ = 'detail'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50))
    expires = db.Column(db.String(7))
    card_type = db.Column(db.String(10))
    card_number = db.Column(db.String(16))
    user_email = db.Column(db.String(50))
    is_linked = db.Column(db.Boolean)

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
