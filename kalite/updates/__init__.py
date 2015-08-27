"""
TODO: NOTHING SHOULD BE HERE! It's prohibiting the import of other updates.xxx
modules at load time because it has so many preconditions for loading.

For now, it means that updates.settings has been copied over to kalite.settings

"""
import shutil

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import UpdateProgressLog, VideoFile
from .videos import *
from fle_utils.chronograph.models import Job
from fle_utils.internet.webcache import invalidate_web_cache
from kalite.i18n import get_localized_exercise_dirpath, get_srt_path, get_locale_path


# Signals

@receiver(post_save, sender=Job)
def my_handler(sender, **kwargs):
    job = kwargs['instance']
    if not job.is_running:
        # Update progress log to be cancelled as well.
        UpdateProgressLog.objects \
            .filter(process_name=job.command, completed=False) \
            .update(completed=True)


def delete_language(lang_code):

    langpack_resource_paths = [get_localized_exercise_dirpath(lang_code), get_srt_path(lang_code), get_locale_path(lang_code)]

    for langpack_resource_path in langpack_resource_paths:
        try:
            shutil.rmtree(langpack_resource_path)
            logging.info("Deleted language pack resource path: %s" % langpack_resource_path)
        except OSError as e:
            if e.errno != 2:    # Only ignore error: No Such File or Directory
                raise
            else:
                logging.debug("Not deleting missing language pack resource path: %s" % langpack_resource_path)

    invalidate_web_cache()
