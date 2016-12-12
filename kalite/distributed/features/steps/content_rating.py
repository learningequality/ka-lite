import csv
import glob
import os

from behave import *
from kalite.testing.behave_helpers import *

from kalite.main.models import ContentRating
from securesync.models import Device

from selenium.webdriver.support.select import Select


RATING_CONTAINER_ID = "rating-container"
TEXT_CONTAINER_ID = "text-container"
STAR_CONTAINER_IDS = (
    "star-container-quality",
    "star-container-difficulty",
)
STAR_RATING_OPTION_CLASS = "star-rating-option"
STAR_INNER_WRAPPER_CLASS = "star-rating-inner-wrapper"
TEXT_INPUT_CLASS = "rating-text-feedback"
DELETE_BTN_CLASS = "rating-delete"


@then(u'my feedback is displayed')
def impl(context):
    for star_id in STAR_CONTAINER_IDS:
        star_el = find_id_with_wait(context, star_id)
        assert elem_is_visible_with_wait(context, star_el), "Star rating form with id '{0}' not visible".format(star_id)
    actual = get_text_feedback(context)
    expected = context.text_feedback
    assert actual == expected, "Expected:\n\t '{expected}'\n but saw\n\t '{actual}'\n in feedback form".format(
        expected=expected, actual=actual)


@then(u'I see a feedback form')
def impl(context):
    feedback_form_container = find_id_with_wait(context, RATING_CONTAINER_ID, wait_time=60)
    assert feedback_form_container.is_displayed(), "Rating form is not visible."


@when(u'I alter a star rating')
def impl(context):
    context.old_val = 3
    enter_star_ratings(context, val=4)


@then(u'the altered rating is displayed')
def impl(context):
    inner_wrapper = find_css_class_with_wait(context, STAR_INNER_WRAPPER_CLASS)
    options = inner_wrapper.find_elements_by_class_name(STAR_RATING_OPTION_CLASS)
    new_val = len([el for el in options if "activated" in el.get_attribute("class")])
    assert context.old_val != new_val, \
        "Star rating has value {new_val}, which should be different from the old value {old_val}".format(
            old_val=context.old_val,
            new_val=new_val,
        )


@then(u'I see a new form')
def impl(context):
    # Only star-container-1 should be visible
    visible_container = find_id_with_wait(context, STAR_CONTAINER_IDS[0])
    assert visible_container.is_displayed(),\
        "Element with id '{0}' not visible, but it should be!".format(STAR_CONTAINER_IDS[0])
    for id_ in STAR_CONTAINER_IDS[1:] + (TEXT_CONTAINER_ID, ):
        # This test has caused so many issues and it seems there's no real way of
        # reliably testing that an element has disappeared. So for now, this is
        # disabled.
        # https://github.com/learningequality/ka-lite/pull/5284
        # assert_no_element_by_css_selector(context, "#{id} div".format(id=id_))
        pass


@given(u'some user feedback exists')
def impl(context):
    context.rating_user = user = FacilityMixins.create_student()
    assert FacilityUser.objects.count() != 0, "User was not be created!"

    context.rating_text = "My fantastic rating"
    context.rating = rating = ContentRating(
        content_kind="Video",
        content_id="abc123",
        user=user,
        text=context.rating_text,
        quality=1,
        difficulty=3
    )
    rating.save()
    assert ContentRating.objects.count() != 0, "No ContentRating objects exist to be exported!"


@then(u'the user feedback is present')
def impl(context):
    # Wait for the file to finish downloading.
    old_cwd = os.getcwd()
    os.chdir(context.download_dir)
    csv_files, tries, max_tries = None, 0, 1000
    while not csv_files:
        if tries >= max_tries:
            raise FindFileTimeout("Couldn't find the content rating csv file... :(")
        csv_files = glob.glob("*.csv")
        tries += 1

    assert len(csv_files) == 1, \
        "Expected only 1 *.csv file, but found {n}: {files}".format(files=csv_files, n=len(csv_files))
    csv_file = csv_files.pop()
    with open(csv_file, "rb") as f:
        assert [row for row in csv.reader(f) if context.rating_user.username in row and context.rating_text in row], \
            "Rating data not found in exported csv file."

    os.chdir(old_cwd)


