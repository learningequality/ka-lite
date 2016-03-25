from behave import given, then
from kalite.testing.behave_helpers import go_to_homepage, build_url, reverse, assert_no_element_by_css_selector

@given("I am on the homepage")
def step_impl(context):
    go_to_homepage(context)

@given("I'm on update_videos page")
def step_impl(context):
    context.browser.get(build_url(context, reverse("update_videos")))

@then("I'm redirected to the homepage")
def step_impl(context):
    expected = build_url(context, reverse('homepage'), params={'login': True, 'next': reverse('update_videos')})
    actual = context.browser.current_url
    assert expected == actual, "Redirected to unexpected url. Expected: {exp}\nActual: {act}".format(exp=expected, act=actual)

@then("I see only superusercreate modal")
def step_impl(context):
    assert_no_element_by_css_selector(context, "#login-container")