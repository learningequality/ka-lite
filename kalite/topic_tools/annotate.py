import os
import json

from django.conf import settings as django_settings
logging = django_settings.LOG

from django.utils.translation import gettext as _

from kalite import i18n

from . import settings
from .base import get_assessment_item_data


def is_content_on_disk(content_id, format="mp4", content_path=None):
    content_path = content_path or django_settings.CONTENT_ROOT
    content_file = os.path.join(content_path, content_id + ".%s" % format)
    return os.path.isfile(content_file)


def create_thumbnail_url(thumbnail):
    if is_content_on_disk(thumbnail, "png"):
        return django_settings.CONTENT_URL + thumbnail + ".png"
    elif is_content_on_disk(thumbnail, "jpg"):
        return django_settings.CONTENT_URL + thumbnail + ".jpg"
    return None


def update_content_availability(content_list, language="en"):
    # Loop through all content items and put thumbnail urls, content urls,
    # and subtitle urls on the content dictionary, and list all languages
    # that the content is available in.
    try:
        contents_folder = os.listdir(django_settings.CONTENT_ROOT)
    except OSError:
        contents_folder = []

    subtitle_langs = {}

    updates = {}

    if os.path.exists(i18n.get_srt_path()):
        for (dirpath, dirnames, filenames) in os.walk(i18n.get_srt_path()):
            # Only both looking at files that are inside a 'subtitles' directory
            if os.path.basename(dirpath) == "subtitles":
                lc = os.path.basename(os.path.dirname(dirpath))
                for filename in filenames:
                    if filename in subtitle_langs:
                        subtitle_langs[filename].append(lc)
                    else:
                        subtitle_langs[filename] = [lc]

    # English-language exercises live in application space, translations in user space
    if language == "en":
        exercise_root = os.path.join(settings.KHAN_EXERCISES_DIRPATH, "exercises")
    else:
        exercise_root = i18n.get_localized_exercise_dirpath(language)
    if os.path.exists(exercise_root):
        try:
            exercise_templates = os.listdir(exercise_root)
        except OSError:
            exercise_templates = []
    else:
        exercise_templates = []

    for content in content_list:

        # Some nodes are duplicated, but they require the same information
        # regardless of where they appear in the topic tree
        if content.get("id") not in updates:
            update = {}

            if content.get("kind") == "Exercise":

                # The central server doesn't have an assessment item database
                if django_settings.CENTRAL_SERVER:
                    continue
                elif content.get("uses_assessment_items", False):
                    items = []

                    assessment_items = content.get("all_assessment_items", [])

                    for item in assessment_items:
                        item = json.loads(item)
                        if get_assessment_item_data(request=None, assessment_item_id=item.get("id")):
                            items.append(item)
                            update["available"] = True
                    update["all_assessment_items"] = items
                else:
                    exercise_file = content.get("name", "") + ".html"

                    if language == "en":
                        exercise_template = exercise_file
                        if exercise_template in exercise_templates:
                            update["available"] = True
                            update["template"] = exercise_template
                    else:
                        exercise_template = os.path.join(language, exercise_file)
                        if exercise_template in exercise_templates:
                            update["available"] = True
                            update["template"] = exercise_template

            elif content.get("kind") == "Topic":
                # Ignore topics, as we only want to update their availability after we have updated the rest.
                continue
            else:
                default_thumbnail = create_thumbnail_url(content.get("id"))
                dubmap = i18n.get_id2oklang_map(content.get("id"))
                if dubmap:
                    content_lang = i18n.select_best_available_language(language, available_codes=dubmap.keys()) or ""
                    if content_lang:
                        dubbed_id = dubmap.get(content_lang)
                        format = content.get("format", "")
                        if (dubbed_id + "." + format) in contents_folder:
                            update["available"] = True
                            thumbnail = create_thumbnail_url(dubbed_id) or default_thumbnail
                            update["content_urls"] = {
                                "stream": django_settings.CONTENT_URL + dubmap.get(content_lang) + "." + format,
                                "stream_type": "{kind}/{format}".format(kind=content.get("kind").lower(), format=format),
                                "thumbnail": thumbnail,
                            }
                        elif django_settings.BACKUP_VIDEO_SOURCE:
                            update["available"] = True
                            update["content_urls"] = {
                                "stream": django_settings.BACKUP_VIDEO_SOURCE.format(youtube_id=dubbed_id, video_format=format),
                                "stream_type": "{kind}/{format}".format(kind=content.get("kind").lower(), format=format),
                                "thumbnail": django_settings.BACKUP_VIDEO_SOURCE.format(youtube_id=dubbed_id, video_format="png"),
                            }

                # Get list of subtitle language codes currently available
                subtitle_lang_codes = subtitle_langs.get("{id}.srt".format(id=content.get("id")), [])

                # Generate subtitle URLs for any subtitles that do exist for this content item
                subtitle_urls = [{
                    "code": lc,
                    "url": django_settings.STATIC_URL + "srt/{code}/subtitles/{id}.srt".format(code=lc, id=content.get("id")),
                    "name": i18n.get_language_name(lc)
                    } for lc in subtitle_lang_codes]

                # Sort all subtitle URLs by language code
                update["subtitle_urls"] = sorted(subtitle_urls, key=lambda x: x.get("code", ""))

            with i18n.translate_block(language):
                update["title"] = _(content.get("title"))
                update["description"] = _(content.get("description")) if content.get("description") else ""


            # Content is currently flagged as available, but is not. Flag as unavailable.
            if content.get("available") and "available" not in update:
                update["available"] = False

        # Path is the only unique key available.
        updates[content.get("path")] = update

    return updates
