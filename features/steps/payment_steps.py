from behave import given, when, then
from flask_api import status
import json

@when(u'I visit the "home page"')
def step_impl(context):
    context.resp = context.app.get('/')
    assert context.resp.status_code == status.HTTP_200_OK

@when(u'I visit "{url}"')
def step_impl(context, url):
    context.resp = context.app.get(url)
    assert context.resp.status_code == status.HTTP_200_OK

@then(u'I should see "{message}"')
def step_impl(context, message):
    assert message in context.resp.data

@then(u'I should not see "{message}"')
def step_impl(context, message):
    assert message not in context.resp.data