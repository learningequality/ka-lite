import thread
import time

from mplayer import *


def play_video(youtube_id, content_root, *args, **kwargs):
    """
    Starts mplayer from the current thread, for the specified YouTube ID.
    Defaults to full screen, but can be overridden by passing a boolean `fullscreen` argument.
    """
    player = Player("%s%s.mp4" % (content_root, youtube_id))
    player.fullscreen = kwargs.get("fullscreen", True)
    return player


def play_video_in_new_thread(*args, **kwargs):
    """
    Starts mplayer in a new persistent thread, with an optional callback that will be called every 10 seconds.
    The callback signature is `callback(<time_watched>, <video_length>)`, with both args in seconds.
    You can override the 10 second interval by passing in a `save_interval` argument.
    """
    thread.start_new_thread(_video_thread, args, kwargs)


def _video_thread(*args, **kwargs):
    # optional arguments
    save_interval = kwargs.get("save_interval", 10)
    callback = kwargs.get("callback")
    has_callback = callable(callback)
    
    # start mplayer, and get a handle for the player
    player = play_video(*args, **kwargs)
        
    last_timestamp = player.time_pos or 0
    time.sleep(save_interval)
    video_length = player.length
    
    while True:
        if not player.is_alive():
            break
        if has_callback:
            timestamp = player.time_pos
            if timestamp > last_timestamp:
                seconds_watched = min(timestamp - last_timestamp, save_interval)
                try:  # never trust a callback
                    callback(seconds_watched, video_length)  # does nothing with output from callback
                except Exception as e:
                    if kwargs.get("logger"):
                        kwargs["logger"].debug("Callback failed: %s" % e)
            last_timestamp = timestamp
        time.sleep(save_interval)
