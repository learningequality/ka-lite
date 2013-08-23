"""
These will be run when you run "manage.py test [central].
These require a test server to be running, and multiple ports
  need to be available.  Run like this:
./manage.py test central --liveserver=localhost:8004-8010
".
"""
import time
from selenium.webdriver.common.keys import Keys

from django.contrib.auth.models import User

import settings
from registration.models import RegistrationProfile
from utils.testing import central_server_test, BrowserTestCase


@central_server_test
class KALiteCentralBrowserTestCase(BrowserTestCase):
    """
    Base class for browser-based central server test cases.
    """

    def browser_register_user(self, username, password, first_name="firstname", last_name="lastname", org_name="orgname", expect_success=True):
        """Registers a user on the central server (and performs relevant checks, unless expect_success=False)"""
         
        register_url = self.reverse("registration_register")

        self.browse_to(register_url) # Load page
        self.assertIn("Sign up", self.browser.title, "Register page title")
        
        # Part 1: REGISTER
        self.browser_activate_element(id="id_first_name") # explicitly set the focus, to start
        self.browser_form_fill(first_name)  # first name
        self.browser_form_fill(last_name)  # last name
        self.browser_form_fill(username)  #email
        self.browser_form_fill(org_name, num_expected_links=1)  #org name
        self.browser_form_fill(password)  #password
        self.browser_form_fill(password)  #password (again)
        self.browser_form_fill("")  #newsletter subscription
        self.browser_form_fill(Keys.SPACE, num_expected_links=1)  # checkbox 2: EULA
        self.browser_form_fill(Keys.SPACE, num_expected_links=1)  # checkbox 3: EULA2
        self.browser_send_keys(Keys.RETURN)  # submit the form

        # Make sure that the page changed to the "thank you" confirmation page
        if expect_success:
            self.assertTrue(self.wait_for_page_change(register_url), "RETURN causes page to change")
            self.assertIn(self.reverse("registration_complete"), self.browser.current_url, "Register browses to thank you page" )
            self.assertIn("Registration complete", self.browser.title, "Check registration complete title")



    def browser_activate_user(self, username, expect_success=True):
        """Activates a user account on the central server (and performs relevant checks, unless expect_success=False)"""
        
        # Get the activation url, then browse there.
        user = User.objects.get(username=username)
        profile = RegistrationProfile.objects.get(user=user)
        activation_key = profile.activation_key
        self.assertNotEqual(activation_key, "ALREADY_ACTIVATED", "Make sure the user wasn't already activated.")
        
        activation_url = self.reverse('registration_activate', kwargs={ 'activation_key': activation_key });
        self.browse_to(activation_url)
        
        # Verify what we see!
        if expect_success:
            self.browser_check_django_message(message_type="success", contains="Your account is now activ", num_messages=1)


    def browser_login_user(self, username, password, expect_success=True):
        """Logs a user account in to the central server (and performs relevant checks, unless expect_success=False)"""

        login_url = self.reverse("auth_login")
        self.browse_to(login_url) # Load page
        self.assertIn("Log in", self.browser.title, "Login page title")
        
        # Focus should be on username, pasword and submit
        #   should be accessible through keyboard only.
        self.browser.find_element_by_id("id_username").clear()
        self.browser.find_element_by_id("id_username").click() # explicitly set the focus, to start
        self.browser_form_fill(username)
        self.browser_form_fill(password)
        self.browser_send_keys(Keys.RETURN)
        
        # Make sure that the page changed to the admin homepage
        if expect_success:
            self.assertTrue(self.wait_for_page_change(login_url), "RETURN causes page to change")
            self.assertIn(self.reverse("homepage"), self.browser.current_url, "Login browses to homepage (account admin)" )
            self.assertIn("Account administration", self.browser.title, "Check account admin page title")

        
    def browser_logout_user(self, expect_success=True):
        """Logs a user account out of the central server (and performs relevant checks, unless expect_success=False)"""
        
        # Nothing to do if they're not logged in!
        if not self.browser_is_logged_in():
            return
        
        # To avoid detection of page changes, do different things based on the 
        #   (assumed) server redirect after logout happens.
        if self.reverse("homepage") in self.browser.current_url:
            self.browser.get(self.reverse("auth_logout"))
        else:
            self.browse_to(self.reverse("auth_logout"))
    
        if expect_success:
            self.assertIn(self.reverse("homepage"), self.browser.current_url, "Logout browses to homepage" )
            self.assertFalse(self.browser_is_logged_in(), "Make sure that user is no longer logged in.")


    def browser_is_logged_in(self, username=None):
        """Checks if a user account is logged in to the central server."""
        elements = self.browser.find_elements_by_id("logout")
        
        if len(elements)==0:
            return False
        elif username is None:
            return True
        else:
            return elements[0].text.startswith(username + " ")
        
        

@central_server_test
class SuperUserTest(KALiteCentralBrowserTestCase):
    """Log in the super user"""

    def test_superuser_login(self):
        """
        Tests that an existing admin user can log in.
        """

        self.browser_login_user(self.admin_user.username, "test")


#@central_server_test
class OrgUserRegistrationTest(KALiteCentralBrowserTestCase):
    user_email = "test_user@nowhere.com"
    password   = "password"

    def test_user_register(self):
        """Tests that a user can register"""
         
        self.browser_register_user(username=self.user_email, password=self.password)


