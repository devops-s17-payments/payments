from behave import given, when, then
from flask_api import status
from app.db.interface import PaymentService
import json

@given(u'the following payments')
def step_impl(context):
	for row in context.table:

		details = {
			'user_name' : row['user_name'],
			'user_email' : row['user_email'],
			'is_linked' : row['is_linked'],
			'card_number' : row['card_number'],
			'card_type' : row['card_type'],
			'expires' : row['expires'],
		}
		public_data = {
			'nickname' : row['nickname'],
			'user_id' : row['user_id'],
			'payment_type' : row['payment_type'],
			'details' : details
		}
		private_data = {
			'is_default' : row['is_default'],
			'is_removed' : row['is_removed'],
			'charge_history' : row['charge_history'],
		}
		PaymentService.load_sample(public_data, private_data)

@given(u'a new credit card')
def step_impl(context):
	for row in context.table:
		details = {
			'user_name' : row['user_name'],
			'card_number' : row['card_number'],
			'card_type' : row['card_type'],
			'expires' : row['expires'],
		}
		payment = {
			'nickname' : row['nickname'],
			'user_id' : row['user_id'],
			'payment_type' : row['payment_type'],
			'details' : details
		}
	context.resp.data = json.dumps(payment)


@when(u'I visit the "home page"')
def step_impl(context):
    context.resp = context.app.get('/')
    assert context.resp.status_code == status.HTTP_200_OK

@when(u'I visit "{url}"')
def step_impl(context, url):
    context.resp = context.app.get(url)
    assert context.resp.status_code == status.HTTP_200_OK

@when(u'I add a new payment to "{url}"')
def step_impl(context, url):
	context.resp = context.app.post(url, data=context.resp.data, content_type='application/json')
	assert context.resp.status_code == status.HTTP_201_CREATED

@then(u'I should see "{message}"')
def step_impl(context, message):
    assert message in context.resp.data

'''

### haven't gotten this one working yet

@then(u'I should see "{count}" existing payments')
def step_impl(context, count):
    #assert (int(count) == len(json.loads(context.resp.data)))
    assert (int(count) == len(context.resp.data))

'''

@then(u'I should not see "{message}"')
def step_impl(context, message):
    assert message not in context.resp.data