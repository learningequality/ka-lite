import requests
import json
import cgi
import os
import readline
import SocketServer
import SimpleHTTPServer
import sys
from decorator import decorator
from functools import partial

from secrets import CONSUMER_KEY, CONSUMER_SECRET
from test_oauth_client import TestOAuthClient
from oauth import OAuthToken


class APIError(Exception):

    """
    Custom Exception Class for returning meaningful errors which are caused by changes
    in the Khan Academy API.
    """

    def __init__(self, msg, obj=None):
        self.msg = msg
        self.obj = obj

    def __str__(self):
        inspection = ""
        if self.obj:
            for id in id_to_kind_map:
                if id(self.obj):
                    inspection = "This occurred in an object of kind %s, called %s." % (
                        id_to_kind_map[id], id(self.obj))
        if not inspection:
            inspection = "Object could not be inspected. Summary of object keys here: %s" % str(
                self.obj.keys())
        return "Khan API Error: %s %s" % (self.msg, inspection)


def create_callback_server(REQUEST_TOKEN):
    """
    Adapted from https://github.com/Khan/khan-api/blob/master/examples/test_client/test.py
    Simple server to handle callbacks from OAuth request to browser.
    """

    class CallbackHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

        def do_GET(self):

            params = cgi.parse_qs(self.path.split(
                '?', 1)[1], keep_blank_values=False)
            REQUEST_TOKEN = OAuthToken(params['oauth_token'][
                                       0], params['oauth_token_secret'][0])
            REQUEST_TOKEN.set_verifier(params['oauth_verifier'][0])

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(
                'OAuth request token fetched; you can close this window.')

        def log_request(self, code='-', size='-'):
            pass

    server = SocketServer.TCPServer(('127.0.0.1', 0), CallbackHandler)
    return server


class AttrDict(dict):

    """
    Base class to give dictionary values from JSON objects are object properties.
    Recursively turn all dictionary sub-objects, and lists of dictionaries
    into AttrDicts also.
    """

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)

    def __getattr__(self, name):
        value = self[name]
        if isinstance(value, dict):
            value = AttrDict(value)
        if isinstance(value, list):
            for i in range(len(value)):
                if isinstance(value[i], dict):
                    value[i] = AttrDict(value[i])
        return value

    def __setattr__(self, name, value):
        self[name] = value


class APIModel(AttrDict):

    _related_field_types = {}  # this is a dummy; do not use directly

    API_attributes = {}  # this is also a dummy.

    def __getattr__(self, name):
        """
        Check to see if the attribute already exists in the object.
        If so, return that attribute according to super.
        If not, and the attribute is in API_attributes for this class,
        then make the appropriate API call to fetch the data, and set it
        into the object, so that repeated queries will not requery the API.
        """
        if name in self.API_attributes and name not in self:
            self[name] = api_call("v1", self.API_url(name), self.session)
            convert_items(name, self)
            return self[name]
        else:
            if name in self._related_field_types:
                convert_items(name, self)
                return self[name]
            else:
                return super(APIModel, self).__getattr__(name)

    def __init__(self, session, *args, **kwargs):

        self.session = session
        super(APIModel, self).__init__(*args, **kwargs)

    def API_url(self, name):
        """
        Generate the url from which to make API calls.
        """
        id = "/" + kind_to_id_map.get(self.kind)(
            self) if kind_to_id_map.get(self.kind) else ""
        get_param = "?" + get_key_to_get_param_map.get(kind_to_get_key_map.get(
            self.kind)) + "=" + self.get(kind_to_get_key_map.get(self.kind)) if kind_to_get_key_map.get(self.kind) else ""
        return self.base_url + id + self.API_attributes[name] + get_param


def api_call(target_version, target_api_url, session, debug=False, authenticate=True):
    """
    Generic API call function, that will try to use an authenticated request if available,
    otherwise will fall back to non-authenticated request.
    """
    # TODO : Use requests for both kinds of authentication.
    # usage : api_call("v1", "/badges")
    resource_url = "/api/" + target_version + target_api_url
    try:
        if authenticate and session.REQUEST_TOKEN and session.ACCESS_TOKEN:
            client = TestOAuthClient(session.SERVER_URL, CONSUMER_KEY, CONSUMER_SECRET)
            response = client.access_resource(resource_url, session.ACCESS_TOKEN)
        else:
            response = requests.get(session.SERVER_URL + resource_url).content
        json_object = json.loads(response)
    except Exception as e:
        print e
        return {}
    if(debug):
        print json_object
    return json_object


