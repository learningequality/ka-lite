from django.db import models

from utils.django_utils import ExtendedModel


class LanguagePack(ExtendedModel):
    """ 
    Stores information about languages that have been installed on the distributed server. Explanation 
    of model fields:
        - code: iso-639 language code. ex: 'en' or 'pt-BR'
        - name: verbose language name. ex: 'English'
        - phrases: total number of strings available to be translated (count of msgids across po files)
        - approved_translations: total number of translations approved on crowdin. note: crowdin differentiates
        between translations that have been submitted and those that have been approved. 
        - percent_translated: approved_translations/phrases 
        - language_pack_version: the version of the language pack relative to software version. Starts at 1, 
        increments each time translations or subtitles get added. 
        - software_version: the software version that the language pack applies to
    """
    code = models.CharField(max_length=8, primary_key=True)
    name = models.CharField(max_length=50)
    phrases = models.PositiveIntegerField(default=0)
    approved_translations = models.PositiveIntegerField(default=0)
    percent_translated = models.PositiveIntegerField(default=0)
    language_pack_version = models.PositiveIntegerField(default=1)
    software_version = models.CharField(max_length=20, default=None)
    subtitle_count = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        return u"%s: %s" % (self.code, self.name)

