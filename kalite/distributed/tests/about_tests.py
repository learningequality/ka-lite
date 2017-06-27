from django.core.urlresolvers import reverse

from kalite.testing.base import KALiteTestCase

class AboutTestCase(KALiteTestCase):

    def test_about(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)

    def test_about_data(self):
        response = self.client.get(reverse('about_data'))
        self.assertIn('success', response.content)