def class_by_kind(node):
    """
    Function to turn a dictionary into a Python object of the appropriate kind,
    based on the "kind" attribute found in the dictionary.
    """
    # TODO: Fail better or prevent failure when "kind" is missing.
    try:
        return kind_to_class_map[node["kind"]](node)
    except KeyError:
        raise APIError(
            "This kind of object should have a 'kind' attribute.", node)


def convert_list_to_classes(self, nodelist, class_converter=class_by_kind):
    """
    Convert each element of the list (in-place) into an instance of a subclass of APIModel.
    You can pass a particular class to `class_converter` if you want to, or it will auto-select by kind.
    """
    print nodelist
    for i in range(len(nodelist)):
        nodelist[i] = class_converter(nodelist[i])

    return nodelist  # just for good measure; it's already been changed


def class_by_name(node, name):
    """
    Function to turn a dictionary into a Python object of the kind given by name.
    """
    return kind_to_class_map[name](node)


def convert_items(name, self):
    """
    Convert attributes of an object to related object types.
    If in a list call to convert each element of the list.
    """

    # convert dicts to the related type
    if isinstance(self[name], dict):
        self[name] = self._related_field_types[name](self[name])
    # convert every item in related list to correct type
    elif isinstance(self[name], list):
        convert_list_to_classes(self[
                                name], class_converter=self._related_field_types[name])


def n_deep(obj, names):
    """
    A function to descend len(names) levels in an object and retrieve the attribute there.
    """
    for name in names:
        try:
            obj = getattr(obj, name)
        except KeyError:
            raise APIError(
                "This object is missing the %s attribute." % name, obj)
    return obj


class Khan():

    SERVER_URL = "http://www.khanacademy.org"

    # Set authorization objects to prevent errors when checking for Auth.

    def __init__(self, lang=None):
        self.lang = lang
        self.REQUEST_TOKEN = None
        self.ACCESS_TOKEN = None

    # def require_authentication():
    #     """
    #     Decorator to require authentication for particular request events.
    #     """
    #     if not (self.REQUEST_TOKEN and self.ACCESS_TOKEN):
    #         print "This data requires authentication."
    #         self.authenticate()
    #     return (self.REQUEST_TOKEN and self.ACCESS_TOKEN)


    # def authenticate(self):
    #     """
    #     Adapted from https://github.com/Khan/khan-api/blob/master/examples/test_client/test.py
    #     First pass at browser based OAuth authentication.
    #     """
    #     # TODO: Allow PIN access for non-browser enabled devices.

    #     server = create_callback_server(self.REQUEST_TOKEN)

    #     client = TestOAuthClient(self.SERVER_URL, CONSUMER_KEY, CONSUMER_SECRET)

    #     client.start_fetch_request_token(
    #         'http://127.0.0.1:%d/' % server.server_address[1])

    #     server.handle_request()

    #     server.server_close()

    #     self.ACCESS_TOKEN = client.fetch_access_token(self.REQUEST_TOKEN)

    def get_exercises(self):
        return convert_list_to_classes(api_call("v1", Exercise.base_url, self))

    def get_exercise(self, exercise_id):
        print api_call("v1", Exercise.base_url + "/" + exercise_id, self)
        return Exercise(api_call("v1", Exercise.base_url + "/" + exercise_id, self), self)

    def get_badges(self):
        return convert_list_to_classes(api_call("v1", Badge.base_url, self))

    def get_badge_category(self, category_id=None):
        if category_id is not None:
            return BadgeCategory(api_call("v1", BadgeCategory.base_url + "/categories/" + str(category_id), self)[0], self)
        else:
            return convert_list_to_classes(api_call("v1", BadgeCategory.base_url + "/categories", self))

    def get_user(self, user_id=""):
        """
        Download user data for a particular user.
        If no user specified, download logged in user's data.
        """
        if self.require_authentication():
            return User(api_call("v1", User.base_url + "?userId=" + user_id))

    def get_topic_tree(self, topic_slug=""):
        """
        Retrieve complete node tree starting at the specified root_slug and descending.
        """
        if topic_slug:
            return Topic(api_call("v1", Topic.base_url + "/" + topic_slug, self), self)
        else:
            return Topic(api_call("v1", "/topictree", self), self)

    def get_topic_exercises(self, topic_slug):
        """
        This will return a list of exercises in the highest level of a topic.
        Not lazy loading from get_tree, as any load of the topic data includes these.
        """
        return convert_list_to_classes(api_call("v1", Topic.base_url + "/" + topic_slug + "/exercises", self))

    def get_topic_videos(self, topic_slug):
        """
        This will return a list of videos in the highest level of a topic.
        Not lazy loading from get_tree, as any load of the topic data includes these.
        """
        return convert_list_to_classes(api_call("v1", Video.base_url + "/" + topic_slug + "/videos", self))

    def get_video(self, video_id):
        return Video(api_call("v1", self.base_url + "/" + video_id, self), self)


