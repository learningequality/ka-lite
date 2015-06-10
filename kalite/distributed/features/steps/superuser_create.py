from behave import *
from selenium import webdriver
from kalite.testing.behave_helpers import *
from django.contrib.auth.models import User

modal_container = "superusercreate-container"

@given("there is superuser")
def step_impl(context):
    if User.objects.exists():
        pass
    else:
        User.objects.create_superuser(username='superusername', password='superpassword', email='super@email.com')
    assert User.objects.exists(), "superuser not crerated successfully!"

@then("there should be no modal displayed")
def step_impl(context):
    assert not find_id_with_wait(context, modal_container), "modal found!"

@given("there is no superuser")
def step_impl(context):
    if User.objects.exists():
        User.objects.all().delete()
    assert not User.objects.exists(), "superuser not deleted successfully!"

@then("I should see a modal")
def step_impl(context):
    assert find_id_with_wait(context, modal_container).is_displayed(), "modal not displayed!"

@given("the username is empty")
def step_impl(context):
    fill_username(context, "")

@when('I click the create button')
def step_impl(context):
    create_button = find_css_class_with_wait(context, "create-btn")
    create_button.click()

@then('the username border will turn red')
def impl(context):
    is_border_red(context, "id_superusername")

@given("I enter a username longer than 40 letters")
def step_impl(context):
    fill_username(context, "x" * 41)

@then("the modal won't dismiss")
def step_impl(context):
    assert find_id_with_wait(context, modal_container).is_displayed(), "modal dismissed!"

@given("the password is empty")
def step_impl(context):
    fill_password(context, "")

@then('the password border will turn red')
def impl(context):
    is_border_red(context, "id_superpassword")

@given("I enter a password longer than 40 letters")
def step_impl(context):
    fill_password(context, "x" * 41)

@given("I enter my email address incorrectly")
def step_impl(context):
    fill_email(context, "incorrect")

@then("the email border will turn red")
def impl(context):
    is_border_red(context, "id_superemail")

@given("I enter a email address longer than 40 letters")
def step_impl(context):
    fill_email(context, "x" * 41 + "@toolong.com")

@given("I enter username correctly")
def step_impl(context):
    fill_username(context, "correct_name")

@given("I enter password correctly")
def step_impl(context):
    fill_password(context, "correct_password")

@given("I enter email correctly")
def step_impl(context):
    fill_email(context, "correct@email.com")

@then("the modal will dismiss")
def impl(context):
    assert not find_id_with_wait(context, modal_container).is_displayed(), "modal not dismissed!"

@then("a superuser is created")
def impl(context):
    assert WebDriverWait(context.browser, 3).until(User.objects.exists()), "superuser not crerated successfully!"


def fill_field(context, text, field_id):
    assert find_id_with_wait(context, field_id), "field is None!"
    field = find_id_with_wait(context, field_id)
    field.clear()
    field.send_keys(text)

def fill_username(context, text):
    fill_field(context, text, "id_superusername")

def fill_password(context, text):
    fill_field(context, text, "id_superpassword")

def fill_email(context, text):
    fill_field(context, text, "id_superemail")

def is_border_red(context, field_id):
    assert find_id_with_wait(context, field_id), "border field is None!"
    border = find_id_with_wait(context, field_id)
    border_color = border.value_of_css_property('border-color')
    print ('border_color: ', border_color)
    assert border_color == 'rgb(169, 68, 66)', "border not red!"
