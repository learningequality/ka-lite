Khan Academy API (Python wrapper)
=========

This is a Python wrapper for the Khan Academy API.

Documentation
Khan Academy API: https://github.com/Khan/khan-api/wiki/Khan-Academy-API

To use:

In order to support multiple authentication sessions to the Khan Academy API, and different language settings, every call to the API is done through a Khan() session.

```python
from api_models import *

#By default lang is set to "en", here we are setting it to Spanish.
khan = Khan(lang="es")

#Get entire Khan Academy topic tree
topic_tree = khan.get_topic_tree()

#Get information for a user - by default it will be whatever user you log in as, but if you are a coach for other users, can retrieve their information also
#If not already authenticated, this will create an OAuth authentication session which will need to be verified via the browser.
current_user = khan.get_user()
```

Khan session object methods available for most documented items in the API.

```python 
khan.get_badge_category()
khan.get_badges()
khan.get_exercise()
khan.get_exercises()
khan.get_topic_exercises()
khan.get_topic_tree()
khan.get_topic_videos()
khan.get_user()
khan.get_video()
```