import shutil

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import UpdateProgressLog, VideoFile
from .videos import *
from fle_utils.chronograph.models import Job
from fle_utils.internet import invalidate_web_cache
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


@receiver(post_save, sender=VideoFile)
def invalidate_on_video_update(sender, **kwargs):
    """
    Listen in to see when videos become available.
    """
    # Can only do full check in Django 1.5+, but shouldn't matter--we should only save with
    # percent_complete == 100 once.
    just_now_available = kwargs["instance"] and kwargs["instance"].percent_complete == 100  # and "percent_complete" in kwargs["updated_fields"]
    if just_now_available:
        # This event should only happen once, so don't bother checking if
        #   this is the field that changed.
        logging.debug("Invalidating cache on VideoFile save for %s" % kwargs["instance"])
        from kalite import caching  # caching also imports updates; import here to prevent circular dependencies
        caching.invalidate_all_caches()


@receiver(pre_delete, sender=VideoFile)
def invalidate_on_video_delete(sender, **kwargs):
    """
    Listen in to see when available videos become unavailable.
    """
    was_available = kwargs["instance"] and kwargs["instance"].percent_complete == 100
    if was_available:
        logging.debug("Invalidating cache on VideoFile delete for %s" % kwargs["instance"])
        from kalite import caching  # caching also imports updates; import here to prevent circular dependencies
        caching.invalidate_all_caches()


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
