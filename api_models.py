import requests
import json
import cgi
import os
import readline
import SocketServer
import SimpleHTTPServer
import sys
from decorator import decorator

from secrets import CONSUMER_KEY, CONSUMER_SECRET
from test_oauth_client import TestOAuthClient
from oauth import OAuthToken

SERVER_URL = "http://www.khanacademy.org"

REQUEST_TOKEN = None
ACCESS_TOKEN = None


@decorator
def require_authentication(func, *args, **kwargs):
    """
    Decorator to require authentication for particular request events.
    """
    if not (REQUEST_TOKEN and ACCESS_TOKEN):
        print "This data requires authentication."
        authenticate()
    return func(*args, **kwargs)


def authenticate():
    server = create_callback_server()

    client = TestOAuthClient(SERVER_URL, CONSUMER_KEY, CONSUMER_SECRET)

    client.start_fetch_request_token(
        'http://127.0.0.1:%d/' % server.server_address[1])

    server.handle_request()

    server.server_close()

    global ACCESS_TOKEN

    ACCESS_TOKEN = client.fetch_access_token(REQUEST_TOKEN)


def create_callback_server():
    class CallbackHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

        def do_GET(self):
            global REQUEST_TOKEN

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
            self[name] = api_call("v1", self.API_url(name))
            convert_items(name, self)
            return self[name]
        else:
            return super(APIModel, self).__getattr__(name)

    def __init__(self, *args, **kwargs):

        super(APIModel, self).__init__(*args, **kwargs)

        for name in getattr(self, "_related_field_types", {}):
            if name in self:
                convert_items(name, self)

    def API_url(self, name):
        """
        Generate the url from which to make API calls.
        """
        return self.base_url + "/" + self[kind_to_id_map[self.kind]] + self.API_attributes[name]


def api_call(target_version, target_api_url, debug=True, authenticate=True):
    # usage : api_call("v1", "/badges")
    resource_url = "/api/" + target_version + target_api_url
    try:
        if authenticate and REQUEST_TOKEN and ACCESS_TOKEN:
            client = TestOAuthClient(SERVER_URL, CONSUMER_KEY, CONSUMER_SECRET)
            response = client.access_resource(resource_url, ACCESS_TOKEN)
        else:
            response = requests.get(SERVER_URL + resource_url).content
        json_object = json.loads(response)
    except Exception as e:
        print e
        return {}
    if(debug):
        print json_object
    return json_object


def class_by_kind(node):
    return kind_to_class_map[node["kind"]](node)


def convert_list_to_classes(nodelist, class_converter=class_by_kind):
    """
    Convert each element of the list (in-place) into an instance of a subclass of APIModel.
    You can pass a particular class to `class_converter` if you want to, or it will auto-select by kind.
    """

    for i in range(len(nodelist)):
        nodelist[i] = class_converter(nodelist[i])

    return nodelist  # just for good measure; it's already been changed


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


class Video(APIModel):

    base_url = "/videos"

    _related_field_types = {
        "related_exercises": class_by_kind,
    }

    API_attributes = {"related_exercises": "/exercises"}

    @classmethod
    def get_video(cls, video_id):
        return Video(api_call("v1", cls.base_url + "/" + video_id))


class Exercise(APIModel):

    base_url = "/exercises"

    _related_field_types = {
        "related_videos": class_by_kind,
        "followup_exercises": class_by_kind,
    }

    API_attributes = {"related_videos": "/videos",
                      "followup_exercises": "/followup_exercises"}

    @classmethod
    def get_exercise(cls, exercise_id):
        return Exercise(api_call("v1", cls.base_url + "/" + exercise_id))


class Topic(APIModel):

    base_url = "/topic"

    _related_field_types = {
        "children": class_by_kind,
    }

    @classmethod
    def get_tree(cls, topic_slug=""):
        """
        Retrieve complete node tree starting at the specified root_slug and descending.
        """
        if topic_slug:
            return Topic(api_call("v1", cls.base_url + "/" + topic_slug))
        else:
            return Topic(api_call("v1", "/topictree"))

    @classmethod
    def get_topic_exercises(cls, topic_slug):
        """
        This will return a list of exercises in the highest level of a topic.
        Not lazy loading from get_tree, as any load of the topic data includes these.
        """
        return convert_list_to_classes(api_call("v1", cls.base_url + "/" + topic_slug + "/exercises"))

    @classmethod
    def get_topic_videos(cls, topic_slug):
        """
        This will return a list of videos in the highest level of a topic.
        Not lazy loading from get_tree, as any load of the topic data includes these.
        """
        return convert_list_to_classes(api_call("v1", cls.base_url + "/" + topic_slug + "/videos"))


class User(APIModel):

    base_url = "/user"

    @classmethod
    @require_authentication
    def get_user(cls, user_id=""):
        """
        Download user data for a particular user.
        If no user specified, download logged in user's data.
        """
        return User(api_call("v1", cls.base_url + "?" + user_id))


class Badge(APIModel):

    base_url = "/badges"

    _related_field_types = {
        "user_badges": class_by_kind,
    }

    @classmethod
    def get_badges(cls):
        return convert_list_to_classes(api_call("v1", cls.base_url), Badge)

    @classmethod
    def get_category(cls, category_id=None):
        if category_id is not None:
            return BadgeCategory(api_call("v1", cls.base_url + "/categories/" + str(category_id))[0])
        else:
            return convert_list_to_classes(api_call("v1", cls.base_url + "/categories"), BadgeCategory)


class BadgeCategory(APIModel):
    pass


class UserExercise(APIModel):
    pass


class UserVideo(APIModel):
    pass


class UserBadge(APIModel):
    pass

# ProblemLog and VideoLog API calls return multiple entities in a list


class ProblemLog(APIModel):
    pass


class VideoLog(APIModel):
    pass


class Separator(APIModel):
    pass


class Scratchpad(APIModel):
    pass


class Article(APIModel):
    pass

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
    "UserBadge": UserBadge,
    "UserVideo": UserVideo,
    "UserExercise": UserExercise,
}


# Different API endpoints use different attributes as the id, depending on the kind of the item.
# This map defines the id to use for API calls, depending on the kind of
# the item.


kind_to_id_map = {
    "Video": "readable_id",
    "Exercise": "name",
    "Topic": "slug",
}

if __name__ == "__main__":
    # print t.name
    # print t.children
    # print t.children[0].__class__
    # print t.children[1].__class__
    # print api_call("v1", "/videos");
    # print api_call("nothing");
    # Video.get_video("adding-subtracting-negative-numbers")
    # Video.get_video("C38B33ZywWs")
    Topic.get_tree("addition-subtraction")
