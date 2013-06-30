"""
These will be run when you run "manage.py test [central].
These require a test server to be running, and multiple ports
  need to be available.  Run like this:
./manage.py test central --liveserver=localhost:8004-8010
".
"""

#import logging
#from selenium import webdriver
#from selenium.common.exceptions import NoSuchElementException

from django.contrib.auth.models import User

import settings
from utils.testing import central_only, KALiteCentralBrowserTestCase


@central_only
class SuperUserTest(KALiteCentralBrowserTestCase):
    """Log in the super user"""

    def test_superuser_login(self):
        """
        Tests that an existing admin user can log in.
        """

        self.login_user(self.admin_user.username, "test")


@central_only
class OrgUserRegistrationTest(KALiteCentralBrowserTestCase):
    user_email = "test_user@nowhere.com"
    password   = "password"

    def test_user_register(self):
        """Tests that a user can register"""
         
        self.register_user(username=self.user_email, password=self.password)


@central_only
class UserRegistrationCaseTest(KALiteCentralBrowserTestCase):
    user_email = "test_user@nowhere.com"
    password   = "password"

    def test_register_login_exact(self):
        """Tests that a user can login with the exact same email address as registered"""
         
        # Register user in one case
        self.register_user(username=self.user_email.lower(), password=self.password)
        self.activate_user(username=self.user_email.lower())

        # Login in the same case
        self.login_user(username=self.user_email.lower(), password=self.password)
        self.logout_user()


    def test_login_mixed(self):
        """Tests that a user can login with the uppercased version of the email address that was registered"""

        # Register user in one case
        self.register_user(username=self.user_email.lower(), password=self.password)
        self.activate_user(username=self.user_email.lower())

        # Login in the same case
        self.login_user(username=self.user_email.upper(), password=self.password)
        self.logout_user()


    def test_register_mixed(self):
        """Tests that a user cannot re-register with the uppercased version of an email address that was registered"""
         
        # Register user in one case
        self.register_user(username=self.user_email.lower(), password=self.password)
        self.activate_user(username=self.user_email.lower())

        # Try to register again in a different case
        self.register_user(username=self.user_email.upper(), password=self.password, expect_success=False)

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
        self.register_user(username=user1_uname, password=user1_password, first_name=user1_fname)
        self.activate_user(username=user1_uname)
        self.login_user(   username=user1_uname, password=user1_password)
        self.logout_user()

        self.register_user(username=user2_uname, password=user2_password, first_name=user2_fname)
        self.activate_user(username=user2_uname)
        self.login_user(   username=user2_uname, password=user2_password)
        self.logout_user()

        # Change the second user to be a case-different version of the first user
        user2 = User.objects.get(username=user2_uname)
        user2_uname = user1_uname.upper()
        user2.username = user2_uname
        user2.email = user2_uname
        user2.save()

        # First, make sure that user 1 can only log in with user 1's email/password
        self.login_user( username=user1_uname, password=user1_password) # succeeds
        errors = self.browser.find_elements_by_class_name("login_error")
        self.assertEqual(len(errors), 0, "No login errors on successful login.")
        self.logout_user()

        self.login_user( username=user2_uname, password=user1_password, expect_success=False) # fails
        errors = self.browser.find_elements_by_class_name("login_error")
        self.assertEqual(len(errors), 1, "Login errors on failed login.")
        self.assertIn("Incorrect user name or password", errors[0].text, "Error text on failed login.")
        
        # Now, check the same in the opposite direction.
        self.login_user( username=user2_uname, password=user2_password) # succeeds
        errors = self.browser.find_elements_by_class_name("login_error")
        self.assertEqual(len(errors), 0, "No login errors on successful login.")
        self.logout_user()

        self.login_user( username=user1_uname, password=user2_password, expect_success=False) # fails
        errors = self.browser.find_elements_by_class_name("login_error")
        self.assertEqual(len(errors), 1, "Login errors on failed login.")
        self.assertIn("Incorrect user name or password", errors[0].text, "Error text on failed login.")