@central_server_test
class UserRegistrationCaseTest(KALiteCentralBrowserTestCase):
    user_email = "test_user@nowhere.com"
    password   = "password"

    def test_register_login_exact(self):
        """Tests that a user can login with the exact same email address as registered"""
         
        # Register user in one case
        self.browser_register_user(username=self.user_email.lower(), password=self.password)
        self.browser_activate_user(username=self.user_email.lower())

        # Login in the same case
        self.browser_login_user(username=self.user_email.lower(), password=self.password)
        self.browser_logout_user()

        
    def test_login_mixed(self):
        """Tests that a user can login with the uppercased version of the email address that was registered"""
         
        # Register user in one case
        self.browser_register_user(username=self.user_email.lower(), password=self.password)
        self.browser_activate_user(username=self.user_email.lower())

        # Login in the same case
        self.browser_login_user(username=self.user_email.upper(), password=self.password)
        self.browser_logout_user()
        

    def test_register_mixed(self):
        """Tests that a user cannot re-register with the uppercased version of an email address that was registered"""
        
        # Register user in one case
        self.browser_register_user(username=self.user_email.lower(), password=self.password)
        self.browser_activate_user(username=self.user_email.lower())

        # Try to register again in a different case
        self.browser_register_user(username=self.user_email.upper(), password=self.password, expect_success=False)

        text_box = self.browser.find_element_by_id("id_email") # form element        
        error    = text_box.parent.find_elements_by_class_name("errorlist")[-1]
        self.assertIn("This email address is already in use.", error.text, "Check 'email is in use' error.")


    def test_login_two_users_different_cases(self):
        """Tests that a user cannot re-register with the uppercased version of an email address that was registered"""
        
        user1_uname = self.user_email.lower()
        user2_uname = "a"+self.user_email.lower()
        user1_password = self.password
        user2_password = "a"+self.password
        user1_fname = "User1"
        user2_fname = "User2"
        
        # Register & activate two users with different usernames / emails
        self.browser_register_user(username=user1_uname, password=user1_password, first_name=user1_fname)
        self.browser_activate_user(username=user1_uname)
        self.browser_login_user(   username=user1_uname, password=user1_password)
        self.browser_logout_user()
        
        self.browser_register_user(username=user2_uname, password=user2_password, first_name=user2_fname)
        self.browser_activate_user(username=user2_uname)
        self.browser_login_user(   username=user2_uname, password=user2_password)
        self.browser_logout_user()
        
        # Change the second user to be a case-different version of the first user
        user2 = User.objects.get(username=user2_uname)
        user2_uname = user1_uname.upper()
        user2.username = user2_uname
        user2.email = user2_uname
        user2.save()
        
        # First, make sure that user 1 can only log in with user 1's email/password
        self.browser_login_user( username=user1_uname, password=user1_password) # succeeds
        errors = self.browser.find_elements_by_class_name("errorlist")
        self.assertEqual(len(errors), 0, "No login errors on successful login.")
        self.browser_logout_user()
        
        self.browser_login_user( username=user2_uname, password=user1_password, expect_success=False) # fails
        errors = self.browser.find_elements_by_class_name("errorlist")
        self.assertEqual(len(errors), 1, "Login errors on failed login.")
        self.assertIn("Incorrect user name or password", errors[0].text, "Error text on failed login.")
        
        # Now, check the same in the opposite direction.
        self.browser_login_user( username=user2_uname, password=user2_password) # succeeds
        errors = self.browser.find_elements_by_class_name("errorlist")
        self.assertEqual(len(errors), 0, "No login errors on successful login.")
        self.browser_logout_user()

        self.browser_login_user( username=user1_uname, password=user2_password, expect_success=False) # fails
        errors = self.browser.find_elements_by_class_name("errorlist")
        self.assertEqual(len(errors), 1, "Login errors on failed login.")
        self.assertIn("Incorrect user name or password", errors[0].text, "Error text on failed login.")
        

@central_server_test
class CentralEmptyFormSubmitCaseTest(KALiteCentralBrowserTestCase):
    """
    Submit forms with no values, make sure there are no errors.
    """
    def test_login_form(self):
        self.empty_form_test(url=self.reverse("auth_login"), submission_element_id="id_username")

    def test_registration_form(self):
        self.empty_form_test(url=self.reverse("registration_register"), submission_element_id="id_first_name")

    def test_password_reset(self):
        self.empty_form_test(url=self.reverse("auth_password_reset"), submission_element_id="id_email")
        

class RegressionTests(KALiteCentralBrowserTestCase):

    def test_issue_300(self):
        """Unauthorized access across central server accounts."""
        user1_uname = "a@a.com"
        user2_uname = "b@b.com"
        user1_password = "a"
        user2_password = "b"
        
        # Register & activate two users with different usernames / emails
        self.browser_register_user(username=user1_uname, password=user1_password)
        self.browser_activate_user(username=user1_uname)
        self.browser_login_user(   username=user1_uname, password=user1_password)

        # Verify that we can go to the page with the correct user
        user1_zone_link = self.browser.find_element_by_css_selector(".zones a.zone-manage-link").get_attribute("href")
        self.browse_to(user1_zone_link)
        self.assertEqual(self.browser.current_url, user1_zone_link)

        # Now create and log in user 2.
        self.browser_logout_user()
        self.browser_register_user(username=user2_uname, password=user2_password)
        self.browser_activate_user(username=user2_uname)
        self.browser_login_user(   username=user2_uname, password=user2_password)

        # Now try 
        self.assertNotEqual(self.browser.current_url, user1_zone_link)
        self.browser_check_django_message(message_type="error", contains="You must be logged in with an account authorized to view this page.", num_messages=1)

