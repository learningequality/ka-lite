import time

from django.conf import settings
from django.utils import unittest

from kalite.testing.base import KALiteBrowserTestCase


class KnowledgeMapTests(KALiteBrowserTestCase):

    @unittest.skipIf("medium" in settings.TESTS_TO_SKIP, "Skipping medium-length test")
    def test_exercise_dashboard(self, map_url=None):
        """
        Get the dashboard.  Validate it, as well as all subpages.
        """
        if not map_url:
            map_url = self.reverse("exercise_dashboard")

        # Get the data
        self.browse_to(map_url)
        time.sleep(0.5)
        exercise_elements = self.browser.find_elements_by_css_selector('div.exercise a')
        self.assertTrue(len(exercise_elements) > 0, "# elements is non-zero for url=%s" % map_url)

        #
        link_urls = []
        for exercise in exercise_elements:
            #self.assertTrue(exercise.is_displayed(), "Exercise %s should be displayed @ %s" % (exercise, map_url))
            url = exercise.get_attribute("href")
            if url.startswith(self.reverse("exercise_dashboard")):
                link_urls.append(url)
            self.assertTrue(url is not None and url!= "")

        for url in link_urls:
            self.test_exercise_dashboard(map_url=url)
            time.sleep(2.)
