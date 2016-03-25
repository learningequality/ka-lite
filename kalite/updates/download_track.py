import json

from django.conf import settings
logging = settings.LOG

from .settings import VIDEO_DOWNLOAD_QUEUE_FILE

class VideoQueue(object):
    """
    This class handles queueing of videos for download.
    It is written to by functions that manipulate the queue,
    and read from by the videodownload management command that
    ultimately downloads the videos.
    """

    def __init__(self):

        self.load()

    def add_files(self, files, language=None):
        """
        Add files to the queue - this should be a list of youtube_ids
        and optionally, the language of the video.
        """
        files = [{"youtube_id": key, "title": value, "language": language} for key, value in files.items()]
        files.extend(self.queue)
        self.queue = files
        self.save()

    def save(self):
        """Save the current queue to disk"""
        try:
            with open(VIDEO_DOWNLOAD_QUEUE_FILE, "w") as f:
                json.dump(self.queue, f)
        except IOError:
            logging.warn("Failed to save video queue file.")

    def load(self):
        """Load the queue from disk, or default to an empty list"""
        try:
            with open(VIDEO_DOWNLOAD_QUEUE_FILE, "r") as f:
                self.queue = json.load(f) or []
        except (IOError, ValueError):
            self.queue = []

    def remove_file(self, youtube_id):
        """Remove the last file from the list, and check that it matches the passed in youtube_id"""
        try:
            removed_file = self.queue.pop()
            if removed_file.get("youtube_id") != youtube_id:
                logging.warn("Tried to remove {youtube_id} from file queue but found {removed_file} instead.".format(youtube_id=youtube_id, removed_file=removed_file.get("youtube_id")))
            else:
                self.save()
        except IndexError:
            logging.warn("Tried to remove {youtube_id} from file queue, but was empty instead.".format(youtube_id=youtube_id))

    def clear(self):
        """Clear all currently queued videos"""
        self.queue = []
        self.save()

    def next(self):
        try:
            return self.queue[-1]
        except IndexError:
            return None

    def count(self):
        return len(self.queue)
