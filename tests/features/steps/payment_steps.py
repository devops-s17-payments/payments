from behave import given, when, then
from flask_api import status
from app.db.interface import PaymentService
import json

#############
# G I V E N #
#############

@given('the following "{url}"')
def step_impl(context, url):
    ''' need this blank post otherwise first live post goes to dev instead of test db '''
    context.app.post(url, data=None, content_type='application/json')
    for row in context.table:
        details = {
            'user_name' : row['user_name'],
            'user_email' : row['user_email'],
            'is_linked' : row['is_linked'],
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

        context.app.post(url, data=json.dumps(payment), content_type='application/json')

@given('a new credit card')
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

@given('an updated credit card')
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

###########
# W H E N #
###########

@when('I visit "{url}"')
def step_impl(context, url):
    context.resp = context.app.get(url)
    assert context.resp.status_code == status.HTTP_200_OK

@when('I get "{url}" with id "{id}"')
def step_impl(context, url, id):
    target = url + '/' + id
    context.resp = context.app.get(target)
    assert context.resp.status_code == status.HTTP_200_OK

@when('I visit the "home page"')
def step_impl(context):
    context.resp = context.app.get('/')

@when(u'I add a new payment to "{url}"')
def step_impl(context, url):
    context.resp = context.app.post(url, data=context.resp.data, content_type='application/json')
    assert context.resp.status_code == status.HTTP_201_CREATED

@when('I change "{attribute}" to "{value}"')
def step_impl(context, attribute, value):
    context.resp.data = json.dumps({attribute : value})

@when('I patch "{url}" with id "{id}"')
def step_impl(context, url, id):
    target = url + '/' + id
    context.resp = context.app.patch(target, data=context.resp.data, content_type='application/json')
    assert context.resp.status_code == status.HTTP_200_OK

@when('I put "{url}" with id "{id}"')
def step_impl(context, url, id):
    target = url + '/' + id
    data = json.loads(context.resp.data)
    assert data['user_id'] == id
    context.resp = context.app.put(target, data=context.resp.data, content_type='application/json')
    assert context.resp.status_code == status.HTTP_200_OK

###########
# T H E N #
###########

@then('I should see "{message}"')
def step_impl(context, message):
    assert message in context.resp.data

@then('I should see a payment with id "{id}" and "{attribute}" = "{value}"')
def step_impl(context, id, attribute, value):
    payments = json.loads(context.resp.data)
    assert payments[0][attribute] == value
    assert payments[0]['payment_id'] == int(id)

@then('I should not see "{message}"')
def step_impl(context, message):
    assert message not in context.resp.data

'''

### haven't gotten this one working yet

@then(u'I should see "{count}" existing payments')
def step_impl(context, count):
    #assert (int(count) == len(json.loads(context.resp.data)))
    assert (int(count) == len(context.resp.data))

'''