import logging
import version
from .models import LanguagePack

# on startup, make sure the english LanguagePack exists
logging.info('Ensuring en language pack exists...')
LanguagePack.objects.get_or_create(
    code='en',
    defaults={
        'software_version': version.VERSION,
        'language_pack_version': 0,
        'percent_translated': 100,
        'subtitle_count': 0,
        'name': 'English',
    })
