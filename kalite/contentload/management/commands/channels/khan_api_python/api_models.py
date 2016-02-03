import requests
import json
import cgi
import os
import SocketServer
import SimpleHTTPServer
import sys
import copy
from decorator import decorator
from functools import partial

try:
    from secrets import CONSUMER_KEY, CONSUMER_SECRET
except ImportError:
    CONSUMER_KEY = None
    CONSUMER_SECRET = None
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


def create_callback_server(session):
    """
    Adapted from https://github.com/Khan/khan-api/blob/master/examples/test_client/test.py
    Simple server to handle callbacks from OAuth request to browser.
    """

    class CallbackHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

        def do_GET(self):

            params = cgi.parse_qs(self.path.split(
                '?', 1)[1], keep_blank_values=False)
            session.REQUEST_TOKEN = OAuthToken(params['oauth_token'][
                0], params['oauth_token_secret'][0])
            session.REQUEST_TOKEN.set_verifier(params['oauth_verifier'][0])

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

    # _related_field_types = None  # this is a dummy; do not use directly

    # _lazy_related_field_types = None  # this is a dummy.

    # _API_attributes = None  # this is also a dummy.

    def __getattr__(self, name):
        """
        Check to see if the attribute already exists in the object.
        If so, return that attribute according to super.
        If not, and the attribute is in API_attributes for this class,
        then make the appropriate API call to fetch the data, and set it
        into the object, so that repeated queries will not requery the API.
        """
        if name in self:
            if name.startswith("_"):
                return super(APIModel, self).__getattr__(name)
            if name in self._lazy_related_field_types or name in self._related_field_types:
                self._session.convert_items(name, self, loaded=(name in self._related_field_types))
                return self[name]
            else:
                return super(APIModel, self).__getattr__(name)
        if name in self._API_attributes:
            self[name] = api_call("v1", self.API_url(name), self._session)
            self._session.convert_items(name, self)
            return self[name]
        if not self._loaded and name not in self:
            self.fetch()
        if name in self._related_field_types:
            self._session.convert_items(name, self)
            return self[name]
        else:
            return super(APIModel, self).__getattr__(name)

    def __init__(self, *args, **kwargs):

        session = kwargs.get('session')
        loaded = kwargs.get('loaded', True)
        kwargs.pop('session', None)
        kwargs.pop('loaded', None)
        super(APIModel, self).__init__(*args, **kwargs)
        self._session = session
        self._loaded = loaded
        self._related_field_types = {}
        self._lazy_related_field_types = {}
        self._API_attributes = {}

    def API_url(self, name):
        """
        Generate the url from which to make API calls.
        """
        id = "/" + kind_to_id_map.get(self.kind)(
            self) if kind_to_id_map.get(self.kind) else ""
        get_param = "?" + get_key_to_get_param_map.get(kind_to_get_key_map.get(
            self.kind)) + "=" + self.get(kind_to_get_key_map.get(self.kind)) if kind_to_get_key_map.get(self.kind) else ""
        if self._session.lang:
            get_param = get_param + "&lang=" if get_param else "?lang="
            get_param += self._session.lang
        return self.base_url + id + self._API_attributes[name] + get_param

    def fetch(self):
        self.update(api_call(
            "v1", self.base_url + "/" + self[kind_to_id_map.get(type(self).__name__, "id")], self._session))
        self._loaded = True

    def toJSON(self):
        output = {}
        for key in self._related_field_types.keys() + self._lazy_related_field_types.keys():
            if self.get(key, None):
                if isinstance(self[key], APIModel):
                    output[key] = self[key].toJSON()
                elif isinstance(self[key], dict):
                    output[key] = json.dumps(self[key])
                elif isinstance(self[key], list):
                    output[key] = []
                    for i, item in enumerate(self[key]):
                        if isinstance(self[key][i], APIModel):
                            output[key].append(self[key][i].toJSON())
                        elif isinstance(self[key][i], dict):
                            output[key].append(json.dumps(self[key][i]))
        for key in self:
            if key not in self._related_field_types.keys() + self._lazy_related_field_types.keys():
                if not (key.startswith("_") or hasattr(self[key], '__call__')):
                    output[key] = self[key]
        return json.dumps(output)

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
            client = TestOAuthClient(
                session.SERVER_URL, CONSUMER_KEY, CONSUMER_SECRET)
            response = client.access_resource(
                resource_url, session.ACCESS_TOKEN)
        else:
            response = requests.get(session.SERVER_URL + resource_url).content
        json_object = json.loads(response)
    except Exception as e:
        print e, "for target: %(target)s " % {"target": target_api_url}
        return {}
    if(debug):
        print json_object
    return json_object


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

    def require_authentication(self):
        """
        Decorator to require authentication for particular request events.
        """
        if not (self.REQUEST_TOKEN and self.ACCESS_TOKEN):
            print "This data requires authentication."
            self.authenticate()
        return (self.REQUEST_TOKEN and self.ACCESS_TOKEN)

    def authenticate(self):
        """
        Adapted from https://github.com/Khan/khan-api/blob/master/examples/test_client/test.py
        First pass at browser based OAuth authentication.
        """
        # TODO: Allow PIN access for non-browser enabled devices.

        if CONSUMER_KEY and CONSUMER_SECRET:

            server = create_callback_server(self)

            client = TestOAuthClient(
                self.SERVER_URL, CONSUMER_KEY, CONSUMER_SECRET)

            client.start_fetch_request_token(
                'http://127.0.0.1:%d/' % server.server_address[1])

            server.handle_request()

            server.server_close()

            self.ACCESS_TOKEN = client.fetch_access_token(self.REQUEST_TOKEN)
        else:
            print "Consumer key and secret not set in secrets.py - authenticated access to API unavailable."

    def class_by_kind(self, node, session=None, loaded=True):
        """
        Function to turn a dictionary into a Python object of the appropriate kind,
        based on the "kind" attribute found in the dictionary.
        """
        # TODO: Fail better or prevent failure when "kind" is missing.
        try:
            return kind_to_class_map[node["kind"]](node, session=self, loaded=loaded)
        except KeyError:
            raise APIError(
                "This kind of object should have a 'kind' attribute.", node)

    def convert_list_to_classes(self, nodelist, session=None, class_converter=None, loaded=True):
        """
        Convert each element of the list (in-place) into an instance of a subclass of APIModel.
        You can pass a particular class to `class_converter` if you want to, or it will auto-select by kind.
        """
        if not class_converter:
            class_converter = self.class_by_kind
        for i in range(len(nodelist)):
            nodelist[i] = class_converter(nodelist[i], session=self, loaded=loaded)

        return nodelist  # just for good measure; it's already been changed

    def class_by_name(self, node, name, session=None, loaded=True):
        """
        Function to turn a dictionary into a Python object of the kind given by name.
        """
        if isinstance(node, str) or isinstance(node, unicode):
            # Assume just an id has been supplied - otherwise there's not much we can do.
            node = {"id": node}
        if isinstance(node, dict):
            return kind_to_class_map[name](node, session=self, loaded=loaded)
        else:
            return node

    def convert_items(self, name, obj, loaded=True):
        """
        Convert attributes of an object to related object types.
        If in a list call to convert each element of the list.
        """
        class_converter = obj._related_field_types.get(name, None) or obj._lazy_related_field_types.get(name, None)
        # convert dicts to the related type
        if isinstance(obj[name], dict):
            obj[name] = class_converter(obj[name], session=self, loaded=loaded)
        # convert every item in related list to correct type
        elif isinstance(obj[name], list):
            self.convert_list_to_classes(obj[
                name], class_converter=class_converter, loaded=loaded)

    def params(self):
        if self.lang:
            return "?lang=" + self.lang
        else:
            return ""

    def get_exercises(self):
        """
        Return list of all exercises in the Khan API
        """
        return self.convert_list_to_classes(api_call("v1", Exercise.base_url + self.params(), self))

    def get_exercise(self, exercise_id):
        """
        Return particular exercise, by "exercise_id"
        """
        return Exercise(api_call("v1", Exercise.base_url + "/" + exercise_id + self.params(), self), session=self)

    def get_badges(self):
        """
        Return list of all badges in the Khan API
        """
        return self.convert_list_to_classes(api_call("v1", Badge.base_url + self.params(), self))

    def get_badge_category(self, category_id=None):
        """
        Return list of all badge categories in the Khan API, or a particular category.
        """
        if category_id is not None:
            return BadgeCategory(api_call("v1", BadgeCategory.base_url + "/categories/" + str(category_id) + self.params(), self)[0], session=self)
        else:
            return self.convert_list_to_classes(api_call("v1", BadgeCategory.base_url + "/categories" + self.params(), self))

    def get_user(self, user_id=""):
        """
        Download user data for a particular user.
        If no user specified, download logged in user's data.
        """
        if self.require_authentication():
            return User(api_call("v1", User.base_url + "?userId=" + user_id + self.params(), self), session=self)

    def get_topic_tree(self):
        """
        Retrieve complete node tree starting at the specified root_slug and descending.
        """
        return Topic(api_call("v1", "/topictree" + self.params(), self), session=self)

    def get_topic(self, topic_slug):
        """
        Retrieve complete topic at the specified topic_slug and descending.
        """
        return Topic(api_call("v1", Topic.base_url + "/" + topic_slug + self.params(), self), session=self)

    def get_topic_exercises(self, topic_slug):
        """
        This will return a list of exercises in the highest level of a topic.
        Not lazy loading from get_tree, as any load of the topic data includes these.
        """
        return self.convert_list_to_classes(api_call("v1", Topic.base_url + "/" + topic_slug + "/exercises" + self.params(), self))

    def get_topic_videos(self, topic_slug):
        """
        This will return a list of videos in the highest level of a topic.
        Not lazy loading from get_tree, as any load of the topic data includes these.
        """
        return self.convert_list_to_classes(api_call("v1", Topic.base_url + "/" + topic_slug + "/videos" + self.params(), self))

    def get_video(self, video_id):
        """
        Return particular video, by "readable_id" or "youtube_id" (deprecated)
        """
        return Video(api_call("v1", Video.base_url + "/" + video_id + self.params(), self), session=self)

    def get_videos(self):
        """
        Return list of all videos.
        As no API endpoint is provided for this by Khan Academy, this function fetches the topic tree,
        and recurses all the nodes in order to find all the videos in the topic tree.
        """
        topic_tree = self.get_topic_tree()

        video_nodes = {}

        def recurse_nodes(node):
            # Add the video to the video nodes
            kind = node["kind"]
            
            if node["id"] not in video_nodes and kind=="Video":
                video_nodes[node["id"]] = node

            # Do the recursion
            for child in node.get("children", []):
                recurse_nodes(child)
        recurse_nodes(topic_tree)

        return self.convert_list_to_classes(video_nodes.values())

    def get_playlists(self):
        """
        Return list of all playlists in the Khan API
        """
        return self.convert_list_to_classes(api_call("v1", Playlist.base_url + self.params(), self))

    def get_playlist_exercises(self, topic_slug):
        """
        This will return a list of exercises in a playlist.
        """
        return self.convert_list_to_classes(api_call("v1", Playlist.base_url + "/" + topic_slug + "/exercises" + self.params(), self))

    def get_playlist_videos(self, topic_slug):
        """
        This will return a list of videos in the highest level of a playlist.
        """
        return self.convert_list_to_classes(api_call("v1", Playlist.base_url + "/" + topic_slug + "/videos" + self.params(), self))

    def get_assessment_item(self, assessment_id):
        """
        Return particular assessment item, by "assessment_id"
        """
        return AssessmentItem(api_call("v1", AssessmentItem.base_url + "/" + assessment_id + self.params(), self), session=self)

    def get_tags(self):
        """
        Return list of all assessment item tags in the Khan API
        """
        return self.convert_list_to_classes(api_call("v1", Tag.base_url + self.params(), self), class_converter=Tag)

