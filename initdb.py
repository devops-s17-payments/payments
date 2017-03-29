from payments import db
from models import *

db.drop_all()
db.create_all()

data = {'nickname' : 'my credit', 'user_id' : 1, 'payment_type' : 'credit', 
		'details' : {'user_name' : 'Jimmy Jones', 'card_number' : '1111222233334444',
		'expires' : '01/2019', 'card_type' : 'Mastercard'}}

#details = Detail()
#details.deserialize(data['detail'])
payment = Payment()
payment.deserialize(data)
db.session.add(payment)
db.session.commit()

obj = Payment.query.get(1)
print obj.nickname
print obj.user_id
print obj.details.card_type
mypayment = db.session.query(Payment).get(1)
mydetail = mypayment.details

print mypayment
print mydetail
