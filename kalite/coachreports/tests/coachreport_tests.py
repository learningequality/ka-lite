from datetime import datetime

from kalite.main.models import AttemptLog
from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins import BrowserActionMixins, CreateAdminMixin, CreatePlaylistProgressMixin, FacilityMixins 

from kalite.testing import KALiteTestCase

class PlaylistProgressTest(FacilityMixins,
                           CreateAdminMixin,
                           CreatePlaylistProgressMixin,
                           BrowserActionMixins,
                           KALiteBrowserTestCase):

    def setUp(self):
        super(PlaylistProgressTest, self).setUp()
        self.setup_fake_device()
        self.facility = self.create_facility()
        self.admin = self.create_admin()
        self.student = self.create_student()
        self.playlist = self.create_playlist_progress(user=self.student)

    def test_student_playlist_progress(self):
        self.browser_login_student(username=self.student.username, password="password", facility_name=self.facility.name)
        self.browse_to(self.reverse('account_management'))

        # Confirm high level progress appears
        progress_bar = self.browser_wait_for_element(css_selector='.progress-bar')
        # progress_bar_success = self.browser_wait_for_element(css_selector='.progress-bar-success')
        self.assertTrue(progress_bar, "Playlist progress rendering incorrectly.")

        # Trigger API call
        self.browser.find_elements_by_class_name('toggle-details')[0].click()

        # Confirm lower-level progress appears
        playlist_details = self.browser_wait_for_element(css_selector='.progress-indicator-sm')
        self.assertTrue(playlist_details, "Didn't load details")
