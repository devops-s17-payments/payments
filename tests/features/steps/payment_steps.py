from behave import given, when, then
from flask_api import status
from app.db.interface import PaymentService
from app import payments
import json


#############
# G I V E N #
#############

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
    context.data = json.dumps(payment)

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
    context.data = json.dumps(payment)

@given('an updated credit card with illegal data')
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
            'is_removed' : row['is_removed'],
            'details' : details
        }
    context.data = json.dumps(payment)

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

@when('I retrieve "{url}" with non-existent id "{id}"')
def step_impl(context, url, id):
    target = url + '/' + id
    context.resp = context.app.get(target)
    assert context.resp.status_code == status.HTTP_404_NOT_FOUND

@when('I query "{url}" with "{attribute1}" = "{value1}" and "{attribute2}" = "{value2}"')
def step_impl(context, url, attribute1,value1,attribute2,value2):
    query_string = '{}={}&{}={}'.format(attribute1, value1, attribute2,value2)
    target = url + '?'+ query_string
    context.resp = context.app.get(target)
    assert context.resp.status_code == status.HTTP_200_OK

@when('I query "{url}" with bad query inputs "{attribute1}" = "{value1}" and "{attribute2}" = "{value2}"')
def step_impl(context, url, attribute1,value1,attribute2,value2):
    query_string = '{}={}&{}={}'.format(attribute1, value1, attribute2,value2)
    target = url + '?'+ query_string
    context.resp = context.app.get(target)
    assert context.resp.status_code == status.HTTP_404_NOT_FOUND

@when('I visit the "home page"')
def step_impl(context):
    context.resp = context.app.get('/')

@when(u'I add a new payment to "{url}"')
def step_impl(context, url):
    context.resp = context.app.post(url, data=context.data, content_type='application/json')
    assert context.resp.status_code == status.HTTP_201_CREATED

@when('I change "{attribute}" to "{value}"')
def step_impl(context, attribute, value):
    context.data = json.dumps({attribute : value})

@when('I change "{attribute}" to "{value}", but misspell the attribute')
def step_impl(context, attribute, value):
    context.data = json.dumps({attribute : value})

@when('I patch "{url}" with id "{id}"')
def step_impl(context, url, id):
    target = url + '/' + id
    context.resp = context.app.patch(target, data=context.data, content_type='application/json')
    assert context.resp.status_code == status.HTTP_200_OK

@when('I patch "{url}" with id "{id}" with bad data')
def step_impl(context, url, id):
    target = url + '/' + id
    context.resp = context.app.patch(target, data=context.data, content_type='application/json')
    assert context.resp.status_code == status.HTTP_400_BAD_REQUEST

@when('I patch "{url}" with id "{id}" with no data')
def step_impl(context, url, id):
    target = url + '/' + id
    context.resp = context.app.patch(target, data=None, content_type='application/json')
    assert context.resp.status_code == status.HTTP_400_BAD_REQUEST

@when('I put "{url}" with id "{id}"')
def step_impl(context, url, id):
    target = url + '/' + id
    data = json.loads(context.data)
    assert data['user_id'] == id
    context.resp = context.app.put(target, data=context.data, content_type='application/json')
    assert context.resp.status_code == status.HTTP_200_OK

@when('I put "{url}" with id "{id}" with illegal data')
def step_impl(context, url, id):
    target = url + '/' + id
    data = json.loads(context.data)
    assert data['user_id'] == id
    context.resp = context.app.put(target, data=context.data, content_type='application/json')
    assert context.resp.status_code == status.HTTP_400_BAD_REQUEST

@when('user with id "{id}" has existing "{url}"')
def step_impl(context, id, url):
    target = url + '?user_id=' + id
    context.resp = context.app.get(target)
    assert context.resp.status_code == status.HTTP_200_OK
    assert len(context.resp.data) > 0

