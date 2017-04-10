from behave import given, when, then
import json

@when('I visit the "home page"')
def step_impl(context):
    context.resp = context.app.get('/')

@then('I should see "{message}"')
def step_impl(context, message):
    assert message in context.resp.data

@then('I should not see "{message}"')
def step_impl(context, message):
    assert message not in context.resp.data