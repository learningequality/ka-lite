
import json
from django.core.urlresolvers import reverse

from .models import Playlist
from kalite.testing.mixins import CreateAdminMixin, FacilityMixins
from kalite.testing.base import KALiteTestCase, KALiteClientTestCase


class PlaylistTests(FacilityMixins, KALiteTestCase):
    # fixtures = ['single_student_testdata.json']

    def setUp(self):

        self.test_student = self.create_student()
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


class PlaylistAPITests(FacilityMixins, CreateAdminMixin, KALiteClientTestCase):
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
        super(PlaylistAPITests, self).setUp()

        self.admin = self.create_admin()
        self.group = self.create_group()
        self.client.login(username='admin', password='admin')

    def test_playlist_list_url_exists(self):
        resp = self.client.get(self._playlist_url())
        self.assertEquals(resp.status_code, 200)

    def test_playlist_detail_url_exists(self):
        resp = self.client.get(self._playlist_url(0))
        self.assertEquals(resp.status_code, 200)

    def test_playlist_list_has_required_data(self):
        PLAYLIST_REQUIRED_ATTRIBUTES = [('description', unicode),
                                        ('entries', list),
                                        ('groups_assigned', list),
                                        ('id', unicode),
                                        ('tag', unicode),
                                        ('resource_uri', unicode),
                                        ('title', unicode)]

        resp = self.client.get(self._playlist_url())
        playlists = json.loads(resp.content)

        for playlist_dict in playlists['objects']:
            # verify each of the attributes. Indexing the playlist
            # dict shouldn't raise an error if they exist. We will
            # also verify that they're the correct type
            for attribute, attrtype in PLAYLIST_REQUIRED_ATTRIBUTES:
                val = playlist_dict[attribute]
                errmsgtemplate = "val %s for attribute %s is not of type %s; is actually of type %s"
                self.assertTrue(isinstance(val, attrtype), errmsgtemplate % (val, attribute, attrtype, type(val)))

    def test_playlist_detail_and_entry_has_required_data(self):
        PLAYLIST_REQUIRED_ATTRIBUTES = [('description', unicode),
                                        ('entries', list),
                                        ('groups_assigned', list),
                                        ('tag', unicode),
                                        ('id', unicode),
                                        ('resource_uri', unicode),
                                        ('title', unicode)]
        PLAYLIST_ENTRY_REQUIRED_ATTRIBUTES = [('entity_id', unicode),
                                              ('title', unicode),
                                              ('entity_kind', unicode),
                                              ('sort_order', int),
                                              ('description', unicode)]
        playlist_id = 'g3_p1'

        resp = self.client.get(self._playlist_url(playlist_id))
        playlist_dict = json.loads(resp.content)

        # check that the toplevel playlist attribute has the required data
        for attribute, attrtype in PLAYLIST_REQUIRED_ATTRIBUTES:
            val = playlist_dict[attribute]
            errmsgtemplate = "val %s for attribute %s is not of type %s; is actually of type %s"
            self.assertTrue(isinstance(val, attrtype), errmsgtemplate % (val, attribute, attrtype, type(val)))

        # check that each of the entries has the required data
        for entry in playlist_dict['entries']:
            for attribute, attrtype in PLAYLIST_ENTRY_REQUIRED_ATTRIBUTES:
                val = entry.get(attribute)
                errmsgtemplate = "val %s for attribute %s for entry %s is not of type %s; is actually of type %s"
                self.assertTrue(isinstance(val, attrtype), errmsgtemplate % (val, attribute, entry, attrtype, type(val)))
