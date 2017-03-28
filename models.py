from payments import db

class BasePayment(db.Model):
    __metaclass__ = ABCMeta
    __tablename__ = 'payments'
    payment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    is_default = db.Column(db.Boolean)
    is_removed = db.Column(db.Boolean)
    charge_history = db.Column(db.Float)

    def self_url(self):
        return url_for('get_pets', id=self.id, _external=True)

    @abstractmethod
    def serialize(self):
        pass

    @abstractmethod
    def deserialize(self, data):
        pass

class CreditPayment(BasePayment):
    payment_type = db.Column(db.String(10))
    user_name = db.Column(db.String(50))
    expires = db.Column(db.DateTime)
    card_type = db.Column(db.String(10))
    card_number = db.Column(db.String(16))

    def serialize(self):
        pass

    def deserialize(self, data):
        pass

class DebitPayment(BasePayment):
    payment_type = db.Column(db.String(10))
    user_name = db.Column(db.String(50))
    expires = db.Column(db.DateTime)
    card_type = db.Column(db.String(10))
    card_number = db.Column(db.String(16))

    def serialize(self):
        pass
        
    def deserialize(self, data):
        pass

class PaypalPayment(BasePayemnt):
    payment_type = db.Column(db.String(10))
    user_name = db.Column(db.String(50))
    user_email = db.Column(db.String(50))
    is_linked = db.Column(db.Boolean)
