from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins.browser_mixins import BrowserActionMixins
from kalite.testing.mixins.facility_mixins import FacilityMixins


class TestShowAjaxMessages(BrowserActionMixins, FacilityMixins, KALiteBrowserTestCase):

    def test_ajax_messages(self):

        # Navigate to video that is not downloaded

        self.browse_to(
            self.reverse("learn") + "khan/math/algebra/introduction-to-algebra/overview_hist_alg/origins-of-algebra/")
        try:
            warning = "This content was not found! You must login as an admin/coach to download the content."
            element = WebDriverWait(self.browser, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR,"div.alert-warning")))
            self.assertTrue(warning in element.text)
        except TimeoutException:
            self.fail("Error: The element may not exist.")
