from selenium.common.exceptions import NoSuchElementException

from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins import BrowserActionMixins, FacilityMixins


class TestShowAjaxMessages(BrowserActionMixins, FacilityMixins, KALiteBrowserTestCase):

    def test_ajax_messages(self):

        # Navigate to video that is not downloaded

        self.browse_to(
            self.reverse("learn") + "khan/math/algebra/introduction-to-algebra/overview_hist_alg/origins-of-algebra/")
        element = self.browser.find_element_by_css_selector("div.alert-warning").text
        try:
            warning = "This content was not found! You must login as an admin/coach to download the content."
            self.assertTrue(warning in element)
        except NoSuchElementException:
            self.fail("Error: The element may not exist.")