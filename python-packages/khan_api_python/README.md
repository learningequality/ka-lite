Khan Academy API (Python wrapper)
=========

This is a Python wrapper for the Khan Academy API.

Documentation
Khan Academy API: https://github.com/Khan/khan-api/wiki/Khan-Academy-API

To use:

In order to support multiple authentication sessions to the Khan Academy API, and different language settings, every call to the API is done through a Khan() session.

```python
from api_models import *
```
By default lang is set to "en", here we are setting it to Spanish.
```python
khan = Khan(lang="es")
```
Get entire Khan Academy topic tree
```python
topic_tree = khan.get_topic_tree()
```
Get information for a user - by default it will be whatever user you log in as, but if you are a coach for other users, can retrieve their information also
If not already authenticated, this will create an OAuth authentication session which will need to be verified via the browser.
```python
current_user = khan.get_user()
```

Khan session object methods available for most documented items in the API.

```python 
khan.get_badge_category()
khan.get_badges()
khan.get_exercise("<exercise_id>")
khan.get_exercises()
khan.get_topic_exercises("<topic_id>")
khan.get_topic_videos("<topic_id>")
khan.get_topic_tree()
khan.get_user("<user_id=current-user>")
khan.get_video("<video_id>")
khan.get_playlists()
khan.get_playlist_exercises("<playlist_id>")
khan.get_playlist_videos("<playlist_id>")
```

No authentication is required for anything but user data. In order to authenticate to retrieve user data, the secrets.py.template needs to be copied to secrets.py and a CONSUMER_KEY and CONSUMER_SECRET entered.

In addition to documented API endpoints, this wrapper also exposes the following functions.

```python
khan.get_videos()
khan.get_assessment_item("<assessment_item_id>")
khan.get_tags()
```


You can register your app with the Khan Academy API here to get these two items:
https://www.khanacademy.org/api-apps/register