@when('user with id "{u_id}" performs "{action}" on "{url}" with id "{p_id}"')
def step_impl(context, u_id, action, url, p_id):
    target = url + '/' + u_id + '/' + action
    data = json.dumps({'payment_id' : int(p_id)})
    context.resp = context.app.patch(target, data=data, content_type='application/json')
    assert context.resp.status_code == status.HTTP_200_OK
    assert 'Payment with id: 1 set as default' in context.resp.data

@when('I try to delete payment {id}')
def step_impl(context, id):
    url = '/payments/{}'.format(id)
    context.resp = context.app.delete(url)
    assert context.resp.status_code == status.HTTP_204_NO_CONTENT

@when('I attempt to retrieve the deleted payment {id}')
def step_impl(context, id):
    url = '/payments/{}'.format(id)
    context.resp = context.app.get(url)


@when('I try to delete a non-existent payment with id {id}')
def step_impl(context, id):
    url = '/payments/{}'.format(id)
    context.resp = context.app.delete(url)

@when('I query payments with a valid query "{attribute}" = "{value}"')
def step_impl(context, attribute, value):
    url = '/payments?{}={}'.format(attribute,value)
    context.resp = context.app.get(url)
    assert context.resp.status_code == status.HTTP_200_OK

@when('I query payments with a bad query "{attribute}" = "{value}"')
def step_impl(context, attribute, value):
    url = '/payments?{}={}'.format(attribute,value)
    context.resp = context.app.get(url)
    assert context.resp.status_code == status.HTTP_404_NOT_FOUND

@when('I list all "{url}"')
def step_impl(context, url):
    context.resp = context.app.get(url)
    assert context.resp.status_code == status.HTTP_200_OK

@when('I list all "{url}" when no payments exist')
def step_impl(context, url):
    context.resp = context.app.get(url)

@when('user with id "{id}" chooses to buy something for ${dollars}')
def step_impl(context, id, dollars):
    url = '/payments/{}/charge'.format(id)
    data = json.dumps({'amount': float(dollars)})
    context.resp = context.app.patch(url, data=data, content_type='application/json')

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

@then('user with id "{u_id}" should see payment with id "{p_id}" set as default')
def step_impl(context, u_id, p_id):
    payments = json.loads(context.resp.data)
    assert payments[0]['is_default'] == True
    assert payments[0]['payment_id'] == int(p_id)
    assert payments[0]['user_id'] == int(u_id)

@then('I should be returned nothing for payment {id}')
def step_impl(context, id):
    assert context.resp.status_code == status.HTTP_204_NO_CONTENT
    assert context.resp.data == ''

@then('the server should tell me payment {id} was not found')
def step_impl(context, id):
    expected_response = payments.NOT_FOUND_ERROR_BODY
    expected_response['error'] = expected_response['error'].format(id)
    actual_response = json.loads(context.resp.data)
    assert context.resp.status_code == status.HTTP_404_NOT_FOUND
    assert actual_response == expected_response

@then('user with id "{id}" should be notified of the charge for ${dollars}')
def step_impl(context, id, dollars):
    expected_response = {
        'success': 'Default payment method for user_id: %s has been charged $%.2f' % ((id), float(dollars))}
    actual_response = json.loads(context.resp.data)
    assert context.resp.status_code == status.HTTP_200_OK
    assert actual_response == expected_response

@then(u'I should see "{count}" existing payments')
def step_impl(context, count):
    assert len(json.loads(context.resp.data)) == int(count)
    assert context.resp.status_code == 200

@then('I should see an error message saying "{error_msg}"')
def step_impl(context,error_msg):
    assert error_msg in json.loads(context.resp.data)['error']

@then('I should see payment "{index}" with id "{id}" and "{attribute}" = "{value}"')
def step_impl(context,index, id, attribute, value):
    payments = json.loads(context.resp.data)
    assert payments[int(index)-1][attribute] == value
    assert payments[int(index)-1]['payment_id'] == int(id)

@then('I should see a payment with "{attribute1}" = "{value1}" and "{attribute2}" = "{value2}"')
def step_impl(context,attribute1, value1,attribute2,value2):
    payments = json.loads(context.resp.data)
    assert payments[0][attribute1] == value1
    assert payments[0][attribute2] == value2
