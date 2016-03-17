from behave import given, then, when
from django.core.urlresolvers import reverse

from kalite.testing.behave_helpers import find_id_with_wait, assert_no_element_by_id, \
    elem_is_visible_with_wait, build_url, login_as_coach

DROPDOWN_MENU_ID = "username"
NAVBAR_TOGGLE_ID = "navbar_toggle"
LOGOUT_LINK_ID = "nav_logout"
DOCS_LINK_ID = "nav_documentation"


@given("I'm logged in as a coach")
def step_impl(context):
    login_as_coach(context)


@given(u"I can see the username dropdown menu")
def step_impl(context):
    go_to_homepage(context)
    context.dropdown_menu = dropdown_menu = find_id_with_wait(context, DROPDOWN_MENU_ID)
    if not dropdown_menu.is_displayed():
        # Perhaps the screen was too small and we need to expand the accordion menu
        navbar_toggle = find_id_with_wait(context, NAVBAR_TOGGLE_ID)
        navbar_toggle.click()
    assert elem_is_visible_with_wait(context, dropdown_menu), "Dropdown menu is not visible!"


@when("I click the username dropdown menu")
def step_impl(context):
    context.dropdown_menu.click()


@then("I see a logout link")
def step_impl(context):
    logout_link = find_id_with_wait(context, LOGOUT_LINK_ID)
    assert logout_link is not None, "Couldn't find the logout link in the DOM!"
    assert elem_is_visible_with_wait(context, logout_link), "Logout link is not visible!"


@then(u"I see the documentation link")
def step_impl(context):
    docs_link = find_id_with_wait(context, DOCS_LINK_ID)
    assert elem_is_visible_with_wait(context, docs_link), "Documentation link is not visible!"


@then(u"I do not see the documentation link")
def step_impl(context):
    find_id_with_wait(context, 'user-name')  # Ensure the menu has loaded at all
    assert_no_element_by_id(context, '#' + DOCS_LINK_ID)


def go_to_homepage(context):
    context.browser.get(build_url(context, reverse("homepage")))