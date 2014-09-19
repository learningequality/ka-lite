import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import Client


logging = settings.LOG


class KALiteClient(Client):
    facility = None
    teacher = None
    student = None
    facility_data = {}
    student_data = {}
    teacher_data = {}

    # urls
    login_url = ''
    logout_url = ''

    def __init__(self, *args, **kwargs):
        super(KALiteClient, self).__init__(*args, **kwargs)
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')

    def setUp(self):
        # Aron: we don't delete this since after a big refactoring
        # I don't wanna go ahead and remove all calls to self.client.setUp
        # again. Probably another time.
        pass

    def login(self, username, password, facility=None):
        self.get(self.login_url)
        data = {
            "csrfmiddlewaretoken": self.cookies["csrftoken"].value,
            "facility": facility,
            "username": username,
            "password": password,
        }
        response = self.post(self.login_url, data=data)
        return response.status_code == 302

    def login_user(self, data, facility=None, use_default_facility=True, follow=True):
        if facility:
            data['facility'] = facility.id
        elif use_default_facility and self.facility:
            data['facility'] = self.facility.id
        else:
            data['facility'] = None
        response = self.post(self.login_url, data=data, follow=follow)
        return response

    def login_teacher(self, data=None, facility=None, use_default_facility=True, follow=True):
        if not data:
            data = self.teacher_data
        response = self.login_user(data, follow=follow, facility=facility, use_default_facility=use_default_facility)
        # logging.warn('==> response %s' % response)
        return response

    def login_student(self, data=None, facility=None, use_default_facility=True, follow=True):
        if not data:
            data = self.student_data
        response = self.login_user(data, follow=follow, facility=facility, use_default_facility=use_default_facility)
        return response

    def logout(self):
        self.get(self.logout_url)

    def is_logged_in(self):
        logged_in = 'facility_user' in self.session
        return logged_in

    def is_logged_out(self):
        return not self.is_logged_in()

    def post_json(self, path="", url_name="", data={}):

        assert path or url_name and not (path and url_name), \
            "You must provide either a path or a reversible url_name!"
        assert isinstance(data, dict) or isinstance(data, basestring), \
            "The 'data' argument must be either a dict or a string."

        if isinstance(data, dict):
            data = json.dumps(data)

        return self.post(path or reverse(url_name), data=data, content_type="application/json")

    def delete_videos(self, youtube_ids):
        return self.post_json(url_name="delete_videos", data={"youtube_ids": youtube_ids})

    def save_video_log(self, **kwargs):
        return self.post_json(url_name="save_video_log", data=kwargs)

    def save_exercise_log(self, **kwargs):
        return self.post_json(url_name="save_exercise_log", data=kwargs)