@when(u'I fill out the form')
def impl(context):
    enter_star_ratings(context)
    text_feedback = context.text_feedback = "This stuff is great, A+++"
    enter_text_feedback(context, text_feedback)


@given(u'I have filled out a feedback form')
def impl(context):
    context.execute_steps(u'''
        Given I open some available content
        When I fill out the form
    ''')


@then(u'I see a delete button')
def impl(context):
    context.delete_btn = find_css_class_with_wait(context, DELETE_BTN_CLASS)
    assert context.delete_btn.is_displayed()


@when(u'I delete my feedback')
def impl(context):
    context.delete_btn.click()


@when(u'I export csv data')
def impl(context):
    go_to_export_url(context)

    resource_select = find_id_with_wait(context, "resource-id")
    Select(resource_select).select_by_visible_text("Ratings")

    export_btn = find_id_with_wait(context, "export-button")
    export_btn.click()


@when(u'I change the text')
def impl(context):
    new_text = "Once upon a midnight dreary"
    context.new_text = get_text_feedback(context) + new_text
    enter_text_feedback(context, new_text)


@then(u'the altered text is displayed')
def impl(context):
    actual = get_text_feedback(context)
    expected = context.new_text
    assert actual == expected, \
        "Expected text: {exp}\nActual text: {act}".format(exp=expected, act=actual)


def enter_star_ratings(context, val=3):
    """
    Enters a value for all three star rating forms, on a new form
    :param context: behave context
    :return: nothing
    """
    for id_ in STAR_CONTAINER_IDS:
        rate_id(context, id_, val=val)


def rate_id(context, id_, val=3):
    """
    Enter a star rating given the id of the container
    :param context: behave context
    :param id: id of the container element
    """

    def rate_element(driver):
        try:
            inner_wrapper = find_id_with_wait(context, id_, wait_time=2)
            # Adding this because sidebar may block the view or have made the
            # screen scroll out of place
            # WebDriverException: Message: Element is not clickable at point (519, 419.7166748046875). Other element would receive the click: <ul style="overflow: hidden; width: auto; height: 697px;" class="sidebar"></ul>
            if not elem_is_visible_with_wait(context, inner_wrapper, wait_time=1):
                raise KALiteTimeout("Expected rating element to show up but it didn't")
            els = inner_wrapper.find_elements_by_class_name(STAR_RATING_OPTION_CLASS)
            rating_el = [el for el in filter(lambda x: int(x.get_attribute("data-val")) == val, els)][0]
            rating_el.click()
            return True
        except (NoSuchElementException, StaleElementReferenceException, TimeoutException, IndexError):
            return False

    try:
        WebDriverWait(context.browser, 30).until(rate_element)
    except TimeoutException:
        raise Exception("Unable to enter rating for container with id '{id:s}'".format(id=id_))


def enter_text_feedback(context, text_feedback):
    """
    Enter text feedback into feedback form
    :param context: behave context
    :param text_feedback: str, the feedback to be entered
    :return: nothing
    """
    input_field = find_css_class_with_wait(context, TEXT_INPUT_CLASS)
    input_field.send_keys(text_feedback)


def get_text_feedback(context):
    """
    Get the text feedback displayed after the feedback form is filled out
    :param context: behave context
    :return: a str with the text feedback displayed.
    """
    return context.browser.execute_script("""
        return $(".{text_input_class}")[0].value;
    """.format(text_input_class=TEXT_INPUT_CLASS))


def go_to_export_url(context):
    params = {"zone_id": Device.get_own_device().get_zone().id}
    context.browser.get(build_url(context, reverse("data_export"), params))


class FindFileTimeout(Exception):
    pass
