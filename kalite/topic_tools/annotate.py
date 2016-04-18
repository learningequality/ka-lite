import os

from django.conf import settings as django_settings

from kalite.i18n.base import get_subtitle_file_path, get_language_name
from kalite.updates.videos import get_local_video_size


logging = django_settings.LOG


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


def update_content_availability(content_list, language="en", channel="khan"):
    # Loop through all content items and put thumbnail urls, content urls,
    # and subtitle urls on the content dictionary, and list all languages
    # that the content is available in.

    # turn this whole function into a generator
    try:
        contents_folder = os.listdir(django_settings.CONTENT_ROOT)
    except OSError:
        contents_folder = []

    subtitle_langs = {}

    if os.path.exists(get_subtitle_file_path()):
        for (dirpath, dirnames, filenames) in os.walk(get_subtitle_file_path()):
            # Only both looking at files that are inside a 'subtitles' directory
            if os.path.basename(dirpath) == "subtitles":
                lc = os.path.basename(os.path.dirname(dirpath))
                for filename in filenames:
                    if filename in subtitle_langs:
                        subtitle_langs[filename].append(lc)
                    else:
                        subtitle_langs[filename] = [lc]

    subtitle_language_dir = language.replace("-", "_")

    for content in content_list:
        # Some nodes are duplicated, but they require the same information
        # regardless of where they appear in the topic tree

        update = {}

        if content.get("kind") == "Exercise":

            # Databases have been pre-filtered to only contain existing exercises.
            # Exercises have been pre-marked as available as well.
            # Assume if the assessment items have been downloaded, then everything is hunky dory.
            continue

        elif content.get("kind") == "Topic":
            # Ignore topics, as we only want to update their availability after we have updated the rest.
            continue
        else:
            file_id = content.get("youtube_id")
            default_thumbnail = create_thumbnail_url(content.get("id"))
            format = content.get("format", "")
            filename = file_id + "." + format if file_id else None

            # Get list of subtitle language codes currently available
            subtitle_lang_codes = subtitle_langs.get("{id}.vtt".format(id=content.get("id")), [])

            if filename and filename in contents_folder:
                update["files_complete"] = 1
                # File for this language is available and downloaded, so let's stamp the file size on it!
                update["size_on_disk"] = get_local_video_size(content.get("youtube_id"))
            else:
                # The video file for this content item does not exist. Set the files_complete and size_on_disk to 0
                if content.get("files_complete"):
                    update["files_complete"] = 0
                if content.get("size_on_disk"):
                    update["size_on_disk"] = 0
                # Set file_id to None as a flag that this file should not be used in any later processing.
                file_id = None

            if not file_id and subtitle_language_dir in subtitle_lang_codes and (content.get("id") + "." + format in contents_folder):
                # The file is not available in this language, but it is available in English and can be subtitled
                file_id = content.get("id")
                filename = file_id + "." + format

            if file_id:
                # We have a valid file_id (i.e. some file that we can use is available locally)
                update["available"] = True
                thumbnail = create_thumbnail_url(file_id) or default_thumbnail
                update["content_urls"] = {
                    "stream": django_settings.CONTENT_URL + filename,
                    "stream_type": "{kind}/{format}".format(kind=content.get("kind").lower(), format=format),
                    "thumbnail": thumbnail,
                }
            elif django_settings.BACKUP_VIDEO_SOURCE:
                # If the file is not available locally, but we are running the demo server, we want to serve the files
                # from the Internet.
                file_id = content.get("youtube_id", content.get("id"))
                update["available"] = True
                update["content_urls"] = {
                    "stream": django_settings.BACKUP_VIDEO_SOURCE.format(youtube_id=file_id, video_format=format),
                    "stream_type": "{kind}/{format}".format(kind=content.get("kind").lower(), format=format),
                    "thumbnail": django_settings.BACKUP_VIDEO_SOURCE.format(youtube_id=file_id, video_format="png"),
                }

            if update.get("available"):
                # Don't bother doing this work if the video is not available at all

                # Generate subtitle URLs for any subtitles that do exist for this content item
                subtitle_urls = [{
                    "code": lc,
                    "url": django_settings.STATIC_URL + "srt/{code}/subtitles/{id}.vtt".format(code=lc, id=content.get("id")),
                    "name": get_language_name(lc)
                    } for lc in subtitle_lang_codes]

                # Sort all subtitle URLs by language code
                update["subtitle_urls"] = sorted(subtitle_urls, key=lambda x: x.get("code", ""))

        # Content is currently flagged as available, but is not. Flag as unavailable.
        if content.get("available") and "available" not in update:
            update["available"] = False


        yield content.get("path"), update
