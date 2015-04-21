from behave import *
from django.core.urlresolvers import reverse

from kalite.testing.behave_helpers import *

DROPDOWN_MENU_ID = "username"
NAVBAR_TOGGLE_ID = "navbar_toggle"
LOGOUT_LINK_ID = "nav_logout"


@given("I'm logged in as a coach")
def step_impl(context):
    login_as_coach(context)


@given("I can see the username dropdown menu")
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


def go_to_homepage(context):
    context.browser.get(build_url(context, reverse("homepage")))