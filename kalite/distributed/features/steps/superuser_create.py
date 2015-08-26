from behave import *
from kalite.testing.behave_helpers import *
from django.contrib.auth.models import User

modal_container = "superusercreate-container"

@then("there should be no modal displayed")
def step_impl(context):
    try:
        # TODO(benjaoming): This is a crazy test... waiting for a timeout in
        # order to see that some element doesn't appear!?
        # I've just set the wait_time to 1 second for now
        find_id_with_wait(context, modal_container, wait_time=1)
        assert False, "Should not find a modal container"
    except TimeoutException:
        # All good
        pass

@given("superuser is deleted")
def step_impl(context):
    if User.objects.all().exists():
        User.objects.all().delete()
    assert not User.objects.all().exists(), "superuser not deleted successfully!"

@then("I should see a modal")
def step_impl(context):
    assert find_id_with_wait(context, modal_container, wait_time=120), "modal not displayed!"

@when("the username is empty")
def step_impl(context):
    fill_username(context, "")

@when('I click the create button')
def step_impl(context):
    context.modal_element = find_id_with_wait(context, modal_container)  # Grab a reference for later
    create_button = find_css_class_with_wait(context, "create-btn")
    create_button.click()

@then('the username border will turn red')
def impl(context):
    is_border_red(context, "id_superusername")

@when("I enter a username longer than 40 letters")
def step_impl(context):
    fill_username(context, "x" * 41)

@then("the modal won't dismiss")
def step_impl(context):
    assert not elem_is_invisible_with_wait(context, context.modal_element), "modal dismissed!"

@when("the password is empty")
def step_impl(context):
    fill_password(context, "")

@then('the password border will turn red')
def impl(context):
    is_border_red(context, "id_superpassword")

@when("I enter a password longer than 40 letters")
def step_impl(context):
    fill_password(context, "x" * 41)

@when("I enter an unmatched password")
def step_impl(context):
    reenter_password(context, "unmatched")

@then("the confirmsuperpassword border will turn red")
def impl(context):
    is_border_red(context, "id_confirmsuperpassword")

@when("I enter username correctly")
def step_impl(context):
    fill_username(context, "correct_name")

@when("I enter password correctly")
def step_impl(context):
    fill_password(context, "correct_password")

@when("I re-enter password correctly")
def step_impl(context):
    reenter_password(context, "correct_password")

@then("the modal will dismiss")
def impl(context):
    assert elem_is_invisible_with_wait(context, context.modal_element, wait_time=60), "modal not dismissed!"

def fill_field(context, text, field_id):
    field = find_id_with_wait(context, field_id, wait_time=180)
    field.clear()
    field.send_keys(text)

def fill_username(context, text):
    fill_field(context, text, "id_superusername")

def fill_password(context, text):
    fill_field(context, text, "id_superpassword")

def reenter_password(context, text):
    fill_field(context, text, "id_confirmsuperpassword")

def is_border_red(context, field_id):
    assert find_id_with_wait(context, field_id), "border field is None!"
    border = find_id_with_wait(context, field_id)
    border_color = border.value_of_css_property('border-color')
    assert border_color == 'rgb(169, 68, 66)', "border not red!"