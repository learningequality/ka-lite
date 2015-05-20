from behave import *
from selenium.common.exceptions import NoSuchElementException

from django.core.urlresolvers import reverse

from kalite.testing.behave_helpers import *

from kalite.testing.mixins.facility_mixins import CreateFacilityMixin, CreateStudentMixin


from django.contrib.auth.models import User

@given("there is superuser")
def step_impl(context):
    if User.objects.exists():
        pass
    else:
        User.objects.create_superuser(username='superusername', password='superpassword', email='super@email.com')

@then("there should be no modal displayed")
def step_impl(context):
    assert not find_id_with_wait(context, "superusercreate-container")

@given("there is no superuser")
def step_impl(context):
    if User.objects.exists():
        User.objects.all().delete()

@then("I should see a modal")
def step_impl(context):
    assert find_id_with_wait(context, "superusercreate-container")

@given("the username is empty")
def step_impl(context):
    fill_username(context, "")

@when('I click the create button')
def impl(context):
    create_button = find_css_class_with_wait(context, "create-btn")
    create_button.click()

@then('the username border will turn red')
def impl(context):
    is_border_red(context, "super_username")

@given("I enter a username longer than 30 letters")
def step_impl(context):
    fill_username(context, "123456789123456789123456789123456789")

@when('I click the create button')
def impl(context):
    create_button = find_css_class_with_wait(context, "create-btn")
    create_button.click()

@then("the modal won't dismiss")
def impl(context):
    assert find_id_with_wait(context, "superusercreate-container")

@given("the password is empty")
def step_impl(context):
    fill_password(context, "")

@when('I click the create button')
def impl(context):
    create_button = find_css_class_with_wait(context, "create-btn")
    create_button.click()

@then('the password border will turn red')
def impl(context):
    is_border_red(context, "super_password")

@given("I enter a password longer than 30 letters")
def step_impl(context):
    fill_password(context, "123456789123456789123456789123456789")

@when('I click the create button')
def impl(context):
    create_button = find_css_class_with_wait(context, "create-btn")
    create_button.click()

@then("the modal won't dismiss")
def impl(context):
    assert find_id_with_wait(context, "superusercreate-container")

@given("I enter my email address incorrectly")
def step_impl(context):
    fill_email(context, "incorrect")

@when('I click the create button')
def impl(context):
    create_button = find_css_class_with_wait(context, "create-btn")
    create_button.click()

@then("the email border will turn red")
def impl(context):
    is_border_red(context, "super_email")

@given("I enter a email address longer than 30 letters")
def step_impl(context):
    fill_email(context, "123456789123456789123456789@toolong.com")

@when('I click the create button')
def impl(context):
    create_button = find_css_class_with_wait(context, "create-btn")
    create_button.click()

@then("the modal won't dismiss")
def impl(context):
    assert find_id_with_wait(context, "superusercreate-container")

@given("I enter everything correctly")
def step_impl(context):
    fill_email(context, "correct@email.com")
    fill_username(context, "correct_name")
    fill_password(context, "correct_password")

@when('I click the create button')
def impl(context):
    create_button = find_css_class_with_wait(context, "create-btn")
    create_button.click()

@then("the modal will dismiss")
def impl(context):
    assert not find_id_with_wait(context, "superusercreate-container")
    assert User.objects.exists()



def fill_field(context, text, field_id):
    field = find_id_with_wait(context, field_id)
    field.send_keys(text)

def fill_username(context, text):
    fill_field(context, text, "super_username")

def fill_password(context, text):
    fill_field(context, text, "super_password")

def fill_email(context, text):
    fill_field(context, text, "super_email")

def is_border_red(context, field_id):
    border = find_id_with_wait(context, field_id)
    border_color = border.value_of_css_property('borderColor')
    assert border_color == 'red'
