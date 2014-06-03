from django.db import models

from fle_utils.django_utils import ExtendedModel

from kalite.facility.models import FacilityGroup, FacilityUser

from securesync.models import DeferredCountSyncedModel


class Playlist(ExtendedModel):
    title = models.CharField(max_length=30)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return "%(title)s:%(desc)s" % {'title': self.title, 'desc': self.description}

    def add_entry(self, *args, **kwargs):
        '''
        Add a playlist entry to the playlist. Automatically inserts the
        right sort order number, and moves other playlist entries if
        inserting an entry in the middle, aka adding an entry with an
        already existing sort order.

        '''
        if 'sort_order' not in kwargs:  # by default, append entry to the playlist
            try:
                last_entry = self.entries.order_by('-sort_order').all()[0]
                kwargs['sort_order'] = last_entry.sort_order + 1
            except IndexError:  # no entries yet
                kwargs['sort_order'] = 0
        else:
            num_entries = self.entries.count()
            entries_to_move = self.entries.filter(
                sort_order__gte=kwargs['sort_order']
            )
            if num_entries > 0 and entries_to_move.exists():
                entries_to_move.update(sort_order=models.F('sort_order') + 1)

        return self.entries.create(*args, **kwargs)


class PlaylistEntry(ExtendedModel):
    ENTITY_KINDS = (
        ('Video', 'Video'),
        ('Exercise', 'Exercise'),
        ('Quiz', 'Quiz'),
        ('Divider', 'Divider'),
    )

    entity_kind = models.CharField(max_length=10, choices=ENTITY_KINDS)
    entity_id = models.CharField(max_length=50)
    sort_order = models.IntegerField()
    description = models.TextField()
    playlist = models.ForeignKey(Playlist, related_name='entries')

    class Meta:
        ordering = ['playlist', 'sort_order']


class PlaylistToGroupMapping(ExtendedModel):
    playlist = models.CharField(db_index=True, max_length=15)
    group = models.ForeignKey(FacilityGroup, related_name='playlists')

class QuizLog(DeferredCountSyncedModel):
    user = models.ForeignKey(FacilityUser, blank=False, null=False, db_index=True)
    # test = models.ForeignKey(Test, blank=False, null=False, db_index=True)
    quiz = models.CharField(blank=False, null=False, max_length=100)
    # TODO: Field that stores the Test/playlist field.
    index = models.IntegerField(blank=False, null=False, default=0)
    complete = models.BooleanField(blank=False, null=False, default=False)
    # Attempts is the number of times the Quiz itself has been attempted.
    attempts = models.IntegerField(blank=False, null=False, default=0)
    total_number = models.IntegerField(blank=False, null=False, default=0)
    total_correct = models.IntegerField(blank=False, null=False, default=0)
    response_log = models.TextField(default="[]")

    class Meta:  # needed to clear out the app_name property from SyncedClass.Meta
        pass