class Exercise(APIModel):

    base_url = "/exercises"

    _related_field_types = {
        "related_videos": partial(class_by_name, name="Video"),
        "followup_exercises": partial(class_by_name, name="Exercise"),
    }

    API_attributes = {
        "related_videos": "/videos",
        "followup_exercises": "/followup_exercises"
    }


class Badge(APIModel):

    base_url = "/badges"

    _related_field_types = {
        "user_badges": class_by_kind,
    }


class BadgeCategory(APIModel):
    pass


class APIAuthModel(APIModel):

    def __getattr__(self, name):
        if self.session.require_authentication():
            return super(APIAuthModel, self).__getattr__(name)

    # TODO: Add API_url function to add "?userID=" + user_id to each item
    # Check that classes other than User have user_id field.


class User(APIAuthModel):

    base_url = "/user"

    _related_field_types = {
        "videos": partial(class_by_name, name="UserVideo"),
        "exercises": partial(class_by_name, name="UserExercise"),
        "students": partial(class_by_name, name="User"),
    }

    API_attributes = {
        "videos": "/videos",
        "exercises": "/exercises",
        "students": "/students",
    }


class UserExercise(APIAuthModel):

    base_url = "/user/exercises"

    _related_field_types = {
        "exercise_model": class_by_kind,
        "followup_exercises": class_by_kind,
        "log": partial(class_by_name, name="ProblemLog"),
    }

    API_attributes = {
        "log": "/log",
        "followup_exercises": "/followup_exercises",
    }


class UserVideo(APIAuthModel):
    base_url = "/user/videos"

    _related_field_types = {
        "video": class_by_kind,
        "log": partial(class_by_name, name="VideoLog"),
    }

    API_attributes = {
        "log": "/log",
    }


class UserBadge(APIAuthModel):
    pass

# ProblemLog and VideoLog API calls return multiple entities in a list


class ProblemLog(APIAuthModel):
    pass


class VideoLog(APIAuthModel):
    pass


class Topic(APIModel):

    base_url = "/topic"

    _related_field_types = {
        "children": class_by_kind,
    }


class Separator(APIModel):
    pass


class Scratchpad(APIModel):
    pass


class Article(APIModel):
    pass


class Video(APIModel):

    base_url = "/videos"

    _related_field_types = {
        "related_exercises": class_by_kind,
    }

    API_attributes = {"related_exercises": "/exercises"}


# kind_to_class_map maps from the kinds of data found in the topic tree,
# and other nested data structures to particular classes.
# If Khan Academy add any new types of data to topic tree, this will break
# the topic tree rendering.


kind_to_class_map = {
    "Video": Video,
    "Exercise": Exercise,
    "Topic": Topic,
    "Separator": Separator,
    "Scratchpad": Scratchpad,
    "Article": Article,
    "User": User,
    "UserData": User,
    "UserBadge": UserBadge,
    "UserVideo": UserVideo,
    "UserExercise": UserExercise,
    "ProblemLog": ProblemLog,
    "VideoLog": VideoLog,
}


# Different API endpoints use different attributes as the id, depending on the kind of the item.
# This map defines the id to use for API calls, depending on the kind of
# the item.


kind_to_id_map = {
    "Video": partial(n_deep, names=["readable_id"]),
    "Exercise": partial(n_deep, names=["name"]),
    "Topic": partial(n_deep, names=["slug"]),
    # "User": partial(n_deep, names=["user_id"]),
    # "UserData": partial(n_deep, names=["user_id"]),
    "UserExercise": partial(n_deep, names=["exercise"]),
    "UserVideo": partial(n_deep, names=["video", "youtube_id"]),
    "ProblemLog": partial(n_deep, names=["exercise"]),
    "VideoLog": partial(n_deep, names=["video_title"]),
}

kind_to_get_key_map = {
    "User": "user_id",
    "UserData": "user_id",
    "UserExercise": "user",
    "UserVideo": "user",
}

get_key_to_get_param_map = {
    "user_id": "userId",
    "user": "username",
}

id_to_kind_map = {value: key for key, value in kind_to_id_map.items()}

if __name__ == "__main__":
    # print t.name
    # print t.children
    # print t.children[0].__class__
    # print t.children[1].__class__
    # print api_call("v1", "/videos");
    # print api_call("nothing");
    # Video.get_video("adding-subtracting-negative-numbers")
    # Video.get_video("C38B33ZywWs")
    Topic.get_tree()
