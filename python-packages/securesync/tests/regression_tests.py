"""
Regressions tests. 
"""

from mock import patch

from django.test import TestCase
from ..devices.views import central_server_down_or_error
from ..devices.models import SyncedModel

class DummySyncedModelClass(SyncedModel):
    pass

class CentralServerDownMessageTest(TestCase):
    """ Tests that if the central server is down, then an error message
    saying as much is returned. Otherwise assume that an actual error message
    was returned by the central server, and pass it along.
    """

    @patch('requests.get')
    def test_error_message_when_central_server_down(self, mock):
        mock().status_code = 500
        error_msg = "Some error message ah!"
        expected_msg = "Central Server is not reachable; please try again after some time."
        self.assertEqual(central_server_down_or_error(error_msg)['error_msg'], expected_msg)
    
    @patch('requests.get')
    def test_error_message_when_central_server_up(self, mock):
        mock().status_code = 200
        error_msg = "Some error message ah!"
        expected_msg = "Some error message ah!"
        self.assertEqual(central_server_down_or_error(error_msg)['error_msg'], expected_msg)


class SimpleBugRegressionTests(TestCase):
    """ Tests for simple regressions, e.g. caused by syntax or runtime errors.
    """

    def test_for_full_clean_concatenation_bug(self):
        """ Tests that SyncedModel.full_clean does not regress with the error:
        `TypeError: can only concatenate list (not "tuple") to list`
        """
        m = DummySyncedModelClass()
        m.full_clean(imported=True)
