import json

from django.core.urlresolvers import reverse
from django.test import Client

class KALiteClient(Client):
    
    def login(self, username, password, facility=None):

        self.get(reverse("login"))
        
        data = {
            "csrfmiddlewaretoken": self.cookies["csrftoken"].value,
            "facility": facility,
            "username": username,
            "password": password,
        }
        
        response = self.post(reverse("login"), data=data)
        
        return response.status_code == 302

    def post_json(self, path="", url_name="", data={}):
        
        assert path or url_name and not (path and url_name), "You must provide either a path or a reversible url_name!"
        assert isinstance(data, dict) or isinstance(data, basestring), "The 'data' argument must be either a dict or a string."

        if isinstance(data, dict):
            data = json.dumps(data)
        
        return self.post(path or reverse(url_name), data=data, content_type="application/json")

    def delete_videos(self, youtube_ids):
        return self.post_json(url_name="main.api_views.delete_videos", data={ "youtube_ids": youtube_ids })
        
    def save_video_log(self, **kwargs):
        return self.post_json(url_name="main.api_views.save_video_log", data=kwargs)
        
    def save_exercise_log(self, **kwargs):
        return self.post_json(url_name="main.api_views.save_exercise_log", data=kwargs)