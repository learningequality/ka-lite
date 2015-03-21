import os
import json
import logging


logger = logging.getLogger(__name__)


class ReplayRecording(object):
    """
    Holds on to a set of request keys and their response values.
    Can be used to reproduce HTTP/HTTPS responses without using
    the network.
    """
    def __init__(self, jsonable=None):
        self.request_responses = []
        if jsonable:
            self._from_jsonable(jsonable)

    def _from_jsonable(self, jsonable):
        self.request_responses = [
            (r['request'], r['response']) for r in jsonable ]

    def to_jsonable(self):
        return [dict(request=request, response=response)
                for request, response in self.request_responses]

    def __contains__(self, request):
        return any(rr[0] == request for rr in self.request_responses)

    def __getitem__(self, request):
        try:
            return next(rr[1] for rr in self.request_responses if rr[0] == request)
        except StopIteration:
            raise KeyError

    def __setitem__(self, request, response):
        self.request_responses.append((request, response))

    def get(self, request, default=None):
        try:
            return self[request]
        except KeyError:
            return default


class ReplayRecordingManager(object):
    """
    Loads and saves replay recordings as to json files.
    """
    @classmethod
    def load(cls, recording_file_name):
        try:
            with open(recording_file_name) as recording_file:
                recording = ReplayRecording(json.load(
                    recording_file,
                    cls=RequestResponseDecoder))
        except IOError:
            logger.debug("ReplayRecordingManager starting new %r",
                os.path.basename(recording_file_name))
            recording = ReplayRecording()
        else:
            logger.debug("ReplayRecordingManager loaded from %r",
                os.path.basename(recording_file_name))
        return recording

    @classmethod
    def save(cls, recording, recording_file_name):
        logger.debug("ReplayRecordingManager saving to %r",
            os.path.basename(recording_file_name))
        dirname, _ = os.path.split(recording_file_name)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(recording_file_name, 'w') as recording_file:
            json.dump(
                recording.to_jsonable(),
                recording_file,
                indent=4,
                sort_keys=True,
                cls=RequestResponseEncoder)


class RequestResponseDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        kwargs['object_hook'] = self.object_hook
        super(RequestResponseDecoder, self).__init__(*args, **kwargs)

    @staticmethod
    def object_hook(d):
        if len(d) == 2 and set(d) == set(['__type__', '__data__']):
            modname = d['__type__'].rsplit('.', 1)[0]
            cls = __import__(modname)
            for attr in d['__type__'].split('.')[1:]:
                cls = getattr(cls, attr)
            d = cls(d['__data__'])
        return d


class RequestResponseEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            from requests.structures import CaseInsensitiveDict
        except ImportError:
            pass
        else:
            if isinstance(obj, CaseInsensitiveDict):
                return {
                    '__type__': 'requests.structures.CaseInsensitiveDict',
                    '__data__': obj._store,
                    }

        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
