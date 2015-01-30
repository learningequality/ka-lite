from urllib3.connectionpool import VerifiedHTTPSConnection
from .base import ReplayHTTPSConnection


class ReplayUrllib3HTTPSConnection(
        ReplayHTTPSConnection, VerifiedHTTPSConnection):
    _baseclass = VerifiedHTTPSConnection
