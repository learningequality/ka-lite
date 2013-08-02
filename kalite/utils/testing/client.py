import json

from django.core.urlresolvers import reverse
from django.test import Client

class KALiteClient(Client):
    
    def login(self, username, password, facility):

        self.get(reverse("login"))
        
        data = {
            "csrfmiddlewaretoken": self.cookies["csrftoken"].value,
            "facility": facility,
            "username": username,
            "password": password,
        }
        
        response = self.post(reverse("login"), data=data)
        
        return response.status_code == 302

    def post_json(self, path="", pattern="", data={}):
        
        if not path and not pattern:
            raise Exception("You must provide either a path or a reversible pattern!")
        
        if isinstance(data, dict):
            data = json.dumps(data)
        elif not isinstance(data, basestring):
            raise Exception("The 'data' argument must be either a dict or a string.")
        
        return self.post(path or reverse(pattern), data=data, content_type="application/json")

    def save_video_log(self, **kwargs):
        return self.post_json(pattern="main.api_views.save_video_log", data=kwargs)
        
    def save_exercise_log(self, **kwargs):
        return self.post_json(pattern="main.api_views.save_exercise_log", data=kwargs)