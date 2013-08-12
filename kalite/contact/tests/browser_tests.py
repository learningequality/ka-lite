"""
These will be run when you run "manage.py test [central].
These require a test server to be running, and multiple ports
  need to be available.  Run like this:
./manage.py test central --liveserver=localhost:8004-8010
".
"""
from central.tests import KALiteCentralBrowserTestCase
from utils.testing import central_server_test

@central_server_test
class ContactEmptyFormSubmitCaseTest(KALiteCentralBrowserTestCase):
    """
    Submit forms with no values, make sure there are no errors.
    """
    def test_contact_form(self):
        self.empty_form_test(url=self.reverse("contact_wizard"), submission_element_id="id_contact_form-name")
