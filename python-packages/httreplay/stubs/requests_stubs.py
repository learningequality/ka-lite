from requests.packages.urllib3.connectionpool import VerifiedHTTPSConnection
from .base import ReplayHTTPSConnection


class ReplayRequestsHTTPSConnection(
        ReplayHTTPSConnection, VerifiedHTTPSConnection):
    _baseclass = VerifiedHTTPSConnection
