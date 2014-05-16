from django.db import models

from fle_utils.django_utils import ExtendedModel

from kalite.facility.models import FacilityGroup


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
    playlist = models.IntegerField()
    group = models.ForeignKey(FacilityGroup, related_name='playlists')
