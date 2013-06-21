import settings
import thread
import time

from mplayer import *

def play_video_in_new_thread(*args, **kwargs):
    """ Starts mplayer in a new persistent thread, with an optional callback for seconds watched. """
    thread.start_new_thread(_video_thread, args, kwargs)

def _video_thread(*args, **kwargs):
    player = play_video(*args, **kwargs)
    callback = kwargs.get("callback", None)
    has_callback = callable(callback)
    last_timestamp = 0
    time.sleep(10)
    video_length = player.length
    while True:
        if not player.is_alive():
            break
        if has_callback:
            timestamp = player.time_pos
            if timestamp > last_timestamp:
                seconds_watched = min(timestamp - last_timestamp, 10)
                callback(seconds_watched, video_length)
            last_timestamp = timestamp
        time.sleep(10)

def play_video(youtube_id, *args, **kwargs):
    """ Starts mplayer from the current thread, for the specified YouTube ID. """
    player = Player("%s%s.mp4" % (settings.CONTENT_ROOT, youtube_id))
    player.fullscreen = True
    return player