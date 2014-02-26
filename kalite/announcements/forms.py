from django import forms

from announcements.models import Announcement


class AnnouncementForm(forms.ModelForm):
    
    class Meta:
        model = Announcement
        fields = [
            "title",
            "content",
            "site_wide",
            "members_only",
            "dismissal_type",
            "publish_start",
            "publish_end"
        ]