class Exercise(APIModel):

    base_url = "/exercises"

    _API_attributes = {
        "related_videos": "/videos",
        "followup_exercises": "/followup_exercises"
    }

    def __init__(self, *args, **kwargs):

        super(Exercise, self).__init__(*args, **kwargs)
        self._related_field_types = {
            "related_videos": partial(self._session.class_by_name, name="Video"),
            "followup_exercises": partial(self._session.class_by_name, name="Exercise"),
            "problem_types": partial(self._session.class_by_name, name="ProblemType"),
        }
        self._lazy_related_field_types = {
            "all_assessment_items": partial(self._session.class_by_name, name="AssessmentItem"),
        }


class ProblemType(APIModel):
    def __init__(self, *args, **kwargs):
        super(ProblemType, self).__init__(*args, **kwargs)
        self._lazy_related_field_types = {
            "assessment_items": partial(self._session.class_by_name, name="AssessmentItem"),
        }
        if self.has_key("items"):
            self.assessment_items = self["items"]
            del self["items"]

class AssessmentItem(APIModel):
    """
    A class to lazily load assessment item data for Perseus Exercise questions.
    """

    base_url = "/assessment_items"

    def __init__(self, *args, **kwargs):

        super(AssessmentItem, self).__init__(*args, **kwargs)

class Tag(APIModel):
    """
    A class for tags for Perseus Assessment Items.
    """

    base_url = "/assessment_items/tags"

class Badge(APIModel):

    base_url = "/badges"

    def __init__(self, *args, **kwargs):

        super(Badge, self).__init__(*args, **kwargs)

        self._related_field_types = {
            "user_badges": self._session.class_by_kind,
        }


class BadgeCategory(APIModel):
    pass


class APIAuthModel(APIModel):

    def __getattr__(self, name):
        # Added to avoid infinite recursion during authentication
        if name == "_session":
            return super(APIAuthModel, self).__getattr__(name)
        elif self._session.require_authentication():
            return super(APIAuthModel, self).__getattr__(name)

    # TODO: Add API_url function to add "?userID=" + user_id to each item
    # Check that classes other than User have user_id field.


class User(APIAuthModel):

    base_url = "/user"

    _API_attributes = {
        "videos": "/videos",
        "exercises": "/exercises",
        "students": "/students",
    }

    def __init__(self, *args, **kwargs):

        super(User, self).__init__(*args, **kwargs)

        self._related_field_types = {
            "videos": partial(self._session.class_by_name, name="UserVideo"),
            "exercises": partial(self._session.class_by_name, name="UserExercise"),
            "students": partial(self._session.class_by_name, name="User"),
        }


class UserExercise(APIAuthModel):

    base_url = "/user/exercises"

    _API_attributes = {
        "log": "/log",
        "followup_exercises": "/followup_exercises",
    }

    def __init__(self, *args, **kwargs):

        super(UserExercise, self).__init__(*args, **kwargs)

        self._related_field_types = {
            "exercise_model": self._session.class_by_kind,
            "followup_exercises": self._session.class_by_kind,
            "log": partial(self._session.class_by_name, name="ProblemLog"),
        }


class UserVideo(APIAuthModel):
    base_url = "/user/videos"

    _API_attributes = {
        "log": "/log",
    }

    def __init__(self, *args, **kwargs):

        super(UserVideo, self).__init__(*args, **kwargs)

        self._related_field_types = {
            "video": self._session.class_by_kind,
            "log": partial(self._session.class_by_name, name="VideoLog"),
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

    def __init__(self, *args, **kwargs):

        super(Topic, self).__init__(*args, **kwargs)

        self._related_field_types = {
            "children": self._session.class_by_kind,
        }

class Playlist(APIModel):

    base_url = "/playlists"

    def __init__(self, *args, **kwargs):

        super(Playlist, self).__init__(*args, **kwargs)

        self._related_field_types = {
            "children": self._session.class_by_kind,
        }


class Separator(APIModel):
    pass


class Scratchpad(APIModel):
    pass


class Article(APIModel):
    pass


class Video(APIModel):

    base_url = "/videos"

    _API_attributes = {"related_exercises": "/exercises"}

    def __init__(self, *args, **kwargs):

        super(Video, self).__init__(*args, **kwargs)

        self._related_field_types = {
            "related_exercises": self._session.class_by_kind,
        }


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
    "Playlist": Playlist,
    "ProblemType": ProblemType,
    "AssessmentItem": AssessmentItem,
    "AssessmentItemTag": Tag,
}


# Different API endpoints use different attributes as the id, depending on the kind of the item.
# This map defines the id to use for API calls, depending on the kind of
# the item.


kind_to_id_map = {
    "Video": partial(n_deep, names=["readable_id"]),
    "Exercise": partial(n_deep, names=["name"]),
    "Topic": partial(n_deep, names=["slug"]),
    "Playlist": partial(n_deep, names=["slug"]),
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
