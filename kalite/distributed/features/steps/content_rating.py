from behave import *
from kalite.testing.behave_helpers import *

from kalite.topic_tools import get_content_cache

RATING_CONTAINER_ID = "rating-container"
TEXT_CONTAINER_ID = "text-container"

@then(u'my feedback is displayed')
def impl(context):
    actual = get_text_feedback(context)
    expected = context.text_feedback
    assert actual == expected, "Expected:\n\t '{expected}'\n but saw\n\t '{actual}'\n in feedback form".format(
        expected=expected, actual=actual)

@then(u'I see a feedback form')
def impl(context):
    feedback_form_container = find_id_with_wait(context, RATING_CONTAINER_ID)
    assert elem_is_visible_with_wait(context, feedback_form_container), "Rating form is not visible."

@given(u'some user feedback exists')
def impl(context):
    assert False

@then(u'the user feedback is present')
def impl(context):
    assert False

@then(u'I see a blank form')
def impl(context):
    assert False

@when(u'I edit my feedback')
def impl(context):
    assert False

@when(u'I fill out the form')
def impl(context):
    text_feedback = context.text_feedback = "This stuff is great, A+++"
    enter_text_feedback(context, text_feedback)
    submit_feedback(context)

@given(u'I am on a content page')
def impl(context):
    go_to_content_item(context)

@given(u'I have filled out a feedback form')
def impl(context):
    assert False

@then(u'I see an edit button')
def impl(context):
    assert False

@then(u'I see a delete button')
def impl(context):
    assert False

@when(u'I delete my feedback')
def impl(context):
    assert False

@when(u'I export csv data')
def impl(context):
    assert False

@then(u'my edited feedback is displayed')
def impl(context):
    assert False


def enter_text_feedback(context, text_feedback):
    """
    Enter text feedback into feedback form
    :param context: behave context
    :param text_feedback: str, the feedback to be entered
    :return: nothing
    """
    text_container = find_id_with_wait(context, TEXT_CONTAINER_ID)
    input_field = text_container.find_element_by_class_name("rating-text-feedback")
    input_field.send_keys(text_feedback)


def submit_feedback(context):
    """
    Submit feedback form
    :param context: behave context
    :return: nothing
    """
    pass


def get_text_feedback(context):
    """
    Get the text feedback displayed after the feedback form is filled out
    :param context: behave context
    :return: a str with the text feedback displayed.
    """
    return "abc123"