"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from facility.models import FacilityUser

from .models import Playlist
from kalite.testing.mixins import CreateAdminMixin, CreateGroupMixin, CreateStudentMixin


class PlaylistTests(CreateStudentMixin, TestCase):
    # fixtures = ['single_student_testdata.json']

    def setUp(self):
        self.create_student()
        self.test_student = FacilityUser.objects.get(username='teststudent1')
        self.p = Playlist.objects.create(
            title="test playlist",
            description="An empty playlist",
        )

    def test_can_create_valid_empty_playlist(self):
        self.assertIsNone(self.p.full_clean())  # doesnt raise any error or anything

    def test_can_add_playlist_entry(self):
        self.p.add_entry(entity_kind='Video')

    def test_add_first_entry_sort_order_is_zero(self):
        entry = self.p.add_entry(entity_kind='Video')
        self.assertEquals(entry.sort_order, 0)

    def test_add_new_entry_sort_order_incremented(self):
        self.p.add_entry(entity_kind='Video')
        new_entry = self.p.add_entry(entity_kind='Video')
        self.assertEquals(new_entry.sort_order, 1)

    def test_add_new_entry_explicit_sort_order_other_entries_moved(self):
        entries = []
        for order in range(3):
            entries.append(self.p.add_entry(
                entity_kind='Video',
                sort_order=order
            ))

        self.p.add_entry(entity_kind='Video', sort_order=1)

        self.assertEqual(entries[0].reload().sort_order, 0)
        self.assertEqual(entries[1].reload().sort_order, 2)
        self.assertEqual(entries[2].reload().sort_order, 3)


class PlaylistAPITests(CreateGroupMixin, CreateAdminMixin, TestCase):
    def _playlist_url(self, playlist_id=None):
        '''
        If no playlist_id is given, returns a url that gets all
        playlists. If playlist_id is given, returns a detail url for that playlist
        '''
        if not playlist_id:
            return reverse("api_dispatch_list", kwargs={'resource_name': 'playlist'})
        else:
            return reverse("api_dispatch_detail", kwargs={'resource_name': 'playlist', 'pk': playlist_id})

    def setUp(self):
        self.admin = self.create_admin()
        self.group = self.create_group()
        self.client = Client()
        self.client.login(username='admin', password='admin')

    def test_playlist_list_url_exists(self):
        resp = self.client.get(self._playlist_url())
        self.assertEquals(resp.status_code, 200)

    def test_playlist_detail_url_exists(self):
        resp = self.client.get(self._playlist_url(0))
        self.assertEquals(resp.status_code, 200)
