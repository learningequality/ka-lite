# see crypto_notes.txt in this directory for more info about key formats, etc

import base64, hashlib, sys, re
from kalite import settings
from config.models import Settings
import rsa as PYRSA
from utils.crypto import *

_own_key = None

def load_keys():
    private_key_string = Settings.get("private_key")
    public_key_string = Settings.get("public_key")
    if private_key_string and public_key_string:
        sys.modules[__name__]._own_key = Key(
            public_key_string=public_key_string,
            private_key_string=private_key_string)
    else:
        reset_keys()

def reset_keys():
    sys.modules[__name__]._own_key = Key()
    Settings.set("private_key", _own_key.get_private_key_string())
    Settings.set("public_key", _own_key.get_public_key_string())

def get_own_key():
    if not _own_key:
        load_keys()
    return _own